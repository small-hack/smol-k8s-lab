from rich.prompt import Prompt
from smol_k8s_lab.k8s_tools.argocd_util import install_with_argocd
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.utils.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.utils.pretty_printing.console_logging import sub_header, header
from smol_k8s_lab.utils.passwords import create_password


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
