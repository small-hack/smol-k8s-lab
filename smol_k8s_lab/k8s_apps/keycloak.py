import logging as log
import json
from rich.prompt import Prompt
from .vouch import configure_vouch
from ..pretty_printing.console_logging import sub_header, header
from ..k8s_tools.k8s_lib import K8s
from ..k8s_tools.argocd import install_with_argocd
from ..subproc import subproc
from ..utils.bw_cli import BwCLI
from ..utils.passwords import create_password


def configure_keycloak_and_vouch(k8s_obj: K8s,
                                 keycloak_config_dict: dict = {},
                                 vouch_config_dict: dict = {},
                                 bitwarden=None):
    """
    Installs Keycloak and Vouch as Argo CD Applications. If
    keycloak_config_dict['init'] is True, it also configures Vouch and Argo CD
    as OIDC Clients.

    Required Arguments:
        keycloak_config_dict: dict, Argo CD parameters for keycloak

    Optional Arguments:
        vouch_config_dict: dict, Argo CD parameters for vouch
        bitwarden:         BwCLI obj, [optional] contains bitwarden session

    Returns True if successful.
    """
    header("🗝️Keycloak Setup")

    # if we're using bitwarden, create the secrets in bitwarden before
    # creating Argo CD app
    if keycloak_config_dict['init']:
        secrets = keycloak_config_dict['argo']['secret_keys']
        keycloak_hostname = secrets['hostname']

        if bitwarden:
            sub_header("Creating secrets in Bitwarden")
            admin_password = bitwarden.generate()
            postgres_password = bitwarden.generate()
            bitwarden.create_login(name='keycloak-admin-credentials',
                                   item_url=keycloak_hostname,
                                   user=secrets['keycloak_admin'],
                                   password=admin_password)
            bitwarden.create_login(name='keycloak-postgres-credentials',
                                   item_url=keycloak_hostname,
                                   user='keycloak',
                                   password=postgres_password)

        # if we're not using bitwarden, create the k8s secrets directly
        else:
            sub_header("Creating secrets in k8s")
            admin_password = create_password()
            k8s_obj.create_secret('keycloak-admin-credentials', 'keycloak',
                                  {'password': admin_password})
            postgres_password = create_password()
            k8s_obj.create_secret('keycloak-postgres-credentials', 'keycloak',
                                  {'password': postgres_password,
                                   'postgres-password': postgres_password})

    install_with_argocd(k8s_obj, 'keycloak', keycloak_config_dict['argo'])

    # only continue through the rest of the function if we're initializes a
    # user and vouch/argocd clients in keycloak
    if not keycloak_config_dict['init']:
        return True
    else:
        realm = secrets['default_realm']
        configure_keycloak(k8s_obj, realm, keycloak_hostname, bitwarden,
                           vouch_config_dict)


def configure_keycloak(k8s_obj: K8s, realm: str = "",
                       keycloak_hostname: str = "", bitwarden=None,
                       vouch_config_dict: dict = {}):
    """
    Sets up initial Keycloak user, Argo CD client, and optional Vouch client.
    Arguments:
        realm:             str, name of the keycloak realm to use
        bitwarden:         BwCLI obj, [optional] session to use for bitwarden
        vouch_config_dict: dict, [optional] Argo CD vouch parameters
    """

    sub_header("Configure Keycloak as your OIDC SSO for Argo CD")
    username = Prompt("What would you like your Keycloak username to be?")
    first_name = Prompt("Enter your First name for your keycloak profile")
    last_name = Prompt("Enter your Last name for your keycloak profile")

    begin = ("kubectl exec -n keycloak keycloak-web-app-0 -- "
             "/opt/bitnami/keycloak/bin/kcadm.sh ")
    end = (f"-o --no-config --server http://localhost:8080/ --realm {realm}"
           "--user KEYCLOAK_ADMIN --password $KEYCLOAK_ADMIN_PASSWORD")

    log.info("Creating a new user...")
    # create a new user
    create_user = (f"{begin} create users -r {realm} -s username={username}"
                   f"-s enabled=true -s firstName={first_name} "
                   f"-s lastName={last_name} {end}")

    log.info("Creating an Argo CD client...")
    # create an argocd client
    create_argocd_client = (f"{begin} create clients -r {realm} "
                            f"-s enabled=true -s clientId=argocd {end}")

    vouch_enabled = vouch_config_dict['enabled']
    if vouch_enabled:
        log.info("Creating an Argo CD client...")
        # create a vouch client
        create_vouch_client = (f"{begin} create clients -r {realm}"
                               f" -s enabled=true -s clientId=vouch {end}")

    subproc([create_user, create_argocd_client, create_vouch_client])

    # get vouch and argocd client
    clients = f"{begin} get clients -r {realm} --fields clientId,secret {end}"
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
        k8s_obj.create_secret('argocd-external-oidc', 'argocd',
                              {'user': 'argocd',
                               'password': argocd_client_secret}, False,
                              {'app.kubernetes.io/part-of': 'argocd'})

    if vouch_enabled:
        url = (f"https://{keycloak_hostname}/realms/{realm}/protocol"
               "/openid-connect")
        configure_vouch(k8s_obj, vouch_config_dict, vouch_client_secret, url,
                        bitwarden)

    return True 
