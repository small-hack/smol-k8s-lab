from json import loads
import logging as log
from rich.prompt import Prompt
from ..k8s_apps.keycloak import Keycloak
from ..k8s_apps.zitadel_api import Zitadel
from ..k8s_tools.argocd_util import install_with_argocd
from ..k8s_tools.k8s_lib import K8s
from ..pretty_printing.console_logging import header
from ..utils.bw_cli import BwCLI, create_custom_field
from ..subproc import subproc


def configure_vouch(k8s_obj: K8s,
                    vouch_config_dict: dict = {},
                    oidc_provider_name: str = "",
                    oidc_provider_hostname: str = "",
                    bitwarden: BwCLI = None,
                    realm: str = "",
                    zitadel: Zitadel = None) -> bool:
    """
    Installs vouch-proxy as an Argo CD application on Kubernetes

    Takes Args:
      k8s_obj:                K8s(), for the authenticated k8s client
      vouch_config_dict:      Argo CD parameters
      oidc_provider_name:     OIDC provider name. options: keycloak, zitadel
      oidc_provider_hostname: OIDC provider hostname e.g. zitadel.example.com
      bitwarden:              BwCLI, to store k8s secrets in bitwarden
      realm:                  keycloak realm to use
      zitadel:                Zitadel object so we don't have to create an api token

    returns True if successful
    """
    header("🗝️ Vouch Setup")

    if vouch_config_dict['init']:
        secrets = vouch_config_dict['argo']['secret_keys']
        vouch_hostname = secrets['hostname']
        base_url, client_id, client_secret = create_vouch_app(vouch_hostname,
                                                              oidc_provider_name,
                                                              oidc_provider_hostname,
                                                              realm,
                                                              zitadel)

        vouch_callback_url = f'https://{vouch_hostname}/auth'
        m = ("[green]Please enter a comma seperated list of [yellow]emails[/] that"
             " are allowed to access domains behind Vouch")
        emails = Prompt.ask(m)
        m = ("[green]Please enter a comma seperated list of [yellow]domains[/] that"
             " are allowed to use Vouch")
        domains = Prompt.ask(m)

        # if using bitwarden, put the secret in bitarden and ESO will grab it
        if bitwarden:
            auth_url = create_custom_field("authUrl", f'{base_url}auth')
            token_url = create_custom_field("tokenUrl", f'{base_url}token')
            user_info_url = create_custom_field("userInfoUrl", f'{base_url}userinfo')
            callback_urls = create_custom_field("callbackUrls", vouch_callback_url)
            # create oauth OIDC bitwarden item
            bitwarden.create_login(name='vouch-oauth-config',
                                   user=client_id,
                                   password=client_secret,
                                   fields=[auth_url,
                                           token_url,
                                           user_info_url,
                                           callback_urls])

            domains_obj = create_custom_field("domains", domains)
            emails_obj = create_custom_field("allowList", emails)
            # create vouch config bitwarden item
            bitwarden.create_login(name='vouch-config',
                                   user='vouch',
                                   password='none',
                                   fields=[domains_obj, emails_obj])
        # create vouch k8s secrets if we're not using bitwarden
        else:
            # create oauth OIDC k8s secret
            k8s_obj.create_secret('vouch-oauth-config', 'vouch',
                                  {'user': client_id,
                                   'password': client_secret,
                                   'authUrl': f'{base_url}/auth',
                                   'tokenUrl': f'{base_url}/token',
                                   'userInfoUrl': f'{base_url}/userinfo',
                                   'callbackUrls': vouch_callback_url})

            # create vouch config k8s secret
            k8s_obj.create_secret('vouch-config', 'vouch',
                                  {'domains': domains, 'allowList': emails})

    install_with_argocd(k8s_obj, 'vouch', vouch_config_dict['argo'])
    return True


def create_vouch_app(vouch_hostname: str = "",
                     provider: str = 'zitadel',
                     provider_hostname: str = "",
                     realm: str = "default",
                     zitadel: Zitadel = None) -> list:
    """
    creates a vouch OIDC application in either keycloak or zitadel
    """
    if provider == 'zitadel':
        # create Vouch OIDC Application
        log.info("Creating a Vouch application...")
        redirect_uris = [f"https://{vouch_hostname}/auth/callback"]
        logout_uris = [f"https://{vouch_hostname}"]
        vouch_client_creds = zitadel.create_application("vouch",
                                                        redirect_uris,
                                                        logout_uris)
        client_id = vouch_client_creds['client_id']
        client_secret = vouch_client_creds['client_secret']
        url = f"https://{provider_hostname}/"

    elif provider == 'keycloak':
        keycloak = Keycloak()
        # create a vouch client
        client_secret = keycloak.create_client('vouch')
        url = f"https://{provider_hostname}/realms/{realm}/protocol/openid-connect"
    else:
        log.error("niether zitadel nor keycloak was passed into "
                  "create_vouch_app, got {provider} instead.")

    return url, client_id, client_secret
