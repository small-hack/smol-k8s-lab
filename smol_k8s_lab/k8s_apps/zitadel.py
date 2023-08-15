import logging as log
from .vouch import configure_vouch
from .zitadel_api import Zitadel
from ..pretty_printing.console_logging import sub_header, header
from ..k8s_tools.kubernetes_util import update_secret_key
from ..k8s_tools.k8s_lib import K8s
from ..k8s_tools.argocd import install_with_argocd
from ..utils.bw_cli import BwCLI
from ..utils.passwords import create_password


def configure_zitadel_and_vouch(zitadel_config_dict: dict = {},
                                k8s_obj: K8s() = K8s(),
                                argocd_hostname: str = "",
                                vouch_config_dict: dict = {},
                                bitwarden=None):
    """
    Installs zitadel and Vouch as Argo CD Applications. If
    zitadel_config_dict['init'] is True, it also configures Vouch and Argo CD
    as OIDC Clients.

    Required Arguments:
        zitadel_config_dict: dict, Argo CD parameters for zitadel
        k8s_obj:             K8s(), kubrenetes client for creating secrets

    Optional Arguments:
        argocd_hostname:   str, the hostname of Argo CD
        vouch_config_dict: dict, Argo CD parameters for vouch
        bitwarden:         BwCLI obj, [optional] contains bitwarden session

    Returns True if successful.
    """
    header("🔑 Zitadel Setup")

    # if we're using bitwarden, create the secrets in bitwarden before
    # creating Argo CD app
    if zitadel_config_dict['init']:
        secrets = zitadel_config_dict['argo']['secret_keys']
        zitadel_hostname = secrets['zitadel_hostname']

        if bitwarden:
            sub_header("Creating secrets in Bitwarden")
            admin_password = bitwarden.generate()
            bitwarden.create_login(name='zitadel-admin-credentials',
                                   item_url=zitadel_hostname,
                                   user=secrets['zitadel_admin'],
                                   password=admin_password)

        # if we're not using bitwarden, create the k8s secrets directly
        else:
            sub_header("Creating secrets in k8s")
            admin_password = create_password()
            k8s_obj.create_secret('zitadel-admin-credentials', 'zitadel',
                                  {'password': admin_password})

    install_with_argocd('zitadel', zitadel_config_dict['argo'])

    # only continue through the rest of the function if we're initializes a
    # user and vouch/argocd clients in zitadel
    if not zitadel_config_dict['init']:
        return True
    else:
        configure_zitadel(zitadel_hostname, argocd_hostname, bitwarden,
                          vouch_config_dict)


def configure_zitadel(zitadel_hostname: str = "", argocd_hostname: str = "",
                      k8s_obj: K8s() = K8s(), bitwarden=None,
                      vouch_config_dict: dict = {}):
    """
    Sets up initial zitadel user, Argo CD client, and optional Vouch client.
    Arguments:
        zitadel_hostname:  str, the hostname of Zitadel
        argocd_hostname:   str, the hostname of Argo CD
        k8s_obj:             K8s(), kubrenetes client for creating secrets
        bitwarden:         BwCLI obj, [optional] session to use for bitwarden
        vouch_config_dict: dict, [optional] Argo CD vouch parameters
    """

    sub_header("Configure zitadel as your OIDC SSO for Argo CD")
    zitadel =  Zitadel(f"https://{zitadel_hostname}/management/v1/")

    log.info("Creating a groups Zitadel Action (sends group info to Argo)")
    zitadel.create_action("groupsClaim")

    # create Argo CD OIDC Application
    log.info("Creating an Argo CD application...")
    redirect_uris = [f"https://{argocd_hostname}/auth/callback"]
    logout_uris = [f"https://{argocd_hostname}"]
    argocd_client = zitadel.create_application("argocd", redirect_uris,
                                               logout_uris)

    # create roles for both Argo CD Admins and regular users
    zitadel.create_role("argocd_administrators", "Argo CD Administrators",
                        "argocd_administrators")
    zitadel.create_role("argocd_users", "Argo CD Users", "argocd_users")

    # update the existing appset-secret-vars secret with issuer and client_id
    update_secret_key(k8s_obj, 'appset-secret-vars', 'argocd',
                      {'argocd_oidc_client_id': argocd_client['client_id'],
                       'argocd_oidc_issuer': f"https://{zitadel_hostname}"},
                      'secret_vars.yaml')

    if bitwarden:
        sub_header("Creating OIDC secrets for Argo CD and Vouch in Bitwarden")
        bitwarden.create_login(name='argocd-external-oidc',
                               user='argocd',
                               password=argocd_client['client_secret'])
    else:
        # the argocd secret needs labels.app.kubernetes.io/part-of: "argocd"
        k8s_obj.create_secret('argocd-external-oidc', 'argocd',
                              {'user': 'argocd',
                               'password': argocd_client['client_secret']},
                              labels={'app.kubernetes.io/part-of': 'argocd'})

    # create zitadel user and grants now that the clients are setup
    log.info("Creating a Zitadel user...")
    user_id = zitadel.create_user()
    zitadel.create_user_grant(user_id, 'argocd_administrators')

    vouch_enabled = vouch_config_dict['enabled']
    if vouch_enabled:
        vouch_hostname = vouch_config_dict['argo']['secret_keys']['hostname']
        # create Vouch OIDC Application
        log.info("Creating a Vouch application...")
        redirect_uris = [f"https://{vouch_hostname}/auth/callback"]
        logout_uris = [f"https://{vouch_hostname}"]
        vouch_client_creds = zitadel.create_application("vouch",
                                                        redirect_uris,
                                                        logout_uris)

    if vouch_enabled:
        url = f"https://{zitadel_hostname}/"
        configure_vouch(vouch_config_dict, vouch_client_creds, url, bitwarden)

    return True
