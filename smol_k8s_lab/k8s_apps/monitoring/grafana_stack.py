# external libraries
import logging as log

# internal libraries
from smol_k8s_lab.k8s_tools.argocd_util import ArgoCD
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_apps.identity_provider.zitadel_api import Zitadel
from smol_k8s_lab.k8s_apps.operators.minio import create_minio_alias
from smol_k8s_lab.k8s_tools.restores import restore_seaweedfs, restore_cnpg_cluster
from smol_k8s_lab.utils.value_from import process_backup_vals
from smol_k8s_lab.utils.passwords import create_password
from smol_k8s_lab.utils.rich_cli.console_logging import sub_header, header

def configure_grafana_stack(argocd: ArgoCD,
                            cfg: dict,
                            zitadel: Zitadel,
                            bitwarden: BwCLI = None) -> bool:
    """
    creates a grafana stack app and initializes it with secrets if you'd like :)

    required:
        argocd            - ArgoCD() object for Argo CD operations
        cfg               - dict, with at least argocd key and init key

    optional:
        zitadel     - Zitadel() object with session token to create zitadel oidc app and roles
        bitwarden   - BwCLI() object with session token to create bitwarden items
    """
    # verify immediately if grafana monitoring stack is installed
    app_installed = argocd.check_if_app_exists('grafana-stack')

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

    header(f"{prefix} [green]Grafana Monitoring Stack[/], so you can monitor your infrastructure",
           '📈')

    secrets = cfg['argo']['secret_keys']
    if secrets:
        grafana_hostname = secrets['grafana_hostname']

    # always declare grafana monitoring stack namespace immediately
    monitoring_namespace = cfg['argo']['namespace']

    if init_enabled:
        # configure backup s3 credentials
        backup_vals = process_backup_vals(cfg.get('backups', ''), 'zitadel', argocd)

    # initial secrets to deploy this app from scratch
    if init_enabled and not app_installed:
        argocd.k8s.create_namespace(monitoring_namespace)

        s3_endpoint = secrets.get('s3_endpoint', "")
        if s3_endpoint and not restore_enabled:
            s3_access_key = create_password()
            # create a local alias to check and make sure nextcloud is functional
            create_minio_alias(minio_alias="monitoring",
                               minio_hostname=s3_endpoint,
                               access_key="monitoring",
                               secret_key=s3_access_key)

        # create Grafana OIDC Application
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
                                  s3_endpoint,
                                  s3_access_key,
                                  backup_vals['s3_user'],
                                  backup_vals['s3_password'],
                                  backup_vals['restic_repo_pass'],
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
        argocd.install_app('grafana-stack', cfg['argo'])
    else:
        if bitwarden and init_enabled:
            log.info("Grafana Monitoring Stack already installed 🎉")
            refresh_bweso(argocd, grafana_hostname, bitwarden)


def refresh_bweso(argocd: ArgoCD, grafana_hostname: str, bitwarden: BwCLI):
    """
    refresh the bitwarden item IDs for use with argocd-appset-secret-plugin
    """
    # update the monitoring stack values for the Argo CD appset
    log.debug("making sure grafana bitwarden IDs are present in "
              "appset secret plugin")

    oidc_id = bitwarden.get_item(
            f"grafana-oidc-credentials-{grafana_hostname}", False
            )[0]['id']

    argocd.update_appset_secret(
            {'grafana_oidc_credentials_bitwarden_id': oidc_id})


def setup_bitwarden_items(argocd: ArgoCD,
                          grafana_hostname: str,
                          s3_endpoint: str,
                          s3_access_key: str,
                          backups_s3_user: str,
                          backups_s3_password: str,
                          restic_repo_pass: str,
                          zitadel_hostname: str,
                          oidc_creds: str,
                          bitwarden: BwCLI):
    """
    setup all the required secrets as items in bitwarden
    """
    sub_header("Creating grafana monitoring stack related secrets in Bitwarden")

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
            {'grafana_oidc_credentials_bitwarden_id': oidc_id}
            )

    restic_repo_obj = create_custom_field('resticRepoPassword', restic_repo_pass)
    s3_backup_id = bitwarden.create_login(
            name='monitoring-backups-s3-credentials',
            item_url=grafana_hostname,
            user=backups_s3_user,
            password=backups_s3_password,
            fields=[restic_repo_obj]
            )

    admin_s3_key = create_password()
    s3_admin_id = bitwarden.create_login(
            name='monitoring-admin-s3-credentials',
            item_url=grafana_hostname,
            user="monitoring-root",
            password=admin_s3_key
            )

    # S3 credentials for loki
    loki_access_key = create_password()
    s3_loki_id = bitwarden.create_login(
            name='loki-s3-credentials',
            item_url=grafana_hostname,
            user="monitoring-postgres",
            password=loki_access_key
            )

    # S3 credentials for mimir
    mimir_access_key = create_password()
    s3_mimir_id = bitwarden.create_login(
            name='mimir-s3-credentials',
            item_url=grafana_hostname,
            user="monitoring-postgres",
            password=mimir_access_key
            )

    # update the monitoring values for the argocd appset
    argocd.update_appset_secret(
            {'loki_s3_credentials_bitwarden_id': s3_loki_id,
             'mimir_s3_credentials_bitwarden_id': s3_mimir_id,
             'monitoring_s3_admin_credentials_bitwarden_id': s3_admin_id,
             'monitoring_s3_backups_credentials_bitwarden_id': s3_backup_id}
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
                      grafana_hostname: str,
                      bitwarden: BwCLI) -> None:
    """
    makes sure we update the appset secret with bitwarden IDs regardless
    """
    s3_backup_id = bitwarden.get_item(
            f"monitoring-backups-s3-credentials-{grafana_hostname}", False
            )[0]['id']

    s3_admin_id = bitwarden.get_item(
            f"monitoring-admin-s3-credentials-{grafana_hostname}", False
            )[0]['id']

    s3_loki_id = bitwarden.get_item(
            f"loki-s3-credentials-{grafana_hostname}", False
            )[0]['id']

    s3_mimir_id = bitwarden.get_item(
            f"mimir-s3-credentials-{grafana_hostname}", False
            )[0]['id']

    # update the monitoring values for the argocd appset
    argocd.update_appset_secret(
            {
            'loki_s3_credentials_bitwarden_id': s3_loki_id,
            'mimir_s3_credentials_bitwarden_id': s3_mimir_id,
            'monitoring_s3_backups_credentials_bitwarden_id': s3_backup_id,
            'monitoring_s3_admin_credentials_bitwarden_id': s3_admin_id
            }
            )


def restore_monitoring_stack(argocd: ArgoCD,
                             grafana_hostname: str,
                             monitoring_namespace: str,
                             argo_dict: dict,
                             secrets: dict,
                             restore_dict: dict,
                             backup_dict: dict,
                             pvc_storage_class: str,
                             pgsql_cluster_name: str,
                             bitwarden: BwCLI) -> None:
    """
    restore monitoring seaweedfs PVCs, monitoring files and/or config PVC(s),
    and CNPG postgresql cluster
    """
    # this is the info for the REMOTE backups
    s3_backup_endpoint = backup_dict['endpoint']
    s3_backup_bucket = backup_dict['bucket']
    access_key_id = backup_dict["s3_user"]
    secret_access_key = backup_dict["s3_password"]
    restic_repo_password = backup_dict['restic_repo_pass']
    cnpg_backup_schedule = backup_dict['postgres_schedule']

    # get where the current argo cd app is located in git
    revision = argo_dict["revision"]
    argo_path = argo_dict["path"]

    # first we grab existing bitwarden items if they exist
    if bitwarden:
        refresh_bitwarden(argocd, grafana_hostname, bitwarden)

        # apply the external secrets so we can immediately use them for restores
        external_secrets_yaml = (
                "https://raw.githubusercontent.com/small-hack/argocd-apps/"
                f"{revision}/{argo_path}/external_secrets_argocd_appset.yaml"
                )
        argocd.k8s.apply_manifests(external_secrets_yaml, argocd.namespace)

        # postgresql s3 ID
        s3_db_creds = bitwarden.get_item(
                f"monitoring-postgres-s3-credentials-{grafana_hostname}", False
                )[0]['login']

        pg_access_key_id = s3_db_creds["username"]
        pg_secret_access_key = s3_db_creds["password"]

    # these are the remote backups for seaweedfs
    s3_pvc_capacity = secrets['s3_pvc_capacity']

    # then we create all the seaweedfs pvcs we lost and restore them
    snapshot_ids = restore_dict['restic_snapshot_ids']
    restore_seaweedfs(
            argocd,
            'monitoring',
            monitoring_namespace,
            revision,
            argo_path,
            s3_backup_endpoint,
            s3_backup_bucket,
            access_key_id,
            secret_access_key,
            restic_repo_password,
            s3_pvc_capacity,
            pvc_storage_class,
            "ReadWriteOnce",
            snapshot_ids['seaweedfs_volume'],
            snapshot_ids['seaweedfs_filer']
            )

    # then we finally can restore the postgres database :D
    if restore_dict.get("cnpg_restore", False):
        psql_version = restore_dict.get("postgresql_version", 16)
        s3_endpoint = secrets.get('s3_endpoint', "")
        restore_cnpg_cluster(argocd.k8s,
                             'monitoring',
                             monitoring_namespace,
                             pgsql_cluster_name,
                             psql_version,
                             s3_endpoint,
                             pg_access_key_id,
                             pg_secret_access_key,
                             pgsql_cluster_name,
                             cnpg_backup_schedule)
