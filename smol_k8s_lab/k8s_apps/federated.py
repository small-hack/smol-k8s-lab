from rich.prompt import Prompt
from ..pretty_printing.console_logging import sub_header
from ..k8s_tools.argocd_util import install_with_argocd
from ..k8s_tools.k8s_lib import K8s
from ..utils.bw_cli import BwCLI, create_custom_field
from ..utils.passwords import create_password


def configure_nextcloud(k8s_obj: K8s,
                        argo_dict: dict = {},
                        bitwarden: BwCLI = None) -> bool:
    """
    creates a nextcloud app and initializes it with secrets if you'd like :)
    """
    if argo_dict['init']:
        secrets = argo_dict['argo']['secret_keys']
        nextcloud_hostname = secrets['nextcloud_hostname']

        # configure the admin user credentials
        m = "Please enter the name of the administrator user for nextcloud"
        username = Prompt.ask(m)

        # configure SMTP
        m = "Please enter the SMTP user for nextcloud"
        mail_user = Prompt.ask(m)
        m = f"Please enter the SMTP password of {mail_user} for nextcloud"
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

            nextcloud_pgsql_password = bitwarden.generate()
            bitwarden.create_login(name='nextcloud-pgsql-credentials',
                                   item_url=nextcloud_hostname,
                                   user='nextcloud',
                                   password=nextcloud_pgsql_password)

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
            k8s_obj.create_secret('nextcloud-pgsql-credentials', 'nextcloud',
                                  {"password": nextcloud_pgsql_password})

            nextcloud_redis_password = create_password()
            k8s_obj.create_secret('nextcloud-redis-credentials', 'nextcloud',
                                  {"password": nextcloud_redis_password})

    install_with_argocd(k8s_obj, 'nextcloud', argo_dict)
    return True


def configure_mastodon(k8s_obj: K8s,
                       argo_dict: dict = {},
                       bitwarden: BwCLI = None) -> bool:
    """
    creates a mastodon app and initializes it with secrets if you'd like :)
    """
    if argo_dict['init']:
        # configure the admin user credentials
        m = "Please enter the name of the administrator user for mastodon"
        username = Prompt.ask(m)
        m = f"Please enter the email of {username} user for mastodon"
        email = Prompt.ask(m)

        secrets = argo_dict['argo']['secret_keys']
        mastodon_hostname = secrets['mastodon_hostname']
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

    install_with_argocd(k8s_obj, 'mastodon', argo_dict)
    return True


def configure_matrix(k8s_obj: K8s,
                     argo_dict: dict = {},
                     bitwarden: BwCLI = None) -> bool:
    """
    creates a matrix app and initializes it with secrets if you'd like :)
    """
    # initial secrets to deploy this app from scratch

    if argo_dict['init']:
        secrets = argo_dict['argo']['secret_keys']
        matrix_hostname = secrets['matrix_hostname']
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

    install_with_argocd(k8s_obj, 'matrix', argo_dict)
    return True
