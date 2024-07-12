# external libraries
import logging as log

# internal libraries
from smol_k8s_lab.k8s_tools.argocd_util import ArgoCD
from smol_k8s_lab.bitwarden.bw_cli import BwCLI
from smol_k8s_lab.k8s_apps.identity_provider.zitadel_api import Zitadel
from smol_k8s_lab.utils.rich_cli.console_logging import sub_header, header

def configure_prometheus_stack(argocd: ArgoCD,
                               cfg: dict,
                               zitadel: Zitadel,
                               bitwarden: BwCLI = None) -> bool:
    """
    creates a prometheus stack app and initializes it with secrets if you'd like :)

    required:
        argocd            - ArgoCD() object for Argo CD operations
        cfg               - dict, with at least argocd key and init key

    optional:
        zitadel     - Zitadel() object with session token to create zitadel oidc app and roles
        bitwarden   - BwCLI() object with session token to create bitwarden items
    """
    # verify immediately if prometheus is installed
    app_installed = argocd.check_if_app_exists('prometheus')

    # verify if initialization is enabled
    init = cfg.get('init', {'enabled': True, 'restore': {'enabled': False}})
    init_enabled = init.get('enabled', True)

    if app_installed:
        header_start = "Syncing"
    else:
        header_start = "Setting up"

    header(f"{header_start} [green]prometheus[/], so you can monitor your infrastructure",
           '🔥')

    secrets = cfg['argo']['secret_keys']
    if secrets:
        grafana_hostname = secrets['grafana_hostname']

    # always declare prometheus namespace immediately
    prometheus_namespace = cfg['argo']['namespace']

    # initial secrets to deploy this app from scratch
    if init_enabled and not app_installed:
        argocd.k8s.create_namespace(prometheus_namespace)

        # create prometheus OIDC Application
        if zitadel:
            log.debug("Creating an OIDC application in Zitadel...")
            zitadel_hostname = zitadel.hostname
            logout_uris = [f"https://{grafana_hostname}"]
            redirect_uris = f"https://{grafana_hostname}/login/generic_oauth"
            oidc_creds = zitadel.create_application("grafana",
                                                    redirect_uris,
                                                    logout_uris)
            zitadel.create_role("grafana_users", "grafana Users", "grafana_users")
            zitadel.update_user_grant(['grafana_users'])
        else:
            zitadel_hostname = ""

        # if the user has bitwarden enabled
        if bitwarden:
            setup_bitwarden_items(argocd,
                                  grafana_hostname,
                                  prometheus_namespace,
                                  zitadel_hostname,
                                  oidc_creds,
                                  bitwarden)

        # else create these as Kubernetes secrets
        else:
            if zitadel:
                # oidc secret
                argocd.k8s.create_secret(
                        'grafana-oidc-credentials',
                        'grafana',
                        {'user': oidc_creds['client_id'],
                         'password': oidc_creds['client_secret']}
                        )

    if not app_installed:
        argocd.install_app('prometheus', cfg['argo'])
    else:
        if bitwarden and init_enabled:
            log.info("prometheus already installed 🎉")
            refresh_bweso(argocd, grafana_hostname, bitwarden)


def refresh_bweso(argocd: ArgoCD, grafana_hostname: str, bitwarden: BwCLI):
    """
    refresh the bitwarden item IDs for use with argocd-appset-secret-plugin
    """
    # update the prometheus values for the argocd appset
    log.debug("making sure prometheus and grafana bitwarden IDs are present in "
              "appset secret plugin")

    oidc_id = bitwarden.get_item(
            f"grafana-oidc-credentials-{grafana_hostname}", False
            )[0]['id']

    argocd.update_appset_secret(
            {'prometheus_grafana_oidc_credentials_bitwarden_id': oidc_id})


def setup_bitwarden_items(argocd: ArgoCD,
                          grafana_hostname: str,
                          prometheus_namespace: str,
                          zitadel_hostname: str,
                          oidc_creds: str,
                          bitwarden: BwCLI):
    """
    setup all the required secrets as items in bitwarden
    """
    sub_header("Creating prometheus related secrets in Bitwarden")

    # OIDC credentials
    log.info("Creating OIDC credentials for grafana in Bitwarden")
    if zitadel_hostname:
        if oidc_creds:
            # for the credentials to zitadel
            oidc_id = bitwarden.create_login(
                    name='grafana-oidc-credentials',
                    item_url=grafana_hostname,
                    user=oidc_creds['client_id'],
                    password=oidc_creds['client_secret']
                    )
        else:
            # we assume the credentials already exist if they fail to create
            oidc_id = bitwarden.get_item(
                    f"grafana-oidc-credentials-{grafana_hostname}"
                    )[0]['id']

    # update the grafana values for the argocd appset
    argocd.update_appset_secret(
            {'prometheus_grafana_oidc_credentials_bitwarden_id': oidc_id}
            )

    # reload the bitwarden ESO provider
    try:
        argocd.k8s.reload_deployment('bitwarden-eso-provider',
                                     'external-secrets')
    except Exception as e:
        log.error(
                "Couldn't scale down the [magenta]bitwarden-eso-provider[/]"
                "deployment in [green]external-secrets[/] namespace. Recieved: "
                f"{e}"
                )
