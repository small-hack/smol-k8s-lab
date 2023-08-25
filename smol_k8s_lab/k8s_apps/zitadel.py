from base64 import standard_b64decode as b64dec
from json import loads
import logging as log
from .zitadel_api import Zitadel
from ..pretty_printing.console_logging import sub_header, header
from ..k8s_tools.kubernetes_util import update_secret_key
from ..k8s_tools.k8s_lib import K8s
from ..k8s_tools.argocd_util import install_with_argocd, wait_for_argocd_app
from ..utils.bw_cli import BwCLI, create_custom_field
from ..utils.passwords import create_password


def configure_zitadel(k8s_obj: K8s,
                      config_dict: dict = {},
                      argocd_hostname: str = "",
                      bitwarden: BwCLI = None):
    """
    Installs zitadel as a Argo CD Applications. If config_dict['init']['enabled']
    is True, it also configures Argo CD as OIDC Clients.

    Required Arguments:
        k8s_obj:      K8s(), kubrenetes client for creating secrets
        config_dict:  dict, Argo CD parameters for zitadel

    Optional Arguments:
        argocd_hostname:  str, the hostname of Argo CD
        bitwarden:        BwCLI obj, [optional] contains bitwarden session

    Returns True if successful.
    """
    header("🔑 Zitadel Setup")
    zitadel_domain = config_dict['argo']['secret_keys']['hostname']
    database_type = config_dict['argo']['secret_keys']['database_type']

    if config_dict['init']['enabled']:
        log.debug("Creating core key and DB credenitals for zitadel...")
        if database_type in ["postgres", "psql", "pgsql", "postgresql"]:
            admin_user = "postgres"
        else:
            admin_user = "root"
        if bitwarden:
            # create zitadel core key
            new_key = bitwarden.generate()
            bitwarden.create_login(name="zitadel-core-key",
                                   user="admin-service-account",
                                   item_url=zitadel_domain,
                                   password=new_key)

            # create db credentials password dict
            password = bitwarden.generate()
            admin_password = bitwarden.generate()
            admin_user_obj = create_custom_field("adminUser", admin_user)
            admin_pass_obj = create_custom_field("adminPassword", admin_password)
            bitwarden.create_login(name="zitadel-db-credentials",
                                   user="zitadel",
                                   item_url=zitadel_domain,
                                   password=password,
                                   fields=[admin_user_obj, admin_pass_obj])
        else:
            new_key = create_password()
            secret_dict = {'masterkey': new_key}
            k8s_obj.create_secret(name="zitadel-core-key",
                                  namespace="zitadel",
                                  str_data=secret_dict)

            password = create_password()
            admin_password = create_password()
            secret_dict = {'username': 'zitadel',
                           'password': password,
                           'adminUsername': admin_user,
                           'adminPassword': admin_password}
            k8s_obj.create_secret(name="zitadel-db-credentials",
                                  namespace="zitadel",
                                  str_data=secret_dict)

    # install Zitadel using ArgoCD
    install_with_argocd(k8s_obj, 'zitadel', config_dict['argo'])

    # only continue through the rest of the function if we're initializes a
    # user and argocd client in zitadel
    if not config_dict['init']['enabled']:
        return True
    else:
        initial_user_dict = config_dict['init']['values']
        # Before initialization, we need to wait for zitadel's API to be up
        wait_for_argocd_app('zitadel')
        wait_for_argocd_app('zitadel-web-app')
        initialize_zitadel(k8s_obj, zitadel_domain, initial_user_dict,
                           argocd_hostname, bitwarden)


def initialize_zitadel(k8s_obj: K8s,
                       zitadel_hostname: str,
                       user_dict: dict = {},
                       argocd_hostname: str = "",
                       bitwarden: BwCLI = None) -> Zitadel:
    """
    Sets up initial zitadel user, Argo CD client
    Arguments:
      zitadel_hostname:  str, the hostname of Zitadel
      user_dict:         dict of initial username, email, first name, last name, gender
      argocd_hostname:   str, the hostname of Argo CD
      k8s_obj:           K8s(), kubrenetes client for creating secrets
      bitwarden:         BwCLI obj, [optional] session to use for bitwarden

    returns zitadel object
    """

    sub_header("Configuring zitadel as your OIDC SSO for Argo CD")

    # get the zitadel service account private key json for generating a jwt
    adm_secret = k8s_obj.get_secret('zitadel-admin-sa', 'zitadel')
    adm_secret_file = adm_secret['data']['zitadel-admin-sa.json']
    private_key_obj = loads(b64dec(str.encode(adm_secret_file)).decode('utf8'))
    # setup the zitadel python api wrapper
    zitadel =  Zitadel(zitadel_hostname, private_key_obj)

    # create our first project
    zitadel.create_project()

    log.info("Creating a groups Zitadel Action (sends group info to Argo CD)")
    zitadel.create_action("groupsClaim")

    # create Argo CD OIDC Application
    log.info("Creating an Argo CD application...")
    redirect_uris = [f"https://{argocd_hostname}/auth/callback"]
    logout_uris = [f"https://{argocd_hostname}"]
    argocd_client = zitadel.create_application("argocd",
                                               redirect_uris,
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
    k8s_obj.reload_deployment('argocd-appset-secret-plugin', 'argocd')

    if bitwarden:
        sub_header("Creating OIDC secret for Argo CD in Bitwarden")
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
    user_id = zitadel.create_user(bitwarden=bitwarden, **user_dict)
    zitadel.create_user_grant(user_id, 'argocd_administrators')

    return zitadel
