import logging as log
import json
from rich.prompt import Prompt
from smol_k8s_lab.bitwarden.bw_cli import BwCLI
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.k8s_tools.argocd_util import install_with_argocd
from smol_k8s_lab.utils.subproc import subproc
from smol_k8s_lab.utils.passwords import create_password
from smol_k8s_lab.utils.rich_cli.console_logging import sub_header, header


class Keycloak():
    """
    Python Wrapper for the keycloak cli
    """
    def __init__(self, realm: str = "default"):
        """
        Mostly for storing the beginning and end of the keycloak cli command 🤦
        """
        log.debug("Initializing keycloak cli object")
        self.realm = realm
        self.exec_path = ("kubectl exec -n keycloak keycloak-web-app-0 -- "
                          "/opt/bitnami/keycloak/bin/kcadm.sh ")
        self.cfg = (f" -o --no-config --server http://localhost:8080/ --realm {realm}"
                    "--user KEYCLOAK_ADMIN --password $KEYCLOAK_ADMIN_PASSWORD")

    def create_user(self, username: str, first_name: str, last_name: str) -> None:
        """ 
        creates a user via the keycloak cli
        """
        log.info(f"Creating a new user for {username}")
        # create a new user
        cmd = (f"create users -r {self.realm} -s username={username} -s enabled=true "
               f"-s firstName={first_name} -s lastName={last_name}")
        subproc([self.exec_path + cmd + self.cfg])

    def create_client(self, clientId: str) -> str:
        """
        creates an OIDC client with clientId str as the ID and returns the ClientSecret
        """
        log.info(f"Creating an {clientId} client...")
        cmd = f"create clients -r {self.realm} -s enabled=true -s clientId={clientId}"
        subproc([self.exec_path + cmd + self.cfg])

        # get client and return the client secret
        cmd = f"get clients -r {self.realm} --fields clientId,secret --query {clientId}"
        return json.loads(subproc([self.exec_path + cmd + self.cfg]))['secret']


def configure_keycloak(k8s_obj: K8s,
                       config_dict: dict,
                       bitwarden: BwCLI = None) -> True:
    """
    Installs Keycloak as an Argo CD Application. If config_dict['init']['enabled']
    is True, it also configures Argo CD as OIDC Client.

    Required Arguments:
        K8s: K8s() class instance so we can create secrets and install with
             argo using a direct connection to the cluster
        config_dict: dict, Argo CD parameters for keycloak

    Optional Arguments:
        bitwarden:         BwCLI obj, [optional] contains bitwarden session

    Returns True if successful.
    """
    header("🗝️Keycloak Setup")

    # if we're using bitwarden, create the secrets in bitwarden before
    # creating Argo CD app
    if config_dict['init']['enabled']:
        secrets = config_dict['argo']['secret_keys']
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

    install_with_argocd(k8s_obj, 'keycloak', config_dict['argo'])

    # only continue through the rest of the function if we're initializes a
    # user and argocd client in keycloak
    if config_dict['init']['enabled']:
        realm = secrets['default_realm']
        initialize_keycloak(k8s_obj, realm, config_dict['init']['values'], bitwarden)
    # always return True
    return True


def initialize_keycloak(k8s_obj: K8s,
                        realm: str,
                        initial_user_dict: dict = {"username": "",
                                                   "first_name": "",
                                                   "last_name": ""},
                        bitwarden=None) -> True:
    """
    Sets up initial Keycloak user, Argo CD client.
    Arguments:
      k8s_obj:           K8s object to use for creating initial secrets
      realm:             name of the keycloak realm to use
      initial_user_dict: initial user dict with username, first_name, last_name
      bitwarden:         BwCLI obj, [optional] session to use for bitwarden
    """
    sub_header("Configuring Keycloak as your OIDC SSO for Argo CD")
    username = initial_user_dict['username']
    if not username:
        username = Prompt("What would you like your Keycloak username to be?")
    first_name = initial_user_dict['first_name']
    if not first_name:
        first_name = Prompt("Enter your First name for your keycloak profile")
    last_name = initial_user_dict['last_name']
    if not last_name:
        last_name = Prompt("Enter your Last name for your keycloak profile")

    # create keycloak object
    keycloak = Keycloak(realm)

    # create initial user
    keycloak.create_user(username, first_name, last_name)

    # create intial client for 
    argocd_client_secret = keycloak.create_client("argocd")


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
