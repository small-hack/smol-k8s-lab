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
    """
    header("Setting up [green]Nextcloud[/green], so you can self host your files", '🩵')
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
        mail_user = Prompt.ask("[green]Please enter the SMTP user for nextcloud")
        m = f"[green]Please enter the SMTP password of {mail_user} for nextcloud"
        mail_pass = Prompt.ask(m, password=True)

        if bitwarden:
            sub_header("Creating secrets in Bitwarden")
            token = bitwarden.generate()
            password = bitwarden.generate()
            serverinfo_token_obj = create_custom_field("serverinfo_token", token)
            smtpUsername = create_custom_field("smtpUsername", mail_user)
            smtpPassword = create_custom_field("smtpPassword", mail_pass)
            bitwarden.create_login(name='nextcloud-admin-credentials',
                                   item_url=nextcloud_hostname,
                                   user=username,
                                   password=password,
                                   fields=[serverinfo_token_obj, smtpUsername,
                                           smtpPassword])

            nextcloud_pgsql_password = create_custom_field('nextcloudPassword',
                                                           bitwarden.generate())
            nextcloud_pgsql_admin_password = create_custom_field('postgresPassword',
                                                                 bitwarden.generate())
            bitwarden.create_login(name='nextcloud-pgsql-credentials',
                                   item_url=nextcloud_hostname,
                                   user='nextcloud',
                                   password='none',
                                   fields=[nextcloud_pgsql_password,
                                           nextcloud_pgsql_admin_password])

            nextcloud_redis_password = bitwarden.generate()
            bitwarden.create_login(name='nextcloud-redis-credentials',
                                   item_url=nextcloud_hostname,
                                   user='nextcloud',
                                   password=nextcloud_redis_password)
        else:
            # these are standard k8s secrets
            token = create_password()
            password = create_password()
            k8s_obj.create_secret('nextcloud-admin-credentials', 'nextcloud',
                                  {"username": username,
                                   "password": password,
                                   "serverinfo_token": token,
                                   "smtpUsername": mail_user,
                                   "smtpPassword": mail_pass})

            nextcloud_pgsql_password = create_password()
            nextcloud_pgsql_admin_password = create_password()
            k8s_obj.create_secret('nextcloud-pgsql-credentials', 'nextcloud',
                                  {"nextcloudPassword": nextcloud_pgsql_password,
                                   "postgresPassword": nextcloud_pgsql_admin_password})

            nextcloud_redis_password = create_password()
            k8s_obj.create_secret('nextcloud-redis-credentials', 'nextcloud',
                                  {"password": nextcloud_redis_password})

    install_with_argocd(k8s_obj, 'nextcloud', config_dict['argo'])
    return True


def configure_mastodon(k8s_obj: K8s,
                       config_dict: dict,
                       bitwarden: BwCLI = None) -> bool:
    """
    creates a mastodon app and initializes it with secrets if you'd like :)
    """
    header("Setting up [green]Mastodon[/green], so you can self host your social media"
           '🐘')
    if config_dict['init']['enabled']:
        # configure the admin user credentials
        m = "[green]Please enter the name of the administrator user for mastodon"
        username = Prompt.ask(m)
        m = f"[green]Please enter the email of {username} user for mastodon"
        email = Prompt.ask(m)

        secrets = config_dict['argo']['secret_keys']
        mastodon_hostname = secrets['hostname']
        if bitwarden:
            email_obj = create_custom_field("email", email)
            sub_header("Creating secrets in Bitwarden")
            password = bitwarden.generate()
            bitwarden.create_login(name='mastodon-admin-credentials',
                                   item_url=mastodon_hostname,
                                   user=username,
                                   password=password,
                                   fields=[email_obj])

            mastodon_pgsql_password = bitwarden.generate()
            postrges_pass_obj = create_custom_field("postrgesPassword",
                                                    mastodon_pgsql_password)
            bitwarden.create_login(name='mastodon-pgsql-credentials',
                                   item_url=mastodon_hostname,
                                   user='mastodon',
                                   password=mastodon_pgsql_password,
                                   fields=[postrges_pass_obj])

            mastodon_redis_password = bitwarden.generate()
            bitwarden.create_login(name='mastodon-redis-credentials',
                                   item_url=mastodon_hostname,
                                   user='mastodon',
                                   password=mastodon_redis_password)
        else:
            password = create_password()
            # this is a standard k8s secrets yaml
            k8s_obj.create_secret('mastodon-admin-credentials', 'mastodon',
                          {"username": username,
                           "password": password,
                           "email": email})

            mastodon_pgsql_password = create_password()
            k8s_obj.create_secret('mastodon-pgsql-credentials', 'mastodon',
                          {"password": mastodon_pgsql_password,
                           'postrgesPassword': mastodon_pgsql_password})

            mastodon_redis_password = create_password()
            k8s_obj.create_secret('mastodon-redis-credentials', 'mastodon',
                                  {"password": mastodon_redis_password})

    install_with_argocd(k8s_obj, 'mastodon', config_dict['argo'])
    return True


def configure_matrix(k8s_obj: K8s,
                     config_dict: dict,
                     bitwarden: BwCLI = None) -> bool:
    """
    creates a matrix app and initializes it with secrets if you'd like :)
    """
    header("Setting up [green]Matrix[/green], so you can self host your own chat"
           '🔢')

    # initial secrets to deploy this app from scratch
    if config_dict['init']['enabled']:
        secrets = config_dict['argo']['secret_keys']
        matrix_hostname = secrets['hostname']
        if bitwarden:
            sub_header("Creating secrets in Bitwarden")
            matrix_pgsql_password = bitwarden.generate()
            postgres_hostname = create_custom_field("hostname",
                                                    'matrix-web-app-postgresql')
            bitwarden.create_login(
                    name='matrix-pgsql-credentials',
                    item_url=matrix_hostname,
                    user='matrix',
                    password=matrix_pgsql_password,
                    fields=[postgres_hostname])
        else:
            matrix_pgsql_password = create_password()
            k8s_obj.create_secret('matrix-pgsql-credentials', 'matrix',
                                  {"password": matrix_pgsql_password})

    install_with_argocd(k8s_obj, 'matrix', config_dict['argo'])
    return True
