from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_tools.argocd_util import install_with_argocd
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.utils.rich_cli.console_logging import sub_header, header
from smol_k8s_lab.utils.passwords import create_password


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

        # configure the smtp credentials
        smtp_user = config_dict['init']['values']['smtp_user']
        smtp_pass = config_dict['init']['values']['smtp_password']
        smtp_host = config_dict['init']['values']['smtp_host']

        # if the user has bitwarden enabled
        if bitwarden:
            sub_header("Creating secrets in Bitwarden")

            # SMTP credentials
            matrix_pgsql_password = bitwarden.generate()
            postgres_hostname = create_custom_field("hostname",
                                                    'matrix-web-app-postgresql')
            bitwarden.create_login(
                    name='matrix-pgsql-credentials',
                    item_url=matrix_hostname,
                    user='matrix',
                    password=matrix_pgsql_password,
                    fields=[postgres_hostname])

            # SMTP credentials
            matrix_smtp_host_obj = create_custom_field("smtpHostname", smtp_host)
            bitwarden.create_login(name='mastodon-smtp-credentials',
                                   item_url=matrix_hostname,
                                   user=smtp_user,
                                   password=smtp_pass,
                                   fields=[matrix_smtp_host_obj])

        # else create these as Kubernetes secrets
        else:
            matrix_pgsql_password = create_password()
            k8s_obj.create_secret('matrix-pgsql-credentials', 'matrix',
                                  {"password": matrix_pgsql_password})

    install_with_argocd(k8s_obj, 'matrix', config_dict['argo'])
    return True
