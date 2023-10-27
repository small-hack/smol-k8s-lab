from base64 import standard_b64decode as b64dec
from json import loads
import logging as log
from .zitadel_api import Zitadel
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.k8s_tools.argocd_util import (install_with_argocd,
                                                wait_for_argocd_app,
                                                check_if_argocd_app_exists,
                                                sync_argocd_app)
from smol_k8s_lab.utils.passwords import create_password
from smol_k8s_lab.utils.rich_cli.console_logging import sub_header, header


def configure_zitadel(k8s_obj: K8s,
                      config_dict: dict,
                      api_tls_verify: bool = False,
                      argocd_hostname: str = "",
                      vouch_hostname: str = "",
                      bitwarden: BwCLI = None) -> dict | None:
    """
    Installs zitadel as a Argo CD Applications. If config_dict['init']['enabled']
    is True, it also configures Argo CD as OIDC Clients.

    Required Arguments:
        k8s_obj:      K8s(), kubrenetes client for creating secrets
        config_dict:  dict, Argo CD parameters for zitadel

    Optional Arguments:
        argocd_hostname:  str, the hostname of Argo CD
        vouch_hostname:   str, the hostname of vouch
        bitwarden:        BwCLI obj, [optional] contains bitwarden session

    If no init: Returns True if successful.
    If init AND vouch_hostname, returns vouch credentials
    """
    header("Setting up [green]Zitadel[/green], our identity management solution", "👥")
    secrets = config_dict['argo']['secret_keys']
    if secrets:
        zitadel_hostname = secrets['hostname']
        database_type = secrets.get('database_type', 'postgresql')

    # check to make sure the app instead already installed with Argo CD
    app_installed = check_if_argocd_app_exists('zitadel')

    if config_dict['init']['enabled'] and not app_installed:
        log.debug("Creating core key and DB credenitals for zitadel...")
        if database_type in ["postgres", "psql", "pgsql", "postgresql"]:
            db_admin_user = "postgres"
        else:
            db_admin_user = "root"

        if bitwarden:
            # create zitadel core key
            new_key = bitwarden.generate()
            core_id = bitwarden.create_login(name="zitadel-core-key",
                                             user="admin-service-account",
                                             item_url=zitadel_hostname,
                                             password=new_key)

            # create db credentials password dict
            db_password = bitwarden.generate()
            db_admin_password = bitwarden.generate()
            db_admin_user_obj = create_custom_field("adminUser", db_admin_user)
            db_admin_pass_obj = create_custom_field("adminPassword",
                                                    db_admin_password)
            db_id = bitwarden.create_login(name="zitadel-db-credentials",
                                           user="zitadel",
                                           item_url=zitadel_hostname,
                                           password=db_password,
                                           fields=[db_admin_user_obj,
                                                   db_admin_pass_obj])

            # update the zitadel values for the argocd appset
            fields = {'zitadel_core_bitwarden_id': core_id,
                      'zitadel_db_bitwarden_id': db_id}
            k8s_obj.update_secret_key(
                    'appset-secret-vars',
                    'argocd',
                    fields,
                    'secret_vars.yaml'
                    )

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
        else:
            new_key = create_password()
            secret_dict = {'masterkey': new_key}
            k8s_obj.create_secret(name="zitadel-core-key",
                                  namespace="zitadel",
                                  str_data=secret_dict)

            db_password = create_password()
            db_admin_password = create_password()
            db_secret_dict = {
                    'username': 'zitadel',
                    'password': db_password,
                    'adminUsername': db_admin_user,
                    'adminPassword': db_admin_password
                    }
            k8s_obj.create_secret(name="zitadel-db-credentials",
                                  namespace="zitadel",
                                  str_data=db_secret_dict)

    # install Zitadel using ArgoCD
    if not app_installed:
        install_with_argocd(k8s_obj, 'zitadel', config_dict['argo'])

        # only continue through the rest of the function if we're initializes a
        # user and argocd client in zitadel
        if config_dict['init']['enabled']:
            initial_user_dict = config_dict['init']['values']
            # Before initialization, we need to wait for zitadel's API to be up
            wait_for_argocd_app('zitadel')
            wait_for_argocd_app('zitadel-web-app')
            vouch_dict = initialize_zitadel(k8s_obj=k8s_obj,
                                            zitadel_hostname=zitadel_hostname,
                                            api_tls_verify=api_tls_verify,
                                            user_dict=initial_user_dict,
                                            argocd_hostname=argocd_hostname,
                                            vouch_hostname=vouch_hostname,
                                            bitwarden=bitwarden)
            return vouch_dict
    else:
        log.info("Zitadel is already installed 🎉")

        # makes sure we update the appset secret with bitwarden IDs regardless
        if bitwarden and config_dict['init']['enabled']:

            db_id = bitwarden.get_item(
                    f"zitadel-db-credentials-{zitadel_hostname}"
                    )[0]['id']

            core_id = bitwarden.get_item(
                    f"zitadel-core-key-{zitadel_hostname}"
                    )[0]['id']

            argo_oidc_item = bitwarden.get_item(
                    f"argocd-oidc-credentials-{argocd_hostname}"
                    )[0]

            argo_client_id = argo_oidc_item['login']['username']

            # update the zitadel values for the argocd appset
            fields = {
                    'zitadel_core_bitwarden_id': core_id,
                    'zitadel_db_bitwarden_id': db_id,
                    'argo_cd_oidc_issuer': f"https://{zitadel_hostname}",
                    'argo_cd_oidc_client_id': argo_client_id,
                    'argo_cd_oidc_logout_url': f"https://{zitadel_hostname}/oidc/v1/end_session",
                    'argo_cd_oidc_bitwarden_id': argo_oidc_item['id']
                    }

            k8s_obj.update_secret_key(
                    'appset-secret-vars',
                    'argocd',
                    fields,
                    'secret_vars.yaml'
                    )

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

            sync_argocd_app('zitadel')
            sync_argocd_app('argo-cd')


def initialize_zitadel(k8s_obj: K8s,
                       zitadel_hostname: str,
                       api_tls_verify: bool = False,
                       user_dict: dict = {},
                       argocd_hostname: str = "",
                       vouch_hostname: str = "",
                       bitwarden: BwCLI = None) -> Zitadel:
    """
    Sets up initial zitadel user, Argo CD client
    Arguments:
      k8s_obj:           K8s(), kubrenetes client for creating secrets
      zitadel_hostname:  str, the hostname of Zitadel
      api_tls_verify:    bool, whether or not to verify the TLS cert on request to api
      user_dict:         dict of initial username, email, first name, last name, gender
      argocd_hostname:   str, the hostname of Argo CD
      vouch_hostname:    str, the hostname to use for vouch
      bitwarden:         BwCLI obj, [optional] session to use for bitwarden

    returns zitadel object
    """

    sub_header("Configuring zitadel as your OIDC SSO for Argo CD")

    # get the zitadel service account private key json for generating a jwt
    adm_secret = k8s_obj.get_secret('zitadel-admin-sa', 'zitadel')
    adm_secret_file = adm_secret['data']['zitadel-admin-sa.json']
    private_key_obj = loads(b64dec(str.encode(adm_secret_file)).decode('utf8'))
    # setup the zitadel python api wrapper
    zitadel =  Zitadel(zitadel_hostname, private_key_obj, api_tls_verify)

    # create our first project
    zitadel.create_project()

    log.info("Creating a groups Zitadel Action (sends group info to Argo CD)")
    zitadel.create_action("groupsClaim")

    # create Argo CD OIDC Application
    log.info("Creating an Argo CD application...")
    redirect_uris = f"https://{argocd_hostname}/auth/callback"
    logout_uris = [f"https://{argocd_hostname}"]
    argocd_client = zitadel.create_application("argocd",
                                               redirect_uris,
                                               logout_uris)

    # create roles for both Argo CD Admins and regular users
    zitadel.create_role("argocd_administrators", "Argo CD Administrators",
                        "argocd_administrators")
    zitadel.create_role("argocd_users", "Argo CD Users", "argocd_users")

    # fields for updating the appset secret
    fields = {
            'argo_cd_oidc_issuer': f"https://{zitadel_hostname}",
            'argo_cd_oidc_client_id': argocd_client['client_id'],
            'argo_cd_oidc_logout_url': f"https://{zitadel_hostname}/oidc/v1/end_session"
            }

    # if bitwarden is enabled, we store the argocd odic secret there
    if bitwarden:
        sub_header("Creating OIDC secret for Argo CD in Bitwarden")
        id = bitwarden.create_login(name='argocd-oidc-credentials',
                                    item_url=argocd_hostname,
                                    user=argocd_client['client_id'],
                                    password=argocd_client['client_secret'])
        fields['argo_cd_oidc_bitwarden_id'] = id
    else:
        # the argocd secret needs labels.app.kubernetes.io/part-of: "argocd"
        k8s_obj.create_secret('argocd-oidc-credentials',
                              'argocd',
                              {'user': 'argocd',
                               'password': argocd_client['client_secret']},
                              labels={'app.kubernetes.io/part-of': 'argocd'})

    # update appset-secret-vars secret with issuer, client_id, logout_url
    k8s_obj.update_secret_key('appset-secret-vars',
                              'argocd',
                              fields,
                              'secret_vars.yaml')
    k8s_obj.reload_deployment('argocd-appset-secret-plugin', 'argocd')

    # create zitadel admin user and grants now that the clients are setup
    header("Creating a Zitadel user...")
    user_id = zitadel.create_user(bitwarden=bitwarden, **user_dict)
    roles_for_user_grant = ['argocd_administrators']

    if vouch_hostname:
        # create Vouch OIDC Application
        log.info("Creating a Vouch application...")
        redirect_uris = f"https://{vouch_hostname}/auth"
        logout_uris = [f"https://{vouch_hostname}"]
        vouch_dict = zitadel.create_application("vouch", redirect_uris, logout_uris)
        zitadel.create_role("vouch_users", "Vouch Users", "vouch_users")
        roles_for_user_grant.append('vouch_users')

    zitadel.create_user_grant(user_id, roles_for_user_grant)

    # grant admin access to first user
    sub_header("creating user IAM membership with IAM_OWNER")
    zitadel.create_iam_membership(user_id, 'IAM_OWNER')

    if vouch_hostname:
        return vouch_dict
    else:
        return True
