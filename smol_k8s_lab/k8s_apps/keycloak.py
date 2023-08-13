import logging as log
from rich.prompt import Prompt
from ..utils.bw_cli import BwCLI
from ..subproc import subproc
from ..k8s_tools.argocd import install_with_argocd
from ..console_logging import sub_header, header


def configure_keycloak(keycloak_config_dict: dict, init: bool = True,
                       bitwarden=None):
    """
    installs Keycloak as an Argo CD application.
    Takes keycloak_config_dict: dict, Argo CD parameters
          init: boolean, if we should do init scripts
          bitwarden: BWCLI object, should we store k8s secrets in bitwarden

    If init = True, we return the following dicts:
        argocd_client_credentials, vouch_client_credentials
    """
    header("🗝️Keycloak Setup")

    secrets = keycloak_config_dict['secrets']
    if bitwarden:
        admin_password = bitwarden.generate()
        postgres_password = bitwarden.generate()

    install_with_argocd('keycloak', keycloak_config_dict['argo'])

    if not init:
        # only continue through the rest of the function if we're initializes a
        # user and vouch/argocd clients in keycloak
        return True

    sub_header("Configure Keycloak as your OIDC SSO for Argo CD")
    username = Prompt("What would you like your Keycloak username to be?")
    first_name = Prompt("Enter your First name for your keycloak profile")
    last_name = Prompt("Enter your Last name for your keycloak profile")
    realm = keycloak_config_dict['argo']['secret_keys']['default_realm']

    c = "kubectl exec -n keycloak keycloak-web-app-0 -- /opt/bitnami/keycloak"
    end = (f"-o --no-config --server http://localhost:8080/ --realm {realm}"
           "--user KEYCLOAK_ADMIN --password $KEYCLOAK_ADMIN_PASSWORD")

    log.info("Creating a new user...")

    # create a new user
    create_user = (f"{c} create users -r {realm} -s username={username} -s "
                   f"enabled=true -s firstName={first_name} "
                   f"-s lastName={last_name} {end}")

    # create an argocd client
    create_argocd_client = (f"{c} create clients -r {realm} -s enabled=true -s"
                            f"clientId=argocd {end}")

    # create an vouch client
    create_vouch_client = (f"{c} create clients -r {realm} -s enabled=true -s "
                           f"clientId=vouch {end}")

    subproc([create_user, create_argocd_client, create_vouch_client])

    # get vouch and argocd client
    clients = f"{c} get clients -r {realm} --fields id,clientId,secret {end}"
    client_json = json.loads(subproc([clients]))

    for client in client_json:
        if client_json['clientId'] == argocd:
            argocd_client_secret = client_json['secret']
        if client_json['clientId'] == vouch:
            vouch_client_credentials = client_json['secret']

    vouch_client_credentials = {'vouch': vouch_client_secret}
    argocd_client_credentials = {'argocd': argocd_client_secret}

    return argocd_client_secret, vouch_client_credentials
