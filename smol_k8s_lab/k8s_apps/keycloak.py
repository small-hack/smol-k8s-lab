import logging as log
import json
from rich.prompt import Prompt
from ..pretty_printing.console_logging import sub_header, header
from ..k8s_tools.k8s_lib import K8s
from ..k8s_tools.argocd_util import install_with_argocd
from ..subproc import subproc
from ..utils.bw_cli import BwCLI
from ..utils.passwords import create_password


def configure_keycloak(k8s_obj: K8s,
                       keycloak_config_dict: dict = {},
                       bitwarden: BwCLI = None) -> True:
    """
    Installs Keycloak as an Argo CD Application. If keycloak_config_dict['init']
    is True, it also configures Argo CD as OIDC Client.

    Required Arguments:
        K8s: K8s() class instance so we can create secrets and install with
             argo using a direct connection to the cluster
        keycloak_config_dict: dict, Argo CD parameters for keycloak

    Optional Arguments:
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
    # user and argocd client in keycloak
    if keycloak_config_dict['init']:
        realm = secrets['default_realm']
        initialize_keycloak(k8s_obj, realm, keycloak_hostname, bitwarden)
    # always return True
    return True


def initialize_keycloak(k8s_obj: K8s,
                        realm: str = "",
                        keycloak_hostname: str = "",
                        bitwarden=None) -> True:
    """
    Sets up initial Keycloak user, Argo CD client.
    Arguments:
        realm:             str, name of the keycloak realm to use
        bitwarden:         BwCLI obj, [optional] session to use for bitwarden
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

    subproc([create_user, create_argocd_client])

    # get argocd client
    clients = f"{begin} get clients -r {realm} --fields clientId,secret --query argocd {end}"
    argocd_client_secret = json.loads(subproc([clients]))['secret']

    if bitwarden:
        sub_header("Creating OIDC secret for Argo CD OIDC in Bitwarden")
        bitwarden.create_login(name='argocd-external-oidc',
                               user='argocd',
                               password=argocd_client_secret)
    else:
        # the argocd secret needs labels.app.kubernetes.io/part-of: "argocd"
        k8s_obj.create_secret('argocd-external-oidc', 'argocd',
                              {'user': 'argocd',
                               'password': argocd_client_secret}, False,
                              {'app.kubernetes.io/part-of': 'argocd'})

    return True 
