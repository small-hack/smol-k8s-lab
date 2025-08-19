import logging as log
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_apps.identity_provider.zitadel_api import Zitadel
from smol_k8s_lab.k8s_tools.argocd_util import ArgoCD
from smol_k8s_lab.utils.rich_cli.console_logging import header
from smol_k8s_lab.utils.passwords import create_password
from smol_k8s_lab.k8s_tools.restores import (restore_seaweedfs,
                                             k8up_restore_pvc,
                                             restore_cnpg_cluster)


def configure_netmaker(argocd: ArgoCD,
                       netmaker_config_dict: dict,
                       oidc_provider_name: str = "",
                       oidc_provider_hostname: str = "",
                       bitwarden: BwCLI = None,
                       zitadel: Zitadel = None) -> None:
    """
    Installs netmaker as an Argo CD application on Kubernetes

    Required Args:
      argocd:                 ArgoCD(), for the argocd operations
      netmaker_config_dict:   Argo CD parameters

    Optional Args:
      oidc_provider_name:     OIDC provider name. options: keycloak, zitadel
      oidc_provider_hostname: OIDC provider hostname e.g. zitadel.example.com
      bitwarden:              BwCLI, to store k8s secrets in bitwarden
      zitadel:                Zitadel api object
    """
    header("Setting up [green]Netmaker[/] to create VPNs", "🗝️")

    # make sure netmaker isn't already installed
    app_installed = argocd.check_if_app_exists("netmaker")
    # this handles the netmaker-oauth-config secret data
    secrets = netmaker_config_dict['argo']['secret_keys']
    if secrets:
        netmaker_hostname = secrets['hostname']
        netmaker_dashboard_hostname = secrets['admin_hostname']
        netmaker_api_hostname = secrets['api_hostname']

    if netmaker_config_dict['init']['enabled'] and not app_installed:
        netmaker_realm = netmaker_config_dict['init']['values'].get('realm', "")
        auth_dict = create_netmaker_app(provider=oidc_provider_name,
                                        provider_hostname=oidc_provider_hostname,
                                        dashboard_hostname=netmaker_dashboard_hostname,
                                        api_hostname=netmaker_api_hostname,
                                        zitadel=zitadel,
                                        realm=netmaker_realm)

        # generate postgres and mqtt credentials
        postgresPassword = create_password()
        sqlPass = create_password()
        mqPass = create_password()

        # netmaker superadmin user and password, as well as master key
        netmaker_user = netmaker_config_dict['init']['values']['admin_user']
        netmaker_pass = create_password()
        netmaker_master_key = create_password()

        # if using bitwarden, put the secret in bitarden and ESO will grab it
        if bitwarden:
            fields = [create_custom_field("issuer", f"https://{oidc_provider_hostname}")]

            log.debug(f"netmaker oauth fields are {fields}")

            postgres_fields = [
                create_custom_field("host", 'postgresql.svc.cluster.local'),
                create_custom_field("port", '5432'),
                create_custom_field("database", 'netmaker'),
                create_custom_field("postgres_password", postgresPassword),
                ]

            log.info(f"netmaker postgres fields are {postgres_fields}")

            # create netmaker super admin credentials bitwarden item
            admin_id = bitwarden.create_login(
                name=f'{netmaker_hostname}-netmaker-admin-credentials',
                user=netmaker_user,
                password=netmaker_pass,
                item_url=netmaker_hostname,
                fields=[create_custom_field("masterkey", netmaker_master_key)]
                )

            # create oauth OIDC bitwarden item
            oauth_id = bitwarden.create_login(
                name=f'{netmaker_hostname}-netmaker-oauth-config',
                user=auth_dict['client_id'],
                item_url=netmaker_hostname,
                password=auth_dict['client_secret'],
                fields=fields
                )

            # create the mqtt bitwarden item
            mq_id = bitwarden.create_login(
                    name=f"{netmaker_hostname}-netmaker-mq-credentials",
                    user='netmaker',
                    password=mqPass
                    )

            # create the postgres bitwarden item
            postgres_id = bitwarden.create_login(
                    name=f"{netmaker_hostname}-netmaker-pgsql-credentials",
                    user='netmaker',
                    password=sqlPass,
                    fields=postgres_fields
                    )

            # update the netmaker values for the argocd appset
            argocd.update_appset_secret(
                    {'netmaker_oauth_config_bitwarden_id': oauth_id,
                     'netmaker_admin_credentials_bitwarden_id': admin_id,
                     'netmaker_mq_config_bitwarden_id': mq_id,
                     'netmaker_pgsql_config_bitwarden_id': postgres_id})

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

        # create netmaker k8s secrets if we're not using bitwarden
        else:
            # create oauth OIDC k8s secret
            argocd.k8s.create_secret('netmaker-admin-credentials',
                                     'netmaker',
                                     {'ADMIN_USER': netmaker_user,
                                      'ADMIN_PASSWORD': netmaker_pass,
                                      'MASTER_KEY': netmaker_master_key}
                                      )

            # create oauth OIDC k8s secret
            argocd.k8s.create_secret('netmaker-oauth-config',
                                     'netmaker',
                                     {'CLIENT_ID': auth_dict['client_id'],
                                      'CLIENT_SECRET': auth_dict['client_secret'],
                                      'OIDC_SSUER': f"https://{oidc_provider_hostname}"}
                                      )

            # create mqtt k8s secret
            argocd.k8s.create_secret('netmaker-mq-credentials',
                                     'netmaker',
                                     {'MQ_PASSWORD': mqPass,
                                      'MQ_USERNAME': 'netmaker'}
                                      )

            # create postgres k8s secret
            argocd.k8s.create_secret('netmaker-pgsql-credentials',
                                     'netmaker',
                                     {'postgres_password': postgresPassword,
                                      'SQL_HOST': 'netmaker-postgresql.netmaker.svc.cluster.local',
                                      'SQL_PORT': '5432',
                                      'SQL_DB': 'netmaker',
                                      'SQL_USER': 'netmaker',
                                      'SQL_PASS': sqlPass}
                                      )

    if not app_installed:
        argocd.install_app('netmaker', netmaker_config_dict['argo'])
    else:
        log.info("netmaker already installed 🎉")

        # we need to still update the bitwarden IDs if bitwarden and init is enabled
        if netmaker_config_dict['init']['enabled'] and bitwarden:
            log.debug("Updating netmaker-admin-credentials bitwarden ID in the appset secret")
            admin_id = bitwarden.get_item(
                    f"{netmaker_hostname}-netmaker-admin-credentials"
                    )[0]['id']

            log.debug("Updating netmaker-oath-config bitwarden ID in the appset secret")
            oauth_id = bitwarden.get_item(
                    f"{netmaker_hostname}-netmaker-oauth-config", False
                    )[0]['id']

            log.debug("Updating netmaker-pqsql-credentials bitwarden ID in the appset secret")
            postgres_id = bitwarden.get_item(
                    f"{netmaker_hostname}-netmaker-pgsql-credentials", False
                    )[0]['id']

            mq_id = bitwarden.get_item(
                    f"{netmaker_hostname}-netmaker-mq-credentials", False
                    )[0]['id']

            # update the netmaker values for the argocd appset
            argocd.update_appset_secret(
                    {'netmaker_oauth_config_bitwarden_id': oauth_id,
                     'netmaker_admin_credentials_bitwarden_id': admin_id,
                     'netmaker_mq_config_bitwarden_id': mq_id,
                     'netmaker_pgsql_config_bitwarden_id': postgres_id})

def create_netmaker_app(provider: str,
                     provider_hostname: str,
                     dashboard_hostname: str = "",
                     api_hostname: str = "",
                     zitadel: Zitadel = None,
                     realm: str = "default") -> list:
    """
    Creates an OIDC application, for netmaker, in either Keycloak or Zitadel

    Arguments:
      provider           - either 'keycloak' or 'zitadel'
      provider_hostname  - hostname of keycloak or zitadel
      dashboard_hostname - hostname of netmaker admina dashboard
      api_hostname       - hostname of netmaker api endpoint
      zitadel            - Zitadel api object
      realm              - realm to use for keycloak if using keycloak

    returns [url, client_id, client_secret]
    """
    # create Netmaker OIDC Application
    if provider == 'zitadel':
        log.info("Creating an OIDC application for Netmaker via Zitadel...")
        netmaker_dict = zitadel.create_application(
                "netmaker",
                f"https://{api_hostname}/api/oauth/callback",
                [f"https://{dashboard_hostname}"]
                )
        zitadel.create_role("netmaker_users", "Netmaker Users", "netmaker_users")
        zitadel.update_user_grant(['netmaker_users'])

        client_id = netmaker_dict['client_id']
        client_secret = netmaker_dict['client_secret']
        auth_url = f'https://{provider_hostname}/oauth/v2/authorize'
        token_url = f'https://{provider_hostname}/oauth/v2/token'
        user_info_url = f'https://{provider_hostname}/oidc/v1/userinfo'
        end_session_url = f'https://{provider_hostname}/oidc/v1/end_session'
    else:
        log.error("zitadel not passed into create_netmaker_app,"
                  f" got {provider} instead.")

    auth_dict = {"auth_url": auth_url,
                 "token_url": token_url,
                 "user_info_url": user_info_url,
                 "end_session_url": end_session_url,
                 "client_id": client_id,
                 "client_secret": client_secret}
    return auth_dict


def restore_netmaker(argocd: ArgoCD,
                     netmaker_hostname: str,
                     netmaker_namespace: str,
                     argo_dict: dict,
                     secrets: dict,
                     restore_dict: dict,
                     backup_dict: dict,
                     global_pvc_storage_class: str,
                     pgsql_cluster_name: str,
                     bitwarden: BwCLI) -> None:
    """
    restore netmaker seaweedfs PVCs, and CNPG postgresql cluster
    """
    # this is the info for the REMOTE backups
    s3_backup_endpoint = backup_dict['endpoint']
    s3_backup_bucket = backup_dict['bucket']
    access_key_id = backup_dict["s3_user"]
    secret_access_key = backup_dict["s3_password"]
    restic_repo_password = backup_dict['restic_repo_pass']
    cnpg_backup_schedule = backup_dict['postgres_schedule']

    # get argo git repo info
    revision = argo_dict['revision']
    argo_path = argo_dict['path']

    # first we grab existing bitwarden items if they exist
    if bitwarden:
        # refresh_bweso(argocd, netmaker_hostname, bitwarden)

        # apply the external secrets so we can immediately use them for restores
        external_secrets_yaml = (
                f"https://raw.githubusercontent.com/small-hack/argocd-apps/{revision}/"
                f"{argo_path}external_secrets_argocd_appset.yaml"
                )
        argocd.k8s.apply_manifests(external_secrets_yaml, argocd.namespace)

        # postgresql s3 ID
        s3_db_creds = bitwarden.get_item(
                f"netmaker-postgres-s3-credentials-{netmaker_hostname}", False
                )[0]['login']

        pg_access_key_id = s3_db_creds["username"]
        pg_secret_access_key = s3_db_creds["password"]

    # these are the remote backups for seaweedfs
    s3_pvc_capacity = secrets['s3_pvc_capacity']

    # then we create all the seaweedfs pvcs we lost and restore them
    snapshot_ids = restore_dict['restic_snapshot_ids']
    s3_pvc_storage_class = secrets.get("s3_pvc_storage_class", global_pvc_storage_class)

    restore_seaweedfs(
            argocd,
            'netmaker',
            netmaker_namespace,
            revision,
            argo_path,
            s3_backup_endpoint,
            s3_backup_bucket,
            access_key_id,
            secret_access_key,
            restic_repo_password,
            s3_pvc_capacity,
            s3_pvc_storage_class,
            "ReadWriteOnce",
            snapshot_ids['seaweedfs_volume'],
            snapshot_ids['seaweedfs_filer'])

    # then we finally can restore the postgres database :D
    if restore_dict.get("cnpg_restore", False):
        psql_version = restore_dict.get("postgresql_version", 16)
        s3_endpoint = secrets.get('s3_endpoint', "")
        restore_cnpg_cluster(argocd.k8s,
                             'netmaker',
                             netmaker_namespace,
                             pgsql_cluster_name,
                             psql_version,
                             s3_endpoint,
                             pg_access_key_id,
                             pg_secret_access_key,
                             pgsql_cluster_name,
                             cnpg_backup_schedule)

    podconfig_yaml = (
            f"https://raw.githubusercontent.com/small-hack/argocd-apps/{revision}/"
            f"{argo_path}pvc_argocd_appset.yaml"
            )
    argocd.k8s.apply_manifests(podconfig_yaml, argocd.namespace)

    # then we begin the restic restore of all the netmaker PVCs we lost
    for pvc in ['files', 'config']:
        pvc_enabled = secrets.get(f'{pvc}_pvc_enabled', 'false')
        if pvc_enabled and pvc_enabled.lower() != 'false':
            # restores the netmaker pvc
            k8up_restore_pvc(argocd.k8s,
                             'netmaker',
                             f'netmaker-{pvc}',
                             'netmaker',
                             s3_backup_endpoint,
                             s3_backup_bucket,
                             access_key_id,
                             secret_access_key,
                             restic_repo_password,
                             snapshot_ids[f'netmaker_{pvc}'],
                             "file-backups-podconfig"
                             )
