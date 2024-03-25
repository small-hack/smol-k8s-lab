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


def configure_netmaker(k8s_obj: K8s,
                    netmaker_config_dict: dict,
                    oidc_provider_name: str = "",
                    oidc_provider_hostname: str = "",
                    bitwarden: BwCLI = None,
                    zitadel: Zitadel = None) -> None:
    """
    Installs netmaker as an Argo CD application on Kubernetes

    Required Args:
      k8s_obj:                K8s(), for the authenticated k8s client
      netmaker_config_dict:      Argo CD parameters

    Optional Args:
      oidc_provider_name:     OIDC provider name. options: keycloak, zitadel
      oidc_provider_hostname: OIDC provider hostname e.g. zitadel.example.com
      bitwarden:              BwCLI, to store k8s secrets in bitwarden
      zitadel:                Zitadel api object 
    """
    header("Setting up [green]Netmaker[/] to create VPNs", "🗝️")

    # make sure netmaker isn't already installed
    app_installed = check_if_argocd_app_exists("netmaker")
    # this handles the netmaker-oauth-config secret data
    secrets = netmaker_config_dict['argo']['secret_keys']
    if secrets:
        netmaker_hostname = secrets['hostname']
        frontendUrl = secrets['admin_pannel_url']
        serverHttpHost = secrets['api_endpoint_url']
        auth_provider = secrets['auth_provider']
        serverBrokerEndpoint = secrets['broker_endpoint_url']

    if netmaker_config_dict['init']['enabled'] and not app_installed:
        auth_dict = create_netmaker_app(provider=oidc_provider_name,
                                     provider_hostname=oidc_provider_hostname,
                                     netmaker_hostname=netmaker_hostname,
                                     users=netmaker_config_dict['init']['values']['user'],
                                     zitadel=zitadel,
                                     realm=netmaker_config_dict['init']['values'].get('realm', ""))

        # if using bitwarden, put the secret in bitarden and ESO will grab it
        if bitwarden:
            fields = [
                create_custom_field("authUrl", auth_dict['auth_url']),
                create_custom_field("tokenUrl", auth_dict['token_url']),
                create_custom_field("userInfoUrl", auth_dict['user_info_url']),
                create_custom_field("endSessionEndpoint", auth_dict['end_session_url']),
                create_custom_field("frontendUrl", frontendUrl),
                create_custom_field("serverHttpHost", serverHttpHost),
                create_custom_field("auth_provider", auth_provider),
                create_custom_field("serverBrokerEndpoint", serverBrokerEndpoint)
                ]

            log.info(f"netmaker oauth fields are {fields}")
            
            # generate postgres credentials
            postgresPassword = create_password()
            sqlPass = create_password()
            mqPass = create_password()
            
            postgres_fields = [
                create_custom_field("postgres_password", postgresPassword),
                create_custom_field("SQL_PASS", sqlPass),
                create_custom_field("MQ_ADMIN_PASSWORD", mqPass)
                ]
            
            log.info(f"netmaker postgres fields are {postgres_fields}")

            # create oauth OIDC bitwarden item
            oauth_id = bitwarden.create_login(
                name='netmaker-oauth-config',
                user=auth_dict['client_id'],
                item_url=netmaker_hostname,
                password=auth_dict['client_secret'],
                fields=fields
                )
            
            # create the postgres bitwarden item
            postgres_id = bitwarden.create_login(
                    name=f"netmaker-pgsql-credentials",
                    fields=postgres_fields
                    )

            # update the netmaker values for the argocd appset
            update_argocd_appset_secret(
                    k8s_obj,
                    {'netmaker_oauth_config_bitwarden_id': oauth_id})

            # update the postgres values for the argocd appset secret
            update_argocd_appset_secret(
                    k8s_obj,
                    {'netmaker_pgsql_config_bitwarden_id': postgres_id})

            # reload the bitwarden ESO provider
            try:
                k8s_obj.reload_deployment('bitwarden-eso-provider', 'external-secrets')
            except Exception as e:
                log.error(
                        "Couldn't scale down the [magenta]bitwarden-eso-provider[/]"
                        "deployment in [green]external-secrets[/] namespace. Recieved: "
                        f"{e}"
                        )

        # create netmaker k8s secrets if we're not using bitwarden
        else:
            # create oauth OIDC k8s secret
            k8s_obj.create_secret('netmaker-oauth-config',
                                  'netmaker',
                                  {'user': auth_dict['client_id'],
                                   'password': auth_dict['client_secret'],
                                   'authUrl': auth_dict['auth_url'],
                                   'tokenUrl': auth_dict['token_url'],
                                   'userInfoUrl': auth_dict['user_info_url'],
                                   'endSessionEndpoint': auth_dict['end_session_url'],
                                   'frontendUrl': frontendUrl,
                                   'serverHttpHost': serverHttpHost,
                                   'auth_provider': auth_provider,
                                   'serverBrokerEndpoint': serverBrokerEndpoint}
                                   )

            # create postgres k8s secret
            k8s_obj.create_secret('netmaker-pgsql-credentials',
                                  'netmaker',
                                  {'postgres_password': postgresPassword,
                                   'SQL_PASS': sqlPass,
                                   'MQ_ADMIN_PASSWORD': mqPass}
                                   )

    if not app_installed:
        install_with_argocd(k8s_obj, 'netmaker', netmaker_config_dict['argo'])
    else:
        log.info("netmaker already installed 🎉")

        # we need to still update the bitwarden IDs if bitwarden and init is enabled
        if netmaker_config_dict['init']['enabled'] and bitwarden:
            log.debug("Updating netmaker-oath-config bitwarden ID in the appset secret")
            oauth_id = bitwarden.get_item(
                    f"netmaker-oauth-config-{netmaker_hostname}"
                    )[0]['id']

            log.debug("Updating netmaker-pqsql-credentials bitwarden ID in the appset secret")
            postgres_id = bitwarden.get_item(
                    f"netmaker-pgsql-credentials"
                    )[0]['id']

            # update the netmaker values for the argocd appset
            update_argocd_appset_secret(
                    k8s_obj,
                    {'netmaker_oauth_config_bitwarden_id': oauth_id})

            update_argocd_appset_secret(
                    k8s_obj,
                    {'netmaker_pgsql_config_bitwarden_id': postgres_id})

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
    # create Netmaker OIDC Application
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
    else:
        log.error("zitadel not passed into create_netmaker_app,"
                  f" got {provider} instead.")

    auth_dict = {"auth_url": auth_url,
                 "token_url": token_url,
                 "user_info_url": user_info_url,
                 "end_session_url": end_session_url,
                 "client_id": client_id,
                 "client_secret": client_secret}
    return auth_dict
