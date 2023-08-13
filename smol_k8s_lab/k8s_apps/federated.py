from ..k8s_tools.argocd import install_with_argocd
from ..k8s_tools.kubernetes_util import create_secret
from ..utils.bw_cli import BwCLI


def configure_nextcloud(argo_dict={}, init=True, bitwarden=BwCLI()):
    """
    creates a nextcloud app and initializes it with secrets if you'd like :)
    """
    if init:
        secrets = argo_dict['secrets']
        if bitwarden:
            sub_header("Creating secrets in Bitwarden")
            admin_password = bitwarden.generate()
            bitwarden.create_login(name='nextcloud-admin-credentials',
                                   item_url=nextcloud_domain,
                                   user=secrets['nextcloud_admin'],
                                   password=admin_password)
        else:
            # this is a standard k8s secrets yaml
            create_secret('nextcloud-login', 'external-secrets',
                          {"username": username, "password": password})

    install_with_argocd('nextcloud', argo_dict)
    return True


def configure_mastodon(argo_dict={}, init=True, bitwarden=BwCLI()):
    """
    creates a mastodon app and initializes it with secrets if you'd like :)
    """
    if init:
        secrets = argo_dict['secrets']
        if bitwarden:
            sub_header("Creating secrets in Bitwarden")
            admin_password = bitwarden.generate()
            bitwarden.create_login(name='mastodon-admin-credentials',
                                   item_url=mastodon_domain,
                                   user=secrets['mastodon_admin'],
                                   password=admin_password)
        else:
            # this is a standard k8s secrets yaml
            create_secret('mastodon-login', 'external-secrets',
                          {"username": username, "password": password})

    install_with_argocd('mastodon', argo_dict)
    return True


def configure_matrix(argo_dict={}, init=True, bitwarden=BwCLI()):
    """
    creates a matrix app and initializes it with secrets if you'd like :)
    """
    if init:
        secrets = argo_dict['secrets']
        if bitwarden:
            sub_header("Creating secrets in Bitwarden")
            admin_password = bitwarden.generate()
            bitwarden.create_login(name='matrix-admin-credentials',
                                   item_url=matrix_domain,
                                   user=secrets['matrix_admin'],
                                   password=admin_password)
        else:
            # this is a standard k8s secrets yaml
            create_secret('matrix-login', 'external-secrets',
                          {"username": username, "password": password})

    install_with_argocd('matrix', argo_dict)
    return True
