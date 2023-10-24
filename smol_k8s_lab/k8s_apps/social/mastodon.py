from rich.prompt import Prompt
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_tools.argocd_util import install_with_argocd
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.k8s_tools.kubernetes_util import update_secret_key
from smol_k8s_lab.utils.rich_cli.console_logging import sub_header, header
from smol_k8s_lab.utils.passwords import create_password

import logging as log


def configure_mastodon(k8s_obj: K8s,
                       config_dict: dict,
                       bitwarden: BwCLI = None,
                       minio_credentials: dict = {}) -> bool:
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
            admin_id = bitwarden.create_login(
                    name='mastodon-admin-credentials',
                    item_url=mastodon_hostname,
                    user=username,
                    password=password,
                    fields=[email_obj]
                    )

            # PostgreSQL credentials
            mastodon_pgsql_password = bitwarden.generate()
            postrges_pass_obj = create_custom_field("postrgesPassword",
                                                    mastodon_pgsql_password)
            db_id = bitwarden.create_login(
                    name='mastodon-pgsql-credentials',
                    item_url=mastodon_hostname,
                    user='mastodon',
                    password=mastodon_pgsql_password,
                    fields=[postrges_pass_obj]
                    )

            # Redis credentials
            mastodon_redis_password = bitwarden.generate()
            redis_id = bitwarden.create_login(
                    name='mastodon-redis-credentials',
                    item_url=mastodon_hostname,
                    user='mastodon',
                    password=mastodon_redis_password
                    )

            # SMTP credentials
            mastodon_smtp_host_obj = create_custom_field("smtpHostname", smtp_host)
            smtp_id = bitwarden.create_login(
                    name='mastodon-smtp-credentials',
                    item_url=mastodon_hostname,
                    user=smtp_user,
                    password=smtp_pass,
                    fields=[mastodon_smtp_host_obj]
                    )

            # S3 credentials
            mastodon_s3_host_obj = create_custom_field("s3Endpoint", s3_endpoint)
            mastodon_s3_bucket_obj = create_custom_field("s3Bucket", s3_bucket)
            s3_id = bitwarden.create_login(
                    name='mastodon-s3-credentials',
                    item_url=mastodon_hostname,
                    user=s3_access_id,
                    password=s3_access_key,
                    fields=[mastodon_s3_host_obj,
                    mastodon_s3_bucket_obj]
                    )

            # update the mastodon values for the argocd appset
            fields = {
                    'mastodon_admin_credentials_bitwarden_id': admin_id,
                    'mastodon_smtp_credentials_bitwarden_id': smtp_id,
                    'mastodon_postgres_credentials_bitwarden_id': db_id,
                    'mastodon_redis_bitwarden_id': redis_id,
                    'mastodon_s3_credentials_bitwarden_id': s3_id,
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
                        "Couldn't scale down the [magenta]bitwarden-eso-provider"
                        "[/] deployment in [green]external-secrets[/] namespace."
                        f"Recieved: {e}"
                        )

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
