from rich.prompt import Prompt
from smol_k8s_lab.k8s_apps.minio import BetterMinio
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_tools.argocd_util import install_with_argocd
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.k8s_tools.kubernetes_util import update_secret_key
from smol_k8s_lab.utils.rich_cli.console_logging import sub_header, header
from smol_k8s_lab.utils.passwords import create_password

import logging as log


def configure_nextcloud(k8s_obj: K8s,
                        config_dict: dict,
                        bitwarden: BwCLI = None,
                        minio_obj: BetterMinio = {}) -> bool:
    """
    creates a nextcloud app and initializes it with secrets if you'd like :)
    required:
        k8s_obj     - K8s() object with cluster credentials
        config_dict - dictionary with at least argocd key and init key
    optional:
        bitwarden   - BwCLI() object with session token
    """
    header("Setting up [green]Nextcloud[/], so you can self host your files",
           '🩵')

    # if the user has chosen to use smol-k8s-lab initialization
    if config_dict['init']['enabled']:
        secrets = config_dict['argo']['secret_keys']
        nextcloud_hostname = secrets['hostname']

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
            mail_user = Prompt.ask(
                    f"[green]Please enter the SMTP user for nextcloud on {mail_host}"
                    )
        if not mail_pass:
            m = f"[green]Please enter the SMTP password of {mail_user} for nextcloud"
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

        if bitwarden:
            sub_header("Creating secrets in Bitwarden")

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
                    password='none',
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
            update_secret_key(k8s_obj, 'appset-secret-vars', 'argocd', fields,
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
        else:
            # these are standard k8s secrets
            token = create_password()
            admin_password = create_password()
            # nextcloud admin credentials
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

    install_with_argocd(k8s_obj, 'nextcloud', config_dict['argo'])
    return True
