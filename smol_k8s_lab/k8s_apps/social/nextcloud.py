# internal libraries
from smol_k8s_lab.k8s_apps.identity_provider.zitadel_api import Zitadel
from smol_k8s_lab.k8s_apps.minio import BetterMinio
from smol_k8s_lab.k8s_apps.social.nextcloud_occ_commands import Nextcloud
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_tools.argocd_util import (install_with_argocd,
                                                check_if_argocd_app_exists,
                                                wait_for_argocd_app)
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.utils.rich_cli.console_logging import sub_header, header
from smol_k8s_lab.utils.passwords import create_password

# external libraries
import logging as log
from rich.prompt import Prompt


def configure_nextcloud(k8s_obj: K8s,
                        config_dict: dict,
                        bitwarden: BwCLI = None,
                        minio_obj: BetterMinio = None,
                        zitadel: Zitadel = None) -> None:
    """
    creates a nextcloud app and initializes it with secrets if you'd like :)

    required:
        k8s_obj     - K8s() object with cluster credentials
        config_dict - dictionary with at least argocd key and init key

    optional:
        bitwarden   - BwCLI() object with session token
        minio_obj   - BetterMinio() object with minio credentials
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

            # backups values
            access_id = init_values.get('backup_s3_access_id', "nextcloud")
            access_key = init_values.get('backup_s3_access_key', None)
            restic_repo_pass = init_values.get('restic_password', None)

        if secrets:
            s3_endpoint = secrets.get('backup_s3_endpoint', None)
            s3_bucket = secrets.get('backup_s3_bucket', 'nextcloud')

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

        # configure backups
        if secrets['backup_method'] == 'local':
            access_id = '""'
            access_key = '""'
        else:
            if minio_obj and s3_endpoint == "minio":
                access_key = minio_obj.create_access_credentials(access_id)
                minio_obj.create_bucket(s3_bucket, access_id)
            else:
                if not access_id:
                    access_id = Prompt.ask(
                            "[green]Please enter the access ID for s3 backups"
                            )
                if not access_key:
                    access_key = Prompt.ask(
                            "[green]Please enter the access key for s3 backups",
                            password=True
                            )

        # configure OIDC
        if zitadel:
            log.debug("Creating a Nextcloud OIDC application in Zitadel...")
            redirect_uris = f"https://{nextcloud_hostname}/callback"
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
            sub_header("Creating secrets in Bitwarden")

            # create oidc credentials
            bitwarden.create_login(
                    name='nextcloud-oidc-credentials',
                    item_url=nextcloud_hostname,
                    user=oidc_creds['client_id'],
                    password=oidc_creds['client_secret']
                    )

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
            smtpHost = create_custom_field("smtpHost", mail_host)
            smtp_id = bitwarden.create_login(
                    name='nextcloud-smtp-credentials',
                    item_url=nextcloud_hostname,
                    user=mail_user,
                    password=mail_pass,
                    fields=[smtpHost]
                    )

            # postgres db credentials creation
            pgsql_admin_password = create_custom_field('postgresAdminPassword',
                                                       bitwarden.generate())
            db_id = bitwarden.create_login(
                    name='nextcloud-pgsql-credentials',
                    item_url=nextcloud_hostname,
                    user='nextcloud',
                    password='same as the postgresAdminPassword',
                    fields=[pgsql_admin_password]
                    )

            # redis credentials creation
            nextcloud_redis_password = bitwarden.generate()
            redis_id = bitwarden.create_login(
                    name='nextcloud-redis-credentials',
                    item_url=nextcloud_hostname,
                    user='nextcloud',
                    password=nextcloud_redis_password
                    )

            # backups s3 credentials creation
            if not restic_repo_pass:
                restic_repo_pass = bitwarden.generate()
            restic_obj = create_custom_field('resticRepoPassword', restic_repo_pass)
            bucket_obj = create_custom_field('bucket', s3_bucket)
            backup_id = bitwarden.create_login(
                    name='nextcloud-backups-s3-credentials',
                    item_url=s3_endpoint,
                    user=access_id,
                    password=access_key,
                    fields=[restic_obj, bucket_obj]
                    )

            # update the nextcloud values for the argocd appset
            fields = {
                    'nextcloud_admin_credentials_bitwarden_id': admin_id,
                    'nextcloud_smtp_credentials_bitwarden_id': smtp_id,
                    'nextcloud_postgres_credentials_bitwarden_id': db_id,
                    'nextcloud_redis_bitwarden_id': redis_id,
                    'nextcloud_backups_credentials_bitwarden_id': backup_id,
                    }

            k8s_obj.update_secret_key('appset-secret-vars',
                                      'argocd',
                                      fields,
                                      'secret_vars.yaml')

            # reload the argocd appset secret plugin
            try:
                k8s_obj.reload_deployment('argocd-appset-secret-plugin', 'argocd')
            except Exception as e:
                log.error(
                        "Couldn't scale down the "
                        "[magenta]argocd-appset-secret-plugin[/] deployment "
                        f"in [green]argocd[/] namespace. Recieved: {e}"
                        )

            # reload the bitwarden ESO provider
            try:
                k8s_obj.reload_deployment('bitwarden-eso-provider', 'external-secrets')
            except Exception as e:
                log.error(
                        "Couldn't scale down the [magenta]"
                        "bitwarden-eso-provider[/] deployment in [green]"
                        f"external-secrets[/] namespace. Recieved: {e}"
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
            pgsql_nextcloud_password = create_password()
            pgsql_admin_password = create_password()
            k8s_obj.create_secret('nextcloud-pgsql-credentials', 'nextcloud',
                                  {"nextcloudUsername": 'nextcloud',
                                   "nextcloudPassword": pgsql_nextcloud_password,
                                   "postgresPassword": pgsql_admin_password})

            # redis credentials creation
            nextcloud_redis_password = create_password()
            k8s_obj.create_secret('nextcloud-redis-credentials', 'nextcloud',
                                  {"password": nextcloud_redis_password})

            # backups s3 credentials creation
            if not restic_repo_pass:
                restic_repo_pass = create_password()
            k8s_obj.create_secret('nextcloud-backups-credentials', 'nextcloud',
                                  {"applicationKeyId": access_id,
                                   "applicationKey": access_key,
                                   "resticRepoPassword": restic_repo_pass})

    if not app_installed:
        install_with_argocd(k8s_obj, 'nextcloud', config_dict['argo'])

        # optional nextcloud apps to install
        nextcloud_apps = config_dict['init']['values']['nextcloud_apps']

        if init_enabled and nextcloud_apps:
            # make sure the web app is completely up first
            wait_for_argocd_app("nextcloud-web-app")

            # install any apps the user would like to install
            nextcloud = Nextcloud(config_dict['argo']['namespace'])
            nextcloud.install_apps(nextcloud_apps)

            # configure nextcloud social login app to work with zitadel
            zitadel_hostname = zitadel.api_url.replace("/management/v1/", "")
            nextcloud.configure_zitadel_social_login(zitadel_hostname,
                                                     oidc_creds['client_id'],
                                                     oidc_creds['client_secret'])
    else:
        log.info("nextcloud already installed 🎉")

        # if bitwarden and init are enabled, make sure we populate appset secret
        # plugin secret with bitwarden item IDs
        if bitwarden and init_enabled:
            log.debug("Making sure nextcloud Bitwarden item IDs are in appset "
                      "secret plugin secret")
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
            backup_id = bitwarden.get_item(
                    f"nextcloud-backups-credentials-{nextcloud_hostname}"
                    )[0]['id']

            fields = {
                    'nextcloud_admin_credentials_bitwarden_id': admin_id,
                    'nextcloud_smtp_credentials_bitwarden_id': smtp_id,
                    'nextcloud_postgres_credentials_bitwarden_id': db_id,
                    'nextcloud_redis_bitwarden_id': redis_id,
                    'nextcloud_backups_credentials_bitwarden_id': backup_id,
                    }

            k8s_obj.update_secret_key('appset-secret-vars',
                                      'argocd',
                                      fields,
                                      'secret_vars.yaml')

            # reload the argocd appset secret plugin
            try:
                k8s_obj.reload_deployment('argocd-appset-secret-plugin', 'argocd')
            except Exception as e:
                log.error(
                        "Couldn't scale down the "
                        "[magenta]argocd-appset-secret-plugin[/] deployment "
                        f"in [green]argocd[/] namespace. Recieved: {e}"
                        )
