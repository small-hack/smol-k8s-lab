# internal libraries
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_apps.operators.minio import create_minio_alias
from smol_k8s_lab.k8s_apps.identity_provider.zitadel_api import Zitadel
from smol_k8s_lab.k8s_tools.argocd_util import (install_with_argocd,
                                                check_if_argocd_app_exists,
                                                update_argocd_appset_secret)
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.k8s_tools.restores import (restore_seaweedfs,
                                             k8up_restore_pvc,
                                             restore_postgresql)
from smol_k8s_lab.utils.rich_cli.console_logging import sub_header, header
from smol_k8s_lab.utils.passwords import create_password

# external libraries
import logging as log
from rich.prompt import Prompt


def configure_nextcloud(k8s_obj: K8s,
                        config_dict: dict,
                        argocd_namespace: str,
                        pvc_storage_class: str,
                        bitwarden: BwCLI = None,
                        zitadel: Zitadel = None) -> None:
    """
    creates a nextcloud app and initializes it with secrets if you'd like :)

    required:
        k8s_obj          - K8s() object with cluster credentials
        config_dict      - dictionary with at least argocd key and init key
        argocd_namespace - namespace of Argo CD

    optional:
        bitwarden   - BwCLI() object with session token to create bitwarden items
        zitadel     - Zitadel() object with session token to create zitadel oidc app and roles
    """
    # check immediately if this app is installed
    app_installed = check_if_argocd_app_exists('nextcloud')

    # get any secret keys passed in
    secrets = config_dict['argo']['secret_keys']
    if secrets:
        nextcloud_hostname = secrets['hostname']

    # verify if initialization is enabled
    init_enabled = config_dict['init'].get('enabled', True)

    # if the user has chosen to use smol-k8s-lab initialization
    if not app_installed and init_enabled:
        nextcloud_namespace = config_dict['argo']['namespace']
        k8s_obj.create_namespace(nextcloud_namespace)

        restore_dict = config_dict['init'].get('restore', {"enabled": False})
        restore_enabled = restore_dict['enabled']
        if restore_enabled:
            header_start = "Restoring"
        else:
            header_start = "Setting up"

        header(f"{header_start} [green]Nextcloud[/], to self host your files",
               '🩵')

        # grab all possile init values
        init_values = config_dict['init'].get('values', None)
        if init_values:
            admin_user = init_values.get('admin_user', 'admin')
            # stmp config values
            mail_host = init_values.get('smtp_host', None)
            mail_user = init_values.get('smtp_user', None)
            mail_pass = init_values.get('smtp_password', None)
            # credentials of remote backups of s3 PVCs
            restic_repo_pass = init_values.get('restic_repo_password', "")
            backups_s3_user = init_values.get('s3_backup_access_id', "")
            backups_s3_password = init_values.get('s3_backup_secret_key', "")

        if secrets:
            s3_endpoint = secrets.get('s3_endpoint', "")
            if s3_endpoint and not restore_enabled:
                s3_access_key = create_password()
                # create a local alias to check and make sure nextcloud is functional
                create_minio_alias(minio_alias="nextcloud",
                                   minio_hostname=s3_endpoint,
                                   access_key="nextcloud",
                                   secret_key=s3_access_key)

        # configure SMTP
        if not mail_host:
            mail_host = Prompt.ask(
                    "[green]Please enter the SMTP host for nextcoud"
                    )

        if not mail_user:
            m = f"[green]Please enter an SMTP user for Nextcloud on server, {mail_host}"
            mail_user = Prompt.ask(m)

        if not mail_pass:
            m = f"[green]Please enter the SMTP password of {mail_user} on {mail_host}"
            mail_pass = Prompt.ask(m, password=True)

        # configure OIDC
        if zitadel and not restore_enabled:
            log.debug("Creating a Nextcloud OIDC application in Zitadel...")
            redirect_uris = f"https://{nextcloud_hostname}/apps/oidc_login/oidc"
            logout_uris = [f"https://{nextcloud_hostname}"]
            oidc_creds = zitadel.create_application(
                    "nextcloud",
                    redirect_uris,
                    logout_uris
                    )
            zitadel.create_role("nextcloud_users", "Nextcloud Users", "nextcloud_users")
            zitadel.create_role("nextcloud_admins", "Nextcloud Admins", "nextcloud_admins")
            zitadel.update_user_grant(['nextcloud_admins'])
            zitadel_hostname = zitadel.hostname
        else:
            zitadel_hostname = ""

        # if bitwarden is enabled, we create login items for each set of credentials
        if bitwarden and not restore_enabled:
            setup_bitwarden_items(nextcloud_hostname, s3_endpoint, s3_access_key,
                                  backups_s3_user, backups_s3_password,
                                  restic_repo_pass, admin_user,
                                  mail_host, mail_user, mail_pass, oidc_creds,
                                  zitadel_hostname, k8s_obj, bitwarden)

        # these are standard k8s secrets
        elif not bitwarden and not restore_enabled:
            # nextcloud admin credentials and smtp credentials
            token = create_password()
            admin_password = create_password()
            k8s_obj.create_secret('nextcloud-admin-credentials', 'nextcloud',
                                  {"username": admin_user,
                                   "password": admin_password,
                                   "serverInfoToken": token,
                                   "smtpHost": mail_host,
                                   "smtpUsername": mail_user,
                                   "smtpPassword": mail_pass})

            # postgres db credentials creation
            k8s_obj.create_secret('nextcloud-pgsql-credentials', 'nextcloud',
                                  {"username": 'nextcloud',
                                   "password": 'we-use-tls-instead-of-password'})

            # redis credentials creation
            nextcloud_redis_password = create_password()
            k8s_obj.create_secret('nextcloud-redis-credentials', 'nextcloud',
                                  {"password": nextcloud_redis_password})

            # s3 credentials creation
            k8s_obj.create_secret('nextcloud-s3-credentials', 'nextcloud',
                                  {"S3_USER": "nextcloud",
                                   "S3_PASSWORD": s3_access_key,
                                   "S3_ENDPOINT": s3_endpoint})

    if not app_installed:
        # if the user is restoring, the process is a little different
        if init_enabled and restore_enabled:
            restore_nextcloud(argocd_namespace,
                              nextcloud_hostname,
                              nextcloud_namespace,
                              config_dict,
                              secrets,
                              restore_dict,
                              pvc_storage_class,
                              k8s_obj,
                              bitwarden)

        install_with_argocd(k8s_obj, 'nextcloud', config_dict['argo'])
    else:
        log.info("nextcloud already installed 🎉")
        if bitwarden and init_enabled:
            refresh_bweso(nextcloud_hostname, k8s_obj, bitwarden)


def restore_nextcloud(argocd_namespace,
                      nextcloud_hostname: str,
                      nextcloud_namespace: str,
                      config_dict: dict,
                      secrets: dict,
                      restore_dict: dict,
                      pvc_storage_class: str,
                      k8s_obj: K8s,
                      bitwarden: BwCLI) -> None:
    """
    restore nextcloud seaweedfs PVCs, nextcloud files and/or config PVC(s),
    and CNPG postgresql cluster
    """
    # first we grab existing bitwarden items if they exist
    if bitwarden:
        refresh_bweso(nextcloud_hostname, k8s_obj, bitwarden)

        # apply the external secrets so we can immediately use them for restores
        # ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️
        # WARNING: change this back to main when done testing
        # ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️
        ref = "add-pvc-helm-chart-for-nextcloud"
        external_secrets_yaml = (
                "https://raw.githubusercontent.com/small-hack/argocd-apps/"
                f"{ref}/nextcloud/app_of_apps/external_secrets_appset.yaml"
                )
        k8s_obj.apply_manifests(external_secrets_yaml, argocd_namespace)

    # these are the remote backups for seaweedfs
    s3_backup_endpoint = secrets['s3_backup_endpoint']
    s3_backup_bucket = secrets['s3_backup_bucket']
    access_key_id = config_dict['init']['values']['s3_backup_access_id']
    secret_access_key = config_dict['init']['values']['s3_backup_secret_key']
    restic_repo_password = config_dict['init']['values']['restic_repo_password']
    s3_pvc_capacity = secrets['s3_pvc_capacity']

    # then we create all the seaweedfs pvcs we lost and restore them
    snapshot_ids = config_dict['init']['restore']['restic_snapshot_ids']
    restore_seaweedfs(
            k8s_obj,
            'nextcloud',
            nextcloud_namespace,
            argocd_namespace,
            s3_backup_endpoint,
            s3_backup_bucket,
            access_key_id,
            secret_access_key,
            restic_repo_password,
            s3_pvc_capacity,
            pvc_storage_class,
            snapshot_ids['seaweedfs_volume'],
            snapshot_ids['seaweedfs_master'],
            snapshot_ids['seaweedfs_filer']
            )

    # then we begin the restic restore of all the nextcloud PVCs we lost
    for pvc in ['files', 'config']:
        pvc_enabled = secrets.get(f'{pvc}_pvc_enabled', 'false')
        if pvc_enabled and pvc_enabled.lower() != 'false':
            pvc_dict = {
                    "kind": "PersistentVolumeClaim",
                    "apiVersion": "v1",
                    "metadata": {
                        "name": f"nextcloud-{pvc}",
                        "namespace": nextcloud_namespace,
                        "annotations": {"k8up.io/backup": "true"},
                        "labels": {
                            "argocd.argoproj.io/instance": "nextcloud-pvc"
                            }
                        },
                    "spec": {
                        "storageClassName": "local-path",
                        "accessModes": [secrets[f'{pvc}_access_mode']],
                        "resources": {
                            "requests": {
                                "storage": secrets[f'{pvc}_storage']}
                            }
                        }
                    }

            # creates the nexcloud files pvc
            k8s_obj.apply_custom_resources([pvc_dict])
            s3_endpoint = secrets.get('s3_endpoint', "")
            k8up_restore_pvc(k8s_obj,
                             'nextcloud',
                             f'nextcloud-{pvc}',
                             'nextcloud',
                             s3_backup_endpoint,
                             s3_backup_bucket,
                             access_key_id,
                             secret_access_key,
                             restic_repo_password,
                             snapshot_ids[f'nextcloud_{pvc}']
                             )

    # then we finally can restore the postgres database :D
    if restore_dict.get("cnpg_restore", False):
        # WARNING: fix version here later before time progresses D:
        psql_version = restore_dict.get("postgresql_version", 16)
        restore_postgresql('nextcloud',
                           nextcloud_namespace,
                           'nextcloud-postgres',
                           psql_version,
                           s3_endpoint,
                           'nextcloud-postgres')


def setup_bitwarden_items(nextcloud_hostname: str,
                          s3_endpoint: str, s3_access_key: str,
                          backups_s3_user: str, backups_s3_password: str,
                          restic_repo_pass: str, admin_user: str,
                          mail_host: str, mail_user: str, mail_pass: str,
                          oidc_creds: dict, zitadel_hostname: str,
                          k8s_obj: K8s, bitwarden: BwCLI) -> None:
    """
    setup all the bitwarden items for nextcloud external secrets to be populated
    """
    sub_header("Creating Nextcloud items in Bitwarden")

    # s3 credentials creation
    bucket_obj = create_custom_field('bucket', "nextcloud-data")
    endpoint_obj = create_custom_field('endpoint', s3_endpoint)
    s3_id = bitwarden.create_login(
            name='nextcloud-user-s3-credentials',
            item_url=nextcloud_hostname,
            user="nextcloud",
            password=s3_access_key,
            fields=[bucket_obj, endpoint_obj]
            )

    pgsql_s3_key = create_password()
    s3_db_id = bitwarden.create_login(
            name='nextcloud-postgres-s3-credentials',
            item_url=nextcloud_hostname,
            user="nextcloud-postgres",
            password=pgsql_s3_key
            )

    admin_s3_key = create_password()
    s3_admin_id = bitwarden.create_login(
            name='nextcloud-admin-s3-credentials',
            item_url=nextcloud_hostname,
            user="nextcloud-root",
            password=admin_s3_key
            )

    # credentials for remote backups of the s3 PVC
    restic_repo_pass_obj = create_custom_field("resticRepoPassword", restic_repo_pass)
    s3_backups_id = bitwarden.create_login(
            name='nextcloud-backups-s3-credentials',
            item_url=nextcloud_hostname,
            user=backups_s3_user,
            password=backups_s3_password,
            fields=[restic_repo_pass_obj]
            )

    # oidc credentials if they were given, else they're probably already there
    if oidc_creds:
        log.debug("Creating OIDC credentials for Nextcloud in Bitwarden...")
        issuer_obj = create_custom_field("issuer", f"https://{zitadel_hostname}")
        oidc_id = bitwarden.create_login(
                name='nextcloud-oidc-credentials',
                item_url=nextcloud_hostname,
                user=oidc_creds['client_id'],
                password=oidc_creds['client_secret'],
                fields=[issuer_obj]
                )
    else:
        oidc_id = bitwarden.get_item(
                f"nextcloud-oidc-credentials-{nextcloud_hostname}"
                )[0]['id']

    # admin credentials + metrics server info token
    token = bitwarden.generate()
    admin_password = bitwarden.generate()
    serverinfo_token_obj = create_custom_field("serverInfoToken", token)
    admin_id = bitwarden.create_login(
            name='nextcloud-admin-credentials',
            item_url=nextcloud_hostname,
            user=admin_user,
            password=admin_password,
            fields=[serverinfo_token_obj]
            )

    # smtp credentials
    smtpHost = create_custom_field("hostname", mail_host)
    smtp_id = bitwarden.create_login(
            name='nextcloud-smtp-credentials',
            item_url=nextcloud_hostname,
            user=mail_user,
            password=mail_pass,
            fields=[smtpHost]
            )

    # postgres db credentials creation
    db_id = bitwarden.create_login(
            name='nextcloud-pgsql-credentials',
            item_url=nextcloud_hostname,
            user='nextcloud',
            password='we-dont-use-the-password-anymore-we-use-tls'
            )

    # redis credentials creation
    nextcloud_redis_password = bitwarden.generate()
    redis_id = bitwarden.create_login(
            name='nextcloud-redis-credentials',
            item_url=nextcloud_hostname,
            user='nextcloud',
            password=nextcloud_redis_password
            )

    # update the nextcloud values for the argocd appset
    update_argocd_appset_secret(
            k8s_obj,
            {'nextcloud_admin_credentials_bitwarden_id': admin_id,
             'nextcloud_oidc_credentials_bitwarden_id': oidc_id,
             'nextcloud_smtp_credentials_bitwarden_id': smtp_id,
             'nextcloud_postgres_credentials_bitwarden_id': db_id,
             'nextcloud_redis_bitwarden_id': redis_id,
             'nextcloud_s3_admin_credentials_bitwarden_id': s3_admin_id,
             'nextcloud_s3_postgres_credentials_bitwarden_id': s3_db_id,
             'nextcloud_s3_nextcloud_credentials_bitwarden_id': s3_id,
             'nextcloud_s3_backups_credentials_bitwarden_id': s3_backups_id}
            )


def refresh_bweso(nextcloud_hostname: str, k8s_obj: K8s, bitwarden: BwCLI) -> None:
    """
    if bitwarden and init are enabled, but app is already installed, make sure
    we populate appset secret plugin secret with nextcloud bitwarden item IDs
    """
    log.debug("Making sure nextcloud Bitwarden item IDs are in appset "
              "secret plugin secret")
    oidc_id = bitwarden.get_item(
            f"nextcloud-oidc-credentials-{nextcloud_hostname}"
            )[0]['id']

    admin_id = bitwarden.get_item(
            f"nextcloud-admin-credentials-{nextcloud_hostname}", False
            )[0]['id']

    smtp_id = bitwarden.get_item(
            f"nextcloud-smtp-credentials-{nextcloud_hostname}", False
            )[0]['id']

    db_id = bitwarden.get_item(
            f"nextcloud-pgsql-credentials-{nextcloud_hostname}", False
            )[0]['id']

    redis_id = bitwarden.get_item(
            f"nextcloud-redis-credentials-{nextcloud_hostname}", False
            )[0]['id']

    s3_admin_id = bitwarden.get_item(
            f"nextcloud-admin-s3-credentials-{nextcloud_hostname}", False
            )[0]['id']

    s3_db_id = bitwarden.get_item(
            f"nextcloud-postgres-s3-credentials-{nextcloud_hostname}", False
            )[0]['id']

    s3_id = bitwarden.get_item(
            f"nextcloud-user-s3-credentials-{nextcloud_hostname}", False
            )[0]['id']

    s3_backups_id = bitwarden.get_item(
            f"nextcloud-backups-s3-credentials-{nextcloud_hostname}", False
            )[0]['id']

    update_argocd_appset_secret(
            k8s_obj,
            {'nextcloud_admin_credentials_bitwarden_id': admin_id,
             'nextcloud_oidc_credentials_bitwarden_id': oidc_id,
             'nextcloud_smtp_credentials_bitwarden_id': smtp_id,
             'nextcloud_postgres_credentials_bitwarden_id': db_id,
             'nextcloud_redis_bitwarden_id': redis_id,
             'nextcloud_s3_admin_credentials_bitwarden_id': s3_admin_id,
             'nextcloud_s3_postgres_credentials_bitwarden_id': s3_db_id,
             'nextcloud_s3_nextcloud_credentials_bitwarden_id': s3_id,
             'nextcloud_s3_backups_credentials_bitwarden_id': s3_backups_id
            })
