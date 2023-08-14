import logging as log
from rich.prompt import Confirm, Prompt
from ..pretty_printing.console_logging import header
from ..k8s_tools.kubernetes_util import create_secret
from ..k8s_tools.argocd import install_with_argocd
from ..subproc import subproc
from ..utils.bw_cli import BwCLI
from ..utils.passwords import create_password


def configure_vouch(vouch_config_dict: dict,
                    vouch_client_secret: str = "",
                    base_url: str = "",
                    bitwarden=None):
    """
    Installs vouch-proxy as an Argo CD application on Kubernetes

    Takes vouch_config_dict: dict, Argo CD parameters
          bitwarden: BWCLI object, to store k8s secrets in bitwarden

    returns True if successful
    """
    header("🗝️vouch Setup")

    if vouch_config_dict['init']:
        secrets = vouch_config_dict['secrets']
        vouch_hostname = secrets['vouch_hostname']

        vouch_callback_url = f'https://{vouch_hostname}/auth'
        m = ("[green]Please enter a comma seperated list of emails that are "
             "allowed to access domains behind Vouch")
        emails = Prompt.ask(m)
        m = ("[green]Please enter a comma seperated list of domains that are "
             "allowed to use Vouch")
        domains = Prompt.ask(m)

        # if using bitwarden, put the secret in bitarden and ESO will grab it
        if bitwarden:
            # create oauth OIDC bitwarden item
            bitwarden.create_login(name='vouch-oauth-config',
                                   user='vouch',
                                   password=vouch_client_secret,
                                   fields=[
                                       {'authUrl': f'{base_url}auth'},
                                       {'tokenUrl': f'{base_url}token'},
                                       {'userInfoUrl': f'{base_url}userinfo'},
                                       {'callbackUrls': vouch_callback_url}
                                       ])

            # create vouch config bitwarden item
            bitwarden.create_login(name='vouch-config',
                                   user='vouch',
                                   password='',
                                   fields=[{'domains': domains},
                                           {'allowList': emails}])
        # create vouch k8s secrets if we're not using bitwarden
        else:
            # create oauth OIDC k8s secret
            create_secret('vouch-oauth-config', 'vouch',
                          {'user': 'vouch',
                           'password': vouch_client_secret,
                           'authUrl': f'{base_url}auth',
                           'tokenUrl': f'{base_url}token',
                           'userInfoUrl': f'{base_url}userinfo',
                           'callbackUrls': vouch_callback_url})

            # create vouch config k8s secret
            create_secret('vouch-config', 'vouch',
                          {'domains': domains, 'allowList': emails})

    install_with_argocd('vouch', vouch_config_dict['argo'])
    return True 
