# internal libraries
from smol_k8s_lab.k8s_apps.identity_provider.zitadel_api import Zitadel
from smol_k8s_lab.k8s_apps.social.nextcloud_occ_commands import Nextcloud
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_tools.argocd_util import (install_with_argocd,
                                                check_if_argocd_app_exists,
                                                wait_for_argocd_app,
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
        bitwarden   - BwCLI() object with session token
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

            # s3 values
            s3_access_id = init_values.get('s3_access_id', "nextcloud")
            s3_access_key = init_values.get('s3_access_key', create_password())
            if config_dict['argo']['directory_recursion']:
                default_minio = True
            else:
                default_minio = False
            create_minio_tenant = init_values.get('create_minio_tenant',
                                                  default_minio)

        if secrets:
            s3_endpoint = secrets.get('s3_endpoint', "")
            s3_bucket = secrets.get('s3_bucket', 'nextcloud')

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

        # configure s3 storage
        # creates the initial root credentials secret for the minio tenant
        if create_minio_tenant:
            credentials_exports = {
                    'config.env': f"""MINIO_ROOT_USER={s3_access_id}
            MINIO_ROOT_PASSWORD={s3_access_key}"""}
            k8s_obj.create_secret('default-tenant-env-config',
                                  config_dict['argo']['namespace'],
                                  credentials_exports)

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
            sub_header("Creating secrets in Bitwarden")

            # create oidc credentials
            issuer_obj = create_custom_field("issuer",
                                             zitadel.api_url.replace("/management/v1/",
                                                                     "")
                                             )
            oidc_id = bitwarden.create_login(
                    name='nextcloud-oidc-credentials',
                    item_url=nextcloud_hostname,
                    user=oidc_creds['client_id'],
                    password=oidc_creds['client_secret'],
                    fields=[issuer_obj]
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
            db_id = bitwarden.create_login(
                    name='nextcloud-pgsql-credentials',
                    item_url=nextcloud_hostname,
                    user='nextcloud',
                    password=bitwarden.generate()
                    )

            # redis credentials creation
            nextcloud_redis_password = bitwarden.generate()
            redis_id = bitwarden.create_login(
                    name='nextcloud-redis-credentials',
                    item_url=nextcloud_hostname,
                    user='nextcloud',
                    password=nextcloud_redis_password
                    )

            # s3 credentials creation
            bucket_obj = create_custom_field('bucket', s3_bucket)
            encryption_obj = create_custom_field('encryption_key', create_password())
            endpoint_obj = create_custom_field('endpoint', s3_endpoint)
            s3_id = bitwarden.create_login(
                    name='nextcloud-s3-credentials',
                    item_url=nextcloud_hostname,
                    user=s3_access_id,
                    password=s3_access_key,
                    fields=[bucket_obj, encryption_obj, endpoint_obj]
                    )

            # update the nextcloud values for the argocd appset
            update_argocd_appset_secret(
                    k8s_obj,
                    {'nextcloud_admin_credentials_bitwarden_id': admin_id,
                     'nextcloud_oidc_credentials_bitwarden_id': oidc_id,
                     'nextcloud_smtp_credentials_bitwarden_id': smtp_id,
                     'nextcloud_postgres_credentials_bitwarden_id': db_id,
                     'nextcloud_redis_bitwarden_id': redis_id,
                     'nextcloud_s3_credentials_bitwarden_id': s3_id}
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
            k8s_obj.create_secret('nextcloud-pgsql-credentials', 'nextcloud',
                                  {"username": 'nextcloud',
                                   "password": pgsql_nextcloud_password})

            # redis credentials creation
            nextcloud_redis_password = create_password()
            k8s_obj.create_secret('nextcloud-redis-credentials', 'nextcloud',
                                  {"password": nextcloud_redis_password})

            # s3 credentials creation
            encryption_key = create_password()
            k8s_obj.create_secret('nextcloud-s3-credentials', 'nextcloud',
                                  {"S3_USER": s3_access_id,
                                   "S3_PASSWORD": s3_access_key,
                                   "S3_ENCRYPTION_KEY": encryption_key,
                                   "S3_ENDPOINT": s3_endpoint})

    if not app_installed:
        install_with_argocd(k8s_obj, 'nextcloud', config_dict['argo'])

        # optional nextcloud apps to install
        nextcloud_apps = config_dict['init']['values']['nextcloud_apps']

        if init_enabled and nextcloud_apps:
            # make sure the web app is completely up first
            wait_for_argocd_app("nextcloud-web-app")

            # install any apps the user passed in as an init value
            nextcloud = Nextcloud(config_dict['argo']['namespace'])
            nextcloud.install_apps(nextcloud_apps)
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
            s3_id = bitwarden.get_item(
                    f"nextcloud-s3-credentials-{nextcloud_hostname}"
                    )[0]['id']

            update_argocd_appset_secret(
                    k8s_obj,
                    {'nextcloud_admin_credentials_bitwarden_id': admin_id,
                     'nextcloud_oidc_credentials_bitwarden_id': oidc_id,
                     'nextcloud_smtp_credentials_bitwarden_id': smtp_id,
                     'nextcloud_postgres_credentials_bitwarden_id': db_id,
                     'nextcloud_redis_bitwarden_id': redis_id,
                     'nextcloud_s3_credentials_bitwarden_id': s3_id,
                    })
