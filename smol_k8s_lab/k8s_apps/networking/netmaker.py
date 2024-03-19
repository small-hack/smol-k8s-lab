import logging as log
from rich.prompt import Prompt
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_apps.identity_provider.zitadel_api import Zitadel
from smol_k8s_lab.k8s_tools.argocd_util import (install_with_argocd,
                                                check_if_argocd_app_exists,
                                                update_argocd_appset_secret)
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.utils.rich_cli.console_logging import header
from smol_k8s_lab.utils.passwords import create_password
from .keycloak import Keycloak


def configure_netmaker(k8s_obj: K8s,
                    netmaker_config_dict: dict,
                    oidc_provider_name: str = "",
                    oidc_provider_hostname: str = "",
                    bitwarden: BwCLI = None,
                    users: list = [],
                    realm: str = "",
                    zitadel: Zitadel = None) -> None:
    """
    Installs netmaler as an Argo CD application on Kubernetes

    Required Args:
      k8s_obj:                K8s(), for the authenticated k8s client
      vouch_config_dict:      Argo CD parameters

    Optional Args:
      oidc_provider_name:     OIDC provider name. options: keycloak, zitadel
      oidc_provider_hostname: OIDC provider hostname e.g. zitadel.example.com
      bitwarden:              BwCLI, to store k8s secrets in bitwarden
      users:                  list of user to give access to vouch app
      realm:                  str keycloak realm to use
      zitadel:                Zitadel api object 
    """
    header("Setting up [green]Netmaker[/] to create VPNs", "🗝️")

    # make sure netmaker isn't already installed
    app_installed = check_if_argocd_app_exists("netmaker")
    # this handles the netmaker-oauth-config secret data
    secrets = netmaker_config_dict['argo']['secret_keys']
    if secrets:
        netmaker_hostname = secrets['hostname']

    if netmaker_config_dict['init']['enabled'] and not app_installed:
        auth_dict = create_netmaker_app(provider=oidc_provider_name,
                                     provider_hostname=oidc_provider_hostname,
                                     netmaker_hostname=netmaker_hostname,
                                     users=users,
                                     zitadel=zitadel,
                                     realm=realm)

        # if using bitwarden, put the secret in bitarden and ESO will grab it
        if bitwarden:
            fields = [
                create_custom_field("authUrl", auth_dict['auth_url']),
                create_custom_field("tokenUrl", auth_dict['token_url']),
                create_custom_field("userInfoUrl", auth_dict['user_info_url']),
                create_custom_field("endSessionEndpoint", auth_dict['end_session_url'])
                ]

            log.info(f"vouch oauth fields are {fields}")

            # create oauth OIDC bitwarden item
            oauth_id = bitwarden.create_login(
                name='netmaler-oauth-config',
                user=auth_dict['client_id'],
                item_url=netmaker_hostname,
                password=auth_dict['client_secret'],
                fields=fields
                )

            # create netmaker config bitwarden item
            vouch_id = bitwarden.create_login(
                    name='netmaker-config',
                    user='netmaker',
                    password='none'
                    )

            # update the netmaker values for the argocd appset
            update_argocd_appset_secret(
                    k8s_obj,
                    {'netmaker_oauth_config_bitwarden_id': oauth_id,
                     'netmaker_config_bitwarden_id': vouch_id}
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

        # create vouch k8s secrets if we're not using bitwarden
        else:
            # create oauth OIDC k8s secret
            k8s_obj.create_secret('vouch-oauth-config',
                                  'vouch',
                                  {'user': auth_dict['client_id'],
                                   'password': auth_dict['client_secret'],
                                   'authUrl': auth_dict['auth_url'],
                                   'tokenUrl': auth_dict['token_url'],
                                   'userInfoUrl': auth_dict['user_info_url'],
                                   'endSessionEndpoint': auth_dict['end_session_url']}
                                   )

    if not app_installed:
        install_with_argocd(k8s_obj, 'netmaker', netmaker_config_dict['argo'])
    else:
        log.info("netmaker already installed 🎉")

        # we need to still update the bitwarden IDs if bitwarden and init is enabled
        if netmaker_config_dict['init']['enabled'] and bitwarden:
            log.debug("Updating vouch bitwarden IDs in the appset secret")
            oauth_id = bitwarden.get_item(
                    f"netmaker-oauth-config-{netmaker_hostname}"
                    )[0]['id']

            netmaker_id = bitwarden.get_item(
                    f"netmaker-config-{netmaker_hostname}"
                    )[0]['id']

            # update the netmaker values for the argocd appset
            update_argocd_appset_secret(
                    k8s_obj,
                    {'netmaker_oauth_config_bitwarden_id': oauth_id,
                     'netmaker_config_bitwarden_id': vouch_id}
                   )


def create_netmaker_app(provider: str,
                     provider_hostname: str,
                     netmaker_hostname: str = "",
                     users: list = [],
                     zitadel: Zitadel = None,
                     realm: str = "default") -> list:
    """
    Creates an OIDC application, for netmaker, in either Keycloak or Zitadel

    Arguments:
      provider          - either 'keycloak' or 'zitadel'
      provider_hostname - hostname of keycloak or zitadel
      netmaker_hostname - hostname of netmaker
      zitadel           - Zitadel api object 
      realm             - realm to use for keycloak if using keycloak

    returns [url, client_id, client_secret]
    """
    # create Vouch OIDC Application
    if provider == 'zitadel':
        log.info("Creating an OIDC application for Netmaker via Zitadel...")
        netmaker_dict = zitadel.create_application(
                "netmaker", 
                f"https://{netmaker_hostname}/auth",
                [f"https://{netmaker_hostname}"]
                )
        zitadel.create_role("netmaker_users", "Netmaker Users", "netmaker_users")
        zitadel.update_user_grant(['netmaker_users'])

        client_id = netmaker_dict['client_id']
        client_secret = netmaker_dict['client_secret']
        auth_url = f'https://{provider_hostname}/oauth/v2/authorize'
        token_url = f'https://{provider_hostname}/oauth/v2/token'
        user_info_url = f'https://{provider_hostname}/oidc/v1/userinfo'
        end_session_url = f'https://{provider_hostname}/oidc/v1/end_session'

    elif provider == 'keycloak':
        keycloak = Keycloak()
        # create a vouch client
        client_secret = keycloak.create_client('netmaker')
        client_id = 'netmaker'
        url = f"https://{provider_hostname}/realms/{realm}/protocol/openid-connect"
        auth_url = f'{url}/auth'
        token_url = f'{url}/token'
        user_info_url = f'{url}/userinfo'
        end_session_url = f'{url}/end_session'
    else:
        log.error("niether zitadel nor keycloak was passed into create_vouch_app,"
                  f" got {provider} instead.")

    auth_dict = {"auth_url": auth_url,
                 "token_url": token_url,
                 "user_info_url": user_info_url,
                 "end_session_url": end_session_url,
                 "client_id": client_id,
                 "client_secret": client_secret}
    return auth_dict
