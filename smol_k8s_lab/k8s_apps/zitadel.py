import logging as log
import json
import requests
from rich.prompt import Prompt
from .vouch import configure_vouch
from ..pretty_printing.console_logging import sub_header, header
from ..k8s_tools.kubernetes_util import create_secret
from ..k8s_tools.argocd import install_with_argocd
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
            create_secret('zitadel-admin-credentials', 'zitadel',
                          {'password': admin_password})

    install_with_argocd('zitadel', zitadel_config_dict['argo'])

    # only continue through the rest of the function if we're initializes a
    # user and vouch/argocd clients in zitadel
    if not zitadel_config_dict['init']:
        return True
    else:
        configure_zitadel(zitadel_hostname, bitwarden, vouch_config_dict)


def configure_zitadel(zitadel_hostname: str = "", bitwarden=None,
                      vouch_config_dict: dict = {}):
    """
    Sets up initial zitadel user, Argo CD client, and optional Vouch client.
    Arguments:
        bitwarden:         BwCLI obj, [optional] session to use for bitwarden
        vouch_config_dict: dict, [optional] Argo CD vouch parameters
    """

    sub_header("Configure zitadel as your OIDC SSO for Argo CD")
    api_url = f"https://{zitadel_hostname}/management/v1/"

    log.info("Creating a Zitadel user...")
    create_zitadel_user(api_url)

    # create Argo CD OIDC Application
    log.info("Creating an Argo CD application...")
    argocd_client_secret = create_zitadel_application(api_url, "argocd")

    vouch_enabled = vouch_config_dict['enabled']
    if vouch_enabled:
        # create Vouch OIDC Application
        log.info("Creating a Vouch application...")
        vouch_client_secret = create_zitadel_application(api_url, "vouch")

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
        url = f""
        configure_vouch(vouch_config_dict, vouch_client_secret, url, bitwarden)

    return True


def create_zitadel_user(api_url: str = ""):
    """
    Creates an initial user in zitadel.
    prompts a user for username, first name, last name, and email.
    Returns True
    """
    username = Prompt("What would you like your Zitadel username to be?")
    first_name = Prompt("Enter your First name for your Zitadel profile")
    last_name = Prompt("Enter your Last name for your Zitadel profile")
    email = Prompt("Enter your email for your Zitadel profile")

    # create a new user via the API
    log.info("Creating a new user...")
    payload = json.dumps({
      "userName": username,
      "profile": {
        "firstName": first_name,
        "lastName": last_name,
        "nickName": "friend",
        "displayName": f"{first_name} {last_name}",
        "preferredLanguage": "en",
        "gender": "GENDER_FEMALE"
      },
      "email": {
        "email": email,
        "isEmailVerified": True
      },
      "password": "string",
      "passwordChangeRequired": True,
    })
    headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Authorization': 'Bearer <TOKEN>'
    }

    response = requests.request("POST", api_url + 'users/human/_import',
                                headers=headers, data=payload)
    log.info(response.text)
    return True


def create_zitadel_application(api_url: str = "", app_name: str = "",
                               redirectUris: list = []):
    """
    Create an OIDC Application in Zitadel via the API.
    Arguments:
        api_url:      str, base URL of the API endpoint for zitadel
        app_name:     str, name of the applcation to create
        redirectUris: list, list of redirect Uri strings

    Returns clientSecret of application.
    """
    payload = json.dumps({
      "name": app_name,
      "redirectUris": [
        "http://localhost:4200/auth/callback"
      ],
      "responseTypes": [
        "OIDC_RESPONSE_TYPE_CODE"
      ],
      "grantTypes": [
        "OIDC_GRANT_TYPE_AUTHORIZATION_CODE"
      ],
      "appType": "OIDC_APP_TYPE_WEB",
      "authMethodType": "OIDC_AUTH_METHOD_TYPE_BASIC",
      "postLogoutRedirectUris": [
        "http://localhost:4200/signedout"
      ],
      "version": "OIDC_VERSION_1_0",
      "devMode": True,
      "accessTokenType": "OIDC_TOKEN_TYPE_BEARER",
      "accessTokenRoleAssertion": True,
      "idTokenRoleAssertion": True,
      "idTokenUserinfoAssertion": True,
      "clockSkew": "1s",
      "additionalOrigins": [
        "scheme://localhost:8080"
      ],
      "skipNativeAppSuccessPage": True
    })
    headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Authorization': 'Bearer <TOKEN>'
    }

    response = requests.request("POST",
                                api_url + 'projects/:projectId/apps/oidc',
                                headers=headers, data=payload)
    log.info(response.text)

    return response.json['clientSecret']
