# external libraries
import logging as log

# internal libraries
from smol_k8s_lab.k8s_tools.argocd_util import ArgoCD
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_apps.operators.minio import create_minio_alias
from smol_k8s_lab.utils.passwords import create_password
from smol_k8s_lab.utils.rich_cli.console_logging import sub_header, header

def configure_tempo(argocd: ArgoCD,
                    cfg: dict,
                    bitwarden: BwCLI = None) -> bool:
    """
    creates a tempo app and initializes it with secrets if you'd like :)

    required:
        argocd            - ArgoCD() object for Argo CD operations
        cfg               - dict, with at least argocd key and init key

    optional:
        bitwarden   - BwCLI() object with session token to create bitwarden items
    """
    # verify immediately if tempo is installed
    app_installed = argocd.check_if_app_exists('tempo')

    # verify if initialization is enabled
    init = cfg.get('init', {'enabled': True, 'restore': {'enabled': False}})
    init_enabled = init.get('enabled', True)

    restore_dict = cfg['init'].get('restore', {"enabled": False})
    restore_enabled = restore_dict['enabled']
    if restore_enabled:
        prefix = "Restoring"
    else:
        if app_installed:
            prefix = "Syncing"
        else:
            prefix = "Setting up"

    header(f"{prefix} [green]tempo[/], so you can monitor your traces",
           '📈')

    secrets = cfg['argo']['secret_keys']
    if secrets:
        tempo_hostname = secrets['hostname']

    # always declare tempo namespace immediately
    monitoring_namespace = cfg['argo']['namespace']

    # initial secrets to deploy this app from scratch
    if init_enabled and not app_installed:
        argocd.k8s.create_namespace(monitoring_namespace)

        s3_endpoint = secrets.get('s3_endpoint', "")
        if s3_endpoint and not restore_enabled:
            s3_access_key = create_password()
            # create a local alias to check and make sure tempo is functional
            create_minio_alias(minio_alias="tempo",
                               minio_hostname=s3_endpoint,
                               access_key="tempo",
                               secret_key=s3_access_key)

        # if the user has bitwarden enabled
        if bitwarden and not restore_enabled:
            setup_bitwarden_items(argocd,
                                  tempo_hostname,
                                  s3_endpoint,
                                  s3_access_key,
                                  bitwarden)

        # else create these as Kubernetes secrets
        elif not bitwarden and not restore_enabled:
            # tempo valkey creds k8s secret
            tempo_valkey_password = create_password()
            argocd.k8s.create_secret('tempo-valkey-credentials', 'forgejo',
                                     {"password": tempo_valkey_password})

    if not app_installed:
        argocd.install_app('tempo', cfg['argo'])
    else:
        if bitwarden and init_enabled:
            log.info("tempo already installed 🎉")
            refresh_bitwarden(argocd, tempo_hostname, bitwarden)


def setup_bitwarden_items(argocd: ArgoCD,
                          tempo_hostname: str,
                          s3_endpoint: str,
                          bitwarden: BwCLI):
    """
    setup all the required secrets as items in bitwarden
    """
    sub_header("Creating tempo related secrets in Bitwarden")

    # valkey credentials
    tempo_valkey_password = bitwarden.generate()
    valkey_id = bitwarden.create_login(
            name='tempo-valkey-credentials',
            item_url=tempo_hostname,
            user='valkey',
            password=tempo_valkey_password
            )

    endpoint_obj = create_custom_field('endpoint', s3_endpoint)

    # S3 credentials for tempo
    tempo_bucket_obj = create_custom_field('bucket', "tempo")
    tempo_access_key = create_password()
    s3_tempo_id = bitwarden.create_login(
            name='tempo-s3-credentials',
            item_url=tempo_hostname,
            user="tempo",
            password=tempo_access_key,
            fields=[tempo_bucket_obj, endpoint_obj]
            )


    # update the monitoring values for the argocd appset
    argocd.update_appset_secret(
            {
            'tempo_valkey_bitwarden_id': valkey_id,
            'tempo_s3_credentials_bitwarden_id': s3_tempo_id
            }
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


def refresh_bitwarden(argocd: ArgoCD,
                      tempo_hostname: str,
                      bitwarden: BwCLI) -> None:
    """
    makes sure we update the appset secret with bitwarden IDs regardless
    """
    valkey_id = bitwarden.get_item(
            f"tempo-valkey-credentials-{tempo_hostname}", False
            )[0]['id']

    # oidc_id = bitwarden.get_item(
    #         f"tempo-oidc-credentials-{tempo_hostname}", False
    #         )[0]['id']

    s3_tempo_id = bitwarden.get_item(
            f"tempo-s3-credentials-{tempo_hostname}", False
            )[0]['id']

    # update the monitoring values for the argocd appset
    # 'tempo_oidc_credentials_bitwarden_id': oidc_id,
    argocd.update_appset_secret(
            {
            'tempo_valkey_bitwarden_id': valkey_id,
            'tempo_s3_credentials_bitwarden_id': s3_tempo_id
            }
            )
