# internal libraries
from smol_k8s_lab.k8s_apps.operators.minio import create_minio_alias
from smol_k8s_lab.k8s_apps.identity_provider.zitadel_api import Zitadel
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_tools.argocd_util import (install_with_argocd,
                                                check_if_argocd_app_exists,
                                                update_argocd_appset_secret)
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.utils.rich_cli.console_logging import sub_header, header
from smol_k8s_lab.utils.passwords import create_password

# external libraries
import logging as log
from rich.prompt import Prompt


def configure_nextcloud(k8s_obj: K8s,
                        config_dict: dict,
                        bitwarden: BwCLI = None,
                        zitadel: Zitadel = None) -> None:
    """
    creates a nextcloud app and initializes it with secrets if you'd like :)

    required:
        k8s_obj     - K8s() object with cluster credentials
        config_dict - dictionary with at least argocd key and init key

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
    init_enabled = config_dict['init']['enabled']

    # if the user has chosen to use smol-k8s-lab initialization
    if not app_installed and init_enabled:
        k8s_obj.create_namespace(config_dict['argo']['namespace'])
        header("Setting up [green]Nextcloud[/], to self host your files",
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
            if s3_endpoint:
                s3_access_key = create_password()
                # create a local alias to check and make sure nextcloud is functional
                create_minio_alias("nextcloud", s3_endpoint, "nextcloud", s3_access_key)

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
        if zitadel:
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

        # if bitwarden is enabled, we create login items for each set of credentials
        if bitwarden:
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
                issuer_obj = create_custom_field("issuer", "https://" + zitadel.hostname)
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

        # these are standard k8s secrets
        else:
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
        install_with_argocd(k8s_obj, 'nextcloud', config_dict['argo'])
    else:
        log.info("nextcloud already installed 🎉")

        # if bitwarden and init are enabled, make sure we populate appset secret
        # plugin secret with bitwarden item IDs
        if bitwarden and init_enabled:
            log.debug("Making sure nextcloud Bitwarden item IDs are in appset "
                      "secret plugin secret")
            oidc_id = bitwarden.get_item(
                    f"nextcloud-oidc-credentials-{nextcloud_hostname}"
                    )[0]['id']

            admin_id = bitwarden.get_item(
                    f"nextcloud-admin-credentials-{nextcloud_hostname}"
                    )[0]['id']

            smtp_id = bitwarden.get_item(
                    f"nextcloud-smtp-credentials-{nextcloud_hostname}"
                    )[0]['id']

            db_id = bitwarden.get_item(
                    f"nextcloud-pgsql-credentials-{nextcloud_hostname}"
                    )[0]['id']

            redis_id = bitwarden.get_item(
                    f"nextcloud-redis-credentials-{nextcloud_hostname}"
                    )[0]['id']

            s3_admin_id = bitwarden.get_item(
                    f"nextcloud-admin-s3-credentials-{nextcloud_hostname}"
                    )[0]['id']

            s3_db_id = bitwarden.get_item(
                    f"nextcloud-postgres-s3-credentials-{nextcloud_hostname}"
                    )[0]['id']

            s3_id = bitwarden.get_item(
                    f"nextcloud-user-s3-credentials-{nextcloud_hostname}"
                    )[0]['id']

            s3_backups_id = bitwarden.get_item(
                    f"nextcloud-backups-s3-credentials-{nextcloud_hostname}"
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
