import logging as log
import json
from rich.prompt import Prompt
from .vouch import configure_vouch
from ..console_logging import sub_header, header
from ..k8s_tools.kubernetes_util import create_secret
from ..k8s_tools.argocd import install_with_argocd
from ..subproc import subproc
from ..utils.bw_cli import BwCLI
from ..utils.passwords import create_password


def configure_zitadel_and_vouch(zitadel_config_dict: dict = {},
                                vouch_config_dict: dict = {},
                                bitwarden=None):
    """
    Installs zitadel and Vouch as Argo CD Applications. If
    zitadel_config_dict['init'] is True, it also configures Vouch and Argo CD
    as OIDC Clients.

    Required Arguments:
        zitadel_config_dict: dict, Argo CD parameters for zitadel

    Optional Arguments:
        vouch_config_dict: dict, Argo CD parameters for vouch
        bitwarden:         BwCLI obj, [optional] contains bitwarden session

    Returns True if successful.
    """
    header("🔑 Zitadel Setup")

    # if we're using bitwarden, create the secrets in bitwarden before
    # creating Argo CD app
    if zitadel_config_dict['init']:
        secrets = zitadel_config_dict['argo']['secret_keys']
        zitadel_domain = secrets['zitadel_domain']

        if bitwarden:
            sub_header("Creating secrets in Bitwarden")
            admin_password = bitwarden.generate()
            bitwarden.create_login(name='zitadel-admin-credentials',
                                   item_url=zitadel_domain,
                                   user=secrets['zitadel_admin'],
                                   password=admin_password)

        # if we're not using bitwarden, create the k8s secrets directly
        else:
            sub_header("Creating secrets in k8s")
            admin_password = create_password()
            create_secret('zitadel-admin-credentials', 'zitadel',
                          {'password': admin_password})

    install_with_argocd('zitadel', zitadel_config_dict['argo'])

    # only continue through the rest of the function if we're initializes a
    # user and vouch/argocd clients in zitadel
    if not zitadel_config_dict['init']:
        return True
    else:
        configure_zitadel(zitadel_domain, bitwarden, vouch_config_dict)


def configure_zitadel(zitadel_domain: str = "", bitwarden=None,
                      vouch_config_dict: dict = {}):
    """
    Sets up initial zitadel user, Argo CD client, and optional Vouch client.
    Arguments:
        bitwarden:         BwCLI obj, [optional] session to use for bitwarden
        vouch_config_dict: dict, [optional] Argo CD vouch parameters
    """

    sub_header("Configure zitadel as your OIDC SSO for Argo CD")
    username = Prompt("What would you like your Zitadel username to be?")
    first_name = Prompt("Enter your First name for your Zitadel profile")
    last_name = Prompt("Enter your Last name for your Zitadel profile")

    begin = ("kubectl exec -n zitadel zitadel-web-app-0 -- "
             "/opt/bitnami/zitadel/bin/kcadm.sh ")

    log.info("Creating a new user...")
    # create a new user
    create_user = (f"{begin} create users -s username={username}"
                   f"-s enabled=true -s firstName={first_name} "
                   f"-s lastName={last_name}")

    log.info("Creating an Argo CD client...")
    # create an argocd client
    create_argocd_client = (f"{begin} create clients "
                            f"-s enabled=true -s clientId=argocd")

    vouch_enabled = vouch_config_dict['enabled']
    if vouch_enabled:
        log.info("Creating an Argo CD client...")
        # create a vouch client
        create_vouch_client = (f"{begin} create clients "
                               f" -s enabled=true -s clientId=vouch")

    subproc([create_user, create_argocd_client, create_vouch_client])

    # get vouch and argocd client
    clients = f"{begin} get clients --fields clientId,secret"
    client_json = json.loads(subproc([clients]))

    for client in client_json:
        if client_json['clientId'] == 'argocd':
            argocd_client_secret = client_json['secret']
        if client_json['clientId'] == 'vouch':
            vouch_client_secret = client_json['secret']

    if bitwarden:
        sub_header("Creating OIDC secrets for Argo CD and Vouch in Bitwarden")
        bitwarden.create_login(name='argocd-external-oidc',
                               user='argocd',
                               password=argocd_client_secret)
    else:
        # the argocd secret needs labels.app.kubernetes.io/part-of: "argocd"
        create_secret('argocd-external-oidc', 'argocd',
                      {'user': 'argocd',
                       'password': argocd_client_secret}, False,
                      {'app.kubernetes.io/part-of': 'argocd'})

    if vouch_enabled:
        url = f"https://{zitadel_domain}/protocol/openid-connect/"
        configure_vouch(vouch_config_dict, vouch_client_secret, url, bitwarden)

    return True 
