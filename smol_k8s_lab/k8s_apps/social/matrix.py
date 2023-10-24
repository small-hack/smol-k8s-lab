from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_tools.argocd_util import install_with_argocd
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.k8s_tools.kubernetes_util import update_secret_key
from smol_k8s_lab.utils.rich_cli.console_logging import sub_header, header
from smol_k8s_lab.utils.passwords import create_password

import logging as log

def configure_matrix(k8s_obj: K8s,
                     config_dict: dict,
                     bitwarden: BwCLI = None,
                     minio_credentials: dict = {}) -> bool:
    """
    creates a matrix app and initializes it with secrets if you'd like :)
    """
    header("Setting up [green]Matrix[/green], so you can self host your own chat"
           '🔢')

    # initial secrets to deploy this app from scratch
    if config_dict['init']['enabled']:
        secrets = config_dict['argo']['secret_keys']
        matrix_hostname = secrets['hostname']

        # configure the smtp credentials
        smtp_user = config_dict['init']['values']['smtp_user']
        smtp_pass = config_dict['init']['values']['smtp_password']
        smtp_host = config_dict['init']['values']['smtp_host']

        # if the user has bitwarden enabled
        if bitwarden:
            sub_header("Creating secrets in Bitwarden")

            # postgresql credentials
            matrix_pgsql_password = bitwarden.generate()
            postgres_hostname = create_custom_field("hostname",
                                                    'matrix-web-app-postgresql')
            db_id = bitwarden.create_login(
                    name='matrix-pgsql-credentials',
                    item_url=matrix_hostname,
                    user='matrix',
                    password=matrix_pgsql_password,
                    fields=[postgres_hostname]
                    )

            # SMTP credentials
            matrix_smtp_host_obj = create_custom_field("smtpHostname", smtp_host)
            smtp_id = bitwarden.create_login(
                    name='mastodon-smtp-credentials',
                    item_url=matrix_hostname,
                    user=smtp_user,
                    password=smtp_pass,
                    fields=[matrix_smtp_host_obj]
                    )

            # registration key
            matrix_registration_key = bitwarden.generate()
            reg_id = bitwarden.create_login(
                    name='mastodon-registration-key',
                    item_url=matrix_hostname,
                    user="admin",
                    password=matrix_registration_key
                    )

            # update the matrix values for the argocd appset
            fields = {
                    'matrix_oidc_credentials_bitwarden_id': "not-set-yet",
                    'matrix_registration_credentials_bitwarden_id': reg_id,
                    'matrix_smtp_credentials_bitwarden_id': smtp_id,
                    'matrix_postgres_credentials_bitwarden_id': db_id,
                    }
            update_secret_key(k8s_obj, 'appset-secret-vars', 'argocd', fields,
                              'secret_vars.yaml')

            # reload the argocd appset secret plugin
            try:
                k8s_obj.reload_deployment('argocd-appset-secret-plugin', 'argocd')
            except Exception as e:
                log.error(
                        "Couldn't scale down the "
                        "[magenta]argocd-appset-secret-plugin[/]"
                        "deployment in [green]argocd[/] namespace. Recieved: "
                        f"{e}"
                        )

            # reload the bitwarden ESO provider
            try:
                k8s_obj.reload_deployment('bitwarden-eso-provider', 'external-secrets')
            except Exception as e:
                log.error(
                        "Couldn't scale down the [magenta]bitwarden-eso-provider[/]"
                        "deployment in [green]external-secrets[/] namespace. Recieved: "
                        f"{e}"
                        )

        # else create these as Kubernetes secrets
        else:
            matrix_pgsql_password = create_password()
            k8s_obj.create_secret('matrix-pgsql-credentials', 'matrix',
                                  {"password": matrix_pgsql_password})
            matrix_registration_key = create_password()
            k8s_obj.create_secret('matrix-registration', 'matrix',
                                  {"registrationSharedSecret": matrix_registration_key})

    install_with_argocd(k8s_obj, 'matrix', config_dict['argo'])
    return True
