# internal libraries
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_tools.argocd_util import ArgoCD
# from smol_k8s_lab.utils.passwords import create_password
from smol_k8s_lab.utils.rich_cli.console_logging import header
from smol_k8s_lab.utils.value_from import extract_secret

# external libraries
import logging as log


def configure_renovate(argocd: ArgoCD,
                       cfg: dict,
                       bitwarden: BwCLI = None) -> bool:
    """
    creates a renovate app and initializes it with secrets if you'd like :)

    required:
        argocd                 - ArgoCD() object for Argo CD operations
        cfg                    - dict, with at least argocd key and init key

    optional:
        bitwarden   - BwCLI() object with session token to create bitwarden items

    coming soon:
        pvc_storage_class      - str, storage class of PVC
    """
    # check immediately if the app is installed
    app_installed = argocd.check_if_app_exists('renovate')

    # verify if initialization is enabled
    init = cfg.get('init', {'enabled': True, 'restore': {'enabled': False}})
    init_enabled = init.get('enabled', True)

    # check if we're restoring and get values for that
    restore_dict = init.get('restore', {"enabled": False})
    restore_enabled = restore_dict['enabled']

    # figure out what header to print
    if restore_enabled:
        header_start = "Restoring"
    else:
        if app_installed:
            header_start = "Syncing"
        else:
            header_start = "Setting up"

    header(f"{header_start} [green]renovate[/], so you can keep your dependencies up to date",
           '🤖')

    # get any secrets for this app
    # secrets = cfg['argo']['secret_keys']

    # we need namespace immediately
    renovate_namespace = cfg['argo']['namespace']

    if init_enabled:
        renovate_pat = extract_secret(init['values'].get('renovate_pat'))
        try:
            github_pat = extract_secret(init['values'].get('renovate_github_pat'))
        except Exception as e:
            log.error(str(e))
            github_pat = "happy_halloween"
        if not github_pat:
            github_pat = "happy_halloween"

    if init_enabled and not app_installed:
        argocd.k8s.create_namespace(renovate_namespace)

        if bitwarden and not restore_enabled:
            setup_bitwarden_items(argocd, bitwarden, renovate_pat, github_pat)

        # these are standard k8s secrets yaml
        elif not bitwarden and not restore_enabled:
            # renovate creds k8s secret
            argocd.k8s.create_secret('renovate-pat', 'renovate',
                                     {"pat": renovate_pat,
                                      "github_token": github_pat})

    if not app_installed:
        if not init_enabled:
            argocd.install_app('renovate', cfg['argo'])
    else:
        log.info("renovate already installed 🎉")

        if bitwarden and init_enabled:
            refresh_bweso(argocd, bitwarden)


def setup_bitwarden_items(argocd: ArgoCD,
                          bitwarden: BwCLI,
                          renovate_pat: str,
                          github_pat: str = "") -> None:

    # renovate credentials
    renovate_id = bitwarden.create_login(
            name='renovate-pat-smol-k8s-lab',
            item_url="renovate.io",
            user='renovate',
            password=renovate_pat,
            fields=[create_custom_field("github-token", github_pat)]
            )

    # update the renovate values for the argocd appset
    argocd.update_appset_secret({'renovate_pat_bitwarden_id': renovate_id})

    # reload the bitwarden ESO provider
    try:
        argocd.k8s.reload_deployment('bitwarden-eso-provider', 'external-secrets')
    except Exception as e:
        log.error(
                "Couldn't scale down the [magenta]bitwarden-eso-provider"
                "[/] deployment in [green]external-secrets[/] namespace."
                f"Recieved: {e}"
                )


def refresh_bweso(argocd: ArgoCD, bitwarden: BwCLI) -> None:
    """
    if renovate already installed, but bitwarden and init are enabled, still
    populate the bitwarden IDs in the appset secret plugin secret
    """
    log.debug("Making sure renovate Bitwarden item IDs are in appset "
              "secret plugin secret")


    secrets_id = bitwarden.get_item("renovate-pat-smol-k8s-lab", False)[0]['id']

    # {'renovate_admin_credentials_bitwarden_id': admin_id,
    argocd.update_appset_secret({'renovate_secret_bitwarden_id': secrets_id})
