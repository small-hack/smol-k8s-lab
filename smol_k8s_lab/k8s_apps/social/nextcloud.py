from rich.prompt import Prompt
from smol_k8s_lab.k8s_tools.argocd_util import install_with_argocd
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.utils.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.utils.pretty_printing.console_logging import sub_header, header
from smol_k8s_lab.utils.passwords import create_password


def configure_nextcloud(k8s_obj: K8s,
                        config_dict: dict,
                        bitwarden: BwCLI = None) -> bool:
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
    if config_dict['init']['enabled']:
        secrets = config_dict['argo']['secret_keys']
        nextcloud_hostname = secrets['hostname']

        # configure the admin user credentials
        init_values = config_dict['init'].get('values', None)
        if init_values:
            username = init_values.get('username', None)
        if not username:
            m = "[green]Please enter the name of the administrator user for nextcloud"
            username = Prompt.ask(m)

        # configure SMTP
        mail_host = Prompt.ask("[green]Please enter the SMTP host for nextcoud")
        mail_user = Prompt.ask("[green]Please enter the SMTP user for nextcloud")
        m = f"[green]Please enter the SMTP password of {mail_user} for nextcloud"
        mail_pass = Prompt.ask(m, password=True)

        # configure backups
        if secrets['backup_method'] == 'local':
            access_id = '""'
            access_key = '""'
        else:
            access_id = Prompt.ask("[green]Please enter the access ID for s3 backups")
            access_key = Prompt.ask("[green]Please enter the access key for s3 backups",
                                    password=True)

        if not Prompt.confirm("[green]Do you have an existing restic repo password?"):
            m = "[green]Please enter the restic repo password"
            restic_repo_pass = Prompt.ask(m, password=True)

        if bitwarden:
            sub_header("Creating secrets in Bitwarden")
            token = bitwarden.generate()
            password = bitwarden.generate()
            serverinfo_token_obj = create_custom_field("serverInfoToken", token)
            smtpUsername = create_custom_field("smtpUsername", mail_user)
            smtpPassword = create_custom_field("smtpPassword", mail_pass)
            smtpHost = create_custom_field("smtpHost", mail_host)
            bitwarden.create_login(name='nextcloud-admin-credentials',
                                   item_url=nextcloud_hostname,
                                   user=username,
                                   password=password,
                                   fields=[serverinfo_token_obj,
                                           smtpHost,
                                           smtpUsername,
                                           smtpPassword])

            # postgres db credentials creation
            pgsql_admin_password = create_custom_field('postgresAdminPassword',
                                                       bitwarden.generate())
            bitwarden.create_login(name='nextcloud-pgsql-credentials',
                                   item_url=nextcloud_hostname,
                                   user='nextcloud',
                                   password='none',
                                   fields=[pgsql_admin_password])

            # redis credentials creation
            nextcloud_redis_password = bitwarden.generate()
            bitwarden.create_login(name='nextcloud-redis-credentials',
                                   item_url=nextcloud_hostname,
                                   user='nextcloud',
                                   password=nextcloud_redis_password)

            # backups s3 credentials creation
            if not restic_repo_pass:
                restic_repo_pass = bitwarden.generate()
            bitwarden.create_login(name='nextcloud-backups-credentials',
                                   item_url=nextcloud_hostname,
                                   user=access_id,
                                   password=access_key,
                                   fields=[create_custom_field('resticRepoPassword',
                                                               restic_repo_pass)])
        else:
            # these are standard k8s secrets
            token = create_password()
            password = create_password()
            # nextcloud admin credentials
            k8s_obj.create_secret('nextcloud-admin-credentials', 'nextcloud',
                                  {"username": username,
                                   "password": password,
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
