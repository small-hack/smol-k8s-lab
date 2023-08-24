from ..k8s_tools.k8s_lib import K8s
from ..utils.bw_cli import BwCLI
from ..pretty_printing.console_logging import header
from ..k8s_apps.keycloak import configure_keycloak
from ..k8s_apps.zitadel import configure_zitadel
from ..k8s_apps.vouch import configure_vouch
import logging as log


def setup_oidc_provider(k8s_obj: K8s,
                        provider_name: str = "",
                        provider_dict: dict = {},
                        vouch_dict: dict = {},
                        bw: BwCLI = None,
                        argocd_fqdn: str = "") -> True:
    header("Setting up [green]OIDC[/]/[green]Oauth[/] Applications")

    # setup keycloak if we're using that for OIDC
    if provider_name == 'keycloak':
        log.debug("Setting up keycloak")
        configure_keycloak(k8s_obj, provider_dict, bw)
        extra = {'realm': provider_dict['argo']['secret_keys']['default_realm']}

    # setup zitadel if we're using that for OIDC
    elif provider_name == 'zitadel':
        log.debug("Setting up zitadel")
        extra = {'zitadel': configure_zitadel(k8s_obj, provider_dict, argocd_fqdn, bw)}

    if vouch_dict:
        log.debug("Setting up vouch")
        if vouch_dict['enabled']:
            configure_vouch(k8s_obj,
                            vouch_dict,
                            provider_name,
                            provider_dict['argo']['secret_keys']['hostname'],
                            bw,
                            **extra)

    return True
