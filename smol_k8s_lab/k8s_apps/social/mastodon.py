from rich.prompt import Prompt
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_tools.argocd_util import install_with_argocd
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.utils.rich_cli.console_logging import sub_header, header
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
        username = config_dict['init']['values']['admin_user']
        email = config_dict['init']['values']['admin_email']
        s3_endpoint = config_dict['init']['values']['s3_endpoint']
        s3_bucket = config_dict['init']['values']['s3_bucket']

        # configure the smtp credentials
        smtp_user = config_dict['init']['values']['smtp_user']
        smtp_pass = config_dict['init']['values']['smtp_password']
        smtp_host = config_dict['init']['values']['smtp_host']

        # configure s3 credentials if they're in use
        s3_access_id = config_dict['init']['values']['s3_access_id']
        s3_access_key = config_dict['init']['values']['s3_access_key']

        secrets = config_dict['argo']['secret_keys']
        mastodon_hostname = secrets['hostname']

        if bitwarden:
            # admin credentials
            email_obj = create_custom_field("email", email)
            sub_header("Creating secrets in Bitwarden")
            password = bitwarden.generate()
            bitwarden.create_login(name='mastodon-admin-credentials',
                                   item_url=mastodon_hostname,
                                   user=username,
                                   password=password,
                                   fields=[email_obj])

            # PostgreSQL credentials
            mastodon_pgsql_password = bitwarden.generate()
            postrges_pass_obj = create_custom_field("postrgesPassword",
                                                    mastodon_pgsql_password)
            bitwarden.create_login(name='mastodon-pgsql-credentials',
                                   item_url=mastodon_hostname,
                                   user='mastodon',
                                   password=mastodon_pgsql_password,
                                   fields=[postrges_pass_obj])

            # Redis credentials
            mastodon_redis_password = bitwarden.generate()
            bitwarden.create_login(name='mastodon-redis-credentials',
                                   item_url=mastodon_hostname,
                                   user='mastodon',
                                   password=mastodon_redis_password)

            # SMTP credentials
            mastodon_smtp_host_obj = create_custom_field("smtpHostname",
                                                         smtp_host)
            bitwarden.create_login(name='mastodon-smtp-credentials',
                                   item_url=mastodon_hostname,
                                   user=smtp_user,
                                   password=smtp_pass,
                                   fields=[mastodon_smtp_host_obj])

            # S3 credentials
            mastodon_s3_host_obj = create_custom_field("s3Endpoint",
                                                       s3_endpoint)
            mastodon_s3_bucket_obj = create_custom_field("s3Bucket",
                                                         s3_bucket)
            bitwarden.create_login(name='mastodon-s3-credentials',
                                   item_url=mastodon_hostname,
                                   user=s3_access_id,
                                   password=s3_access_key,
                                   fields=[mastodon_s3_host_obj,
                                           mastodon_s3_bucket_obj])

        # these are standard k8s secrets yaml
        else:
            password = create_password()
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
