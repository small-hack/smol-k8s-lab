# internal libraries
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_apps.operators.minio import create_minio_alias
from smol_k8s_lab.k8s_apps.identity_provider.zitadel_api import Zitadel
from smol_k8s_lab.k8s_apps.social.nextcloud_occ_commands import Nextcloud
from smol_k8s_lab.k8s_tools.argocd_util import ArgoCD
from smol_k8s_lab.k8s_tools.restores import (restore_seaweedfs,
                                             recreate_pvc,
                                             k8up_restore_pvc,
                                             restore_cnpg_cluster)
from smol_k8s_lab.utils.passwords import create_password
from smol_k8s_lab.utils.rich_cli.console_logging import sub_header, header
from smol_k8s_lab.utils.run.subproc import subproc
from smol_k8s_lab.utils.value_from import extract_secret, process_backup_vals

# external libraries
import logging as log
from rich.prompt import Prompt


def configure_nextcloud(argocd: ArgoCD,
                        cfg: dict,
                        pvc_storage_class: str,
                        zitadel: Zitadel = None,
                        bitwarden: BwCLI = None) -> None:
    """
    creates a nextcloud app and initializes it with secrets if you'd like :)

    required:
        argocd            - ArgoCD() object for Argo CD operations
        cfg               - dict, with at least argocd key and init key
        pvc_storage_class - str, storage class of PVC

    optional:
        bitwarden   - BwCLI() object with session token to create bitwarden items
        zitadel     - Zitadel() object with session token to create zitadel oidc app and roles
    """
    # check immediately if this app is installed
    app_installed = argocd.check_if_app_exists('nextcloud')

    # get any secret keys passed in
    secrets = cfg['argo']['secret_keys']
    if secrets:
        nextcloud_hostname = secrets['hostname']

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

    header(f"{header_start} [green]Nextcloud[/], to self host your files",
           '🩵')

    # if the user has chosen to use smol-k8s-lab initialization
    if not app_installed and init_enabled:
        nextcloud_namespace = cfg['argo']['namespace']
        argocd.k8s.create_namespace(nextcloud_namespace)


        # grab all possile init values
        init_values = init.get('values', None)
        if init_values:
            admin_user = init_values.get('admin_user', 'admin')

            # stmp config values
            mail_host = init_values.get('smtp_host', None)
            mail_user = init_values.get('smtp_user', None)
            mail_pass = extract_secret(init_values.get('smtp_password', ""))
        else:
            log.warn("Strange, there's no nextcloud init values...")

        # backups are their own config.yaml section
        backup_vals = process_backup_vals(cfg.get('backups', {}), 'nextcloud', argocd)

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
            zitadel.create_role("nextcloud_users",
                                "Nextcloud Users",
                                "nextcloud_users")
            zitadel.create_role("nextcloud_admins",
                                "Nextcloud Admins",
                                "nextcloud_admins")
            zitadel.update_user_grant(['nextcloud_admins'])
            zitadel_hostname = zitadel.hostname
        else:
            zitadel_hostname = ""

        # if bitwarden is enabled, we create login items for each set of credentials
        if bitwarden and not restore_enabled:
            setup_bitwarden_items(argocd,
                                  nextcloud_hostname,
                                  s3_endpoint,
                                  s3_access_key,
                                  backup_vals['s3_user'],
                                  backup_vals['s3_password'],
                                  backup_vals['restic_repo_pass'],
                                  admin_user,
                                  mail_host,
                                  mail_user,
                                  mail_pass,
                                  oidc_creds,
                                  zitadel_hostname,
                                  bitwarden)

        # these are standard k8s secrets
        elif not bitwarden and not restore_enabled:
            # nextcloud admin credentials and smtp credentials
            token = create_password()
            admin_password = create_password()
            argocd.k8s.create_secret('nextcloud-admin-credentials', 'nextcloud',
                                     {"username": admin_user,
                                      "password": admin_password,
                                      "serverInfoToken": token,
                                      "smtpHost": mail_host,
                                      "smtpUsername": mail_user,
                                      "smtpPassword": mail_pass})

            # postgres db credentials creation
            argocd.k8s.create_secret('nextcloud-pgsql-credentials', 'nextcloud',
                                     {"username": 'nextcloud',
                                      "password": 'we-use-tls-instead-of-password'})

            # redis credentials creation
            nextcloud_redis_password = create_password()
            argocd.k8s.create_secret('nextcloud-redis-credentials', 'nextcloud',
                                     {"password": nextcloud_redis_password})

            # s3 credentials creation
            argocd.k8s.create_secret('nextcloud-s3-credentials', 'nextcloud',
                                     {"accessKeyId": "nextcloud",
                                      "secretAccessKey": s3_access_key,
                                      "S3_ENDPOINT": s3_endpoint})

    if not app_installed:
        # if the user is restoring, the process is a little different
        if init_enabled and restore_enabled:
            restore_nextcloud(argocd,
                              nextcloud_hostname,
                              nextcloud_namespace,
                              cfg['argo'],
                              secrets,
                              restore_dict,
                              backup_vals,
                              pvc_storage_class,
                              'nextcloud-postgres',
                              bitwarden)
        else:
            argocd.install_app('nextcloud', cfg['argo'])
    else:
        log.info("nextcloud already installed 🎉")
        if bitwarden and init_enabled:
            refresh_bweso(argocd, nextcloud_hostname, bitwarden)


def restore_nextcloud(argocd: ArgoCD,
                      nextcloud_hostname: str,
                      nextcloud_namespace: str,
                      argo_dict: dict,
                      secrets: dict,
                      restore_dict: dict,
                      backup_dict: dict,
                      pvc_storage_class: str,
                      pgsql_cluster_name: str,
                      bitwarden: BwCLI) -> None:
    """
    restore nextcloud seaweedfs PVCs, nextcloud files and/or config PVC(s),
    and CNPG postgresql cluster
    """
    # this is the info for the REMOTE backups
    s3_backup_endpoint = backup_dict['endpoint']
    s3_backup_bucket = backup_dict['bucket']
    access_key_id = backup_dict["s3_user"]
    secret_access_key = backup_dict["s3_password"]
    restic_repo_password = backup_dict['restic_repo_pass']
    cnpg_backup_schedule = backup_dict['postgres_schedule']

    # first we grab existing bitwarden items if they exist
    if bitwarden:
        refresh_bweso(argocd, nextcloud_hostname, bitwarden)

        # apply the external secrets so we can immediately use them for restores
        external_secrets_yaml = (
                "https://raw.githubusercontent.com/small-hack/argocd-apps/main/"
                "nextcloud/app_of_apps/external_secrets_argocd_appset.yaml"
                )
        argocd.k8s.apply_manifests(external_secrets_yaml, argocd.namespace)

        # postgresql s3 ID
        s3_db_creds = bitwarden.get_item(
                f"nextcloud-postgres-s3-credentials-{nextcloud_hostname}", False
                )[0]['login']

        pg_access_key_id = s3_db_creds["username"]
        pg_secret_access_key = s3_db_creds["password"]

    # these are the remote backups for seaweedfs
    s3_pvc_capacity = secrets['s3_pvc_capacity']

    # then we create all the seaweedfs pvcs we lost and restore them
    snapshot_ids = restore_dict['restic_snapshot_ids']
    restore_seaweedfs(
            argocd,
            'nextcloud',
            nextcloud_namespace,
            s3_backup_endpoint,
            s3_backup_bucket,
            access_key_id,
            secret_access_key,
            restic_repo_password,
            s3_pvc_capacity,
            pvc_storage_class,
            "ReadWriteOnce",
            snapshot_ids['seaweedfs_volume'],
            snapshot_ids['seaweedfs_master'],
            snapshot_ids['seaweedfs_filer']
            )

    # then we finally can restore the postgres database :D
    if restore_dict.get("cnpg_restore", False):
        psql_version = restore_dict.get("postgresql_version", 16)
        s3_endpoint = secrets.get('s3_endpoint', "")
        restore_cnpg_cluster(argocd.k8s,
                             'nextcloud',
                             nextcloud_namespace,
                             pgsql_cluster_name,
                             psql_version,
                             s3_endpoint,
                             pg_access_key_id,
                             pg_secret_access_key,
                             pgsql_cluster_name,
                             cnpg_backup_schedule)

    # then we begin the restic restore of all the nextcloud PVCs we lost
    for pvc in ['files', 'config']:
        pvc_enabled = secrets.get(f'{pvc}_pvc_enabled', 'false')
        if pvc_enabled and pvc_enabled.lower() != 'false':
            # creates the nexcloud pvc
            recreate_pvc(argocd.k8s,
                         'nextcloud',
                         f'nextcloud-{pvc}',
                         nextcloud_namespace,
                         secrets[f'{pvc}_storage'],
                         pvc_storage_class,
                         secrets[f'{pvc}_access_mode'],
                         "nextcloud-pvc"
                         )

            # restores the nextcloud pvc
            k8up_restore_pvc(argocd.k8s,
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

    # todo: from here on out, this could be async to start on other tasks
    # install nextcloud as usual, but wait on it this time
    argocd.install_app('nextcloud', argo_dict, True)

    # verify nextcloud rolled out completely, just in case
    rollout = (f"kubectl rollout status -n {nextcloud_namespace} "
               "deployment/nextcloud-web-app --watch --timeout 10m")
    while True:
        rolled_out = subproc([rollout], error_ok=True)
        if "NotFound" not in rolled_out:
            break

    # try to update the maintenance mode of nextcloud to off
    nextcloud_obj = Nextcloud(argocd.k8s, nextcloud_namespace)
    nextcloud_obj.set_maintenance_mode("off")


def setup_bitwarden_items(argocd: ArgoCD,
                          nextcloud_hostname: str,
                          s3_endpoint: str,
                          s3_access_key: str,
                          backups_s3_user: str,
                          backups_s3_password: str,
                          restic_repo_pass: str,
                          admin_user: str,
                          mail_host: str,
                          mail_user: str,
                          mail_pass: str,
                          oidc_creds: dict,
                          zitadel_hostname: str,
                          bitwarden: BwCLI) -> None:
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
    argocd.update_appset_secret(
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


def refresh_bweso(argocd: ArgoCD,
                  nextcloud_hostname: str,
                  bitwarden: BwCLI) -> None:
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

    argocd.update_appset_secret(
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
