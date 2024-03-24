#!/usr/bin/env python3.11
"""
       Name: base_install
DESCRIPTION: installs helm repos, updates them, and installs charts for metallb,
             cert-manager, and ingress-nginx
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
import logging as log
from rich.prompt import Prompt
from ..bitwarden.bw_cli import BwCLI
from ..k8s_tools.helm import prepare_helm
from ..k8s_tools.k8s_lib import K8s
from ..utils.rich_cli.console_logging import header
from .argocd import configure_argocd
from .ingress.ingress_nginx_controller import (configure_ingress_nginx,
                                               install_ingress_nginx_argocd_app)
from .ingress.cert_manager import configure_cert_manager
# from .identity_provider.keycloak import configure_keycloak
from .identity_provider.zitadel import configure_zitadel
from .identity_provider.zitadel_api import Zitadel
from .identity_provider.vouch import configure_vouch
from .networking.metallb import configure_metallb
from .networking.cilium import configure_cilium
from .secrets_management.external_secrets_operator import configure_external_secrets
from .secrets_management.infisical import configure_infisical
from .secrets_management.vault import configure_vault
from .social.matrix import configure_matrix
from .social.mastodon import configure_mastodon
from .social.nextcloud import configure_nextcloud


def setup_k8s_secrets_management(k8s_obj: K8s,
                                 k8s_distro: str,
                                 eso_dict: dict = {},
                                 eso_provider: str = "",
                                 infisical_dict: dict = {},
                                 vault_dict: dict = {},
                                 bitwarden: BwCLI = None) -> None:
    """
    sets up k8s secrets management tooling
    """
    # secrets management section
    header_msg = "Setting up K8s secret management with [green]"

    # setup external secrets operator and bitwarden external secrets
    if eso_dict['enabled']:
        header_msg += f'External Secrets Operator[/] and [blue]{eso_provider}[/] as the Provider'
        header(header_msg, '🤫')
        configure_external_secrets(k8s_obj,
                                   eso_dict,
                                   eso_provider,
                                   k8s_distro,
                                   bitwarden)

    # setup infisical - an secrets manager and operator for k8s that replaces eso
    elif infisical_dict['enabled']:
        header_msg += 'Infisical Secrets Operator[/]'
        header(header_msg, '🤫')
        configure_infisical(k8s_obj, infisical_dict)

    # setup hashicorp's vault, a secret key management system that works with eso
    if vault_dict['enabled']:
        configure_vault(k8s_obj, vault_dict)


def setup_oidc_provider(k8s_obj: K8s,
                        api_tls_verify: bool = False,
                        zitadel_dict: dict = {},
                        vouch_dict: dict = {},
                        bw: BwCLI = None,
                        argocd_fqdn: str = "") -> Zitadel | None:
    """
    sets up oidc provider. only zitadel is supported right now
    if we choose to add keycloak back, we'll be adding the following arg
    keycloak_dict: dict = {}
    """
    header("Setting up [green]OIDC[/]/[green]Oauth[/] Applications")

    # keycloak_enabled = keycloak_dict['enabled']
    zitadel_enabled = zitadel_dict['enabled']

    vouch_enabled = False
    if vouch_dict:
        vouch_enabled = vouch_dict['enabled']

    # setup keycloak if we're using that for OIDC
    # if keycloak_enabled:
    #     log.debug("Setting up keycloak")
    #     configure_keycloak(k8s_obj, keycloak_dict, bw)
    #     realm = keycloak_dict['argo']['secret_keys']['default_realm']
    #     user = keycloak_dict['init']['values']['username']

    # setup zitadel if we're using that for OIDC
    if zitadel_enabled:
        zitadel_init_enabled = zitadel_dict['init']['enabled']
        log.debug("Setting up zitadel")
        if zitadel_init_enabled:
            zitadel_obj = configure_zitadel(
                    k8s_obj=k8s_obj,
                    config_dict=zitadel_dict,
                    api_tls_verify=api_tls_verify,
                    argocd_hostname=argocd_fqdn,
                    bitwarden=bw
                    )
        else:
            configure_zitadel(k8s_obj=k8s_obj,
                              config_dict=zitadel_dict,
                              bitwarden=bw)

    if vouch_enabled:
        log.debug("Setting up vouch")
        # if keycloak_enabled:
        #     keycloak_host = keycloak_dict['argo']['secret_keys']['hostname']
        #     configure_vouch(
        #        k8s_obj=k8s_obj,
        #        vouch_config_dict=vouch_dict,
        #        oidc_provider_name='keycloak',
        #        oidc_provider_hostname=keycloak_host,
        #        bitwarden=bw,
        #        users=[{'user': user}],
        #        realm=realm)
        if zitadel_enabled:
            configure_vouch(k8s_obj=k8s_obj,
                            vouch_config_dict=vouch_dict,
                            oidc_provider_name='zitadel',
                            oidc_provider_hostname=zitadel_dict['argo']['secret_keys']['hostname'],
                            bitwarden=bw,
                            users=[],
                            realm="",
                            zitadel=zitadel_obj)
        else:
            configure_vouch(k8s_obj, vouch_dict, '', '', bw)

    if zitadel_enabled and zitadel_init_enabled:
        return zitadel_obj


def setup_base_apps(k8s_obj: K8s,
                    k8s_distro: str,
                    cilium_dict: dict = {},
                    metallb_dict: dict = {},
                    ingress_dict: dict = {},
                    cert_manager_dict: dict = {},
                    argo_enabled: bool = False,
                    argo_secrets_plugin_enabled: bool = False,
                    plugin_secrets: dict = {},
                    bw: BwCLI = None) -> None:
    """ 
    Uses Helm to install all base apps that need to be running being argo cd:
        cilium, metallb, ingess-nginx, cert-manager, argo cd, argocd secrets plugin
    All Needed for getting Argo CD up and running.
    """
    metallb_enabled = metallb_dict['enabled']
    cilium_enabled = cilium_dict['enabled']
    ingress_nginx_enabled = ingress_dict["enabled"]
    # make sure helm is installed and the repos are up to date
    prepare_helm(k8s_distro, argo_enabled, metallb_enabled, cilium_enabled,
                 argo_secrets_plugin_enabled)

    # needed for network policy editor and hubble UI
    if cilium_enabled:
        header("Installing [green]cilium[/green] so we have networking tools",
               '🛜')
        if cilium_dict['init']['enabled']:
            configure_cilium(cilium_dict)

    # needed for metal (non-cloud provider) installs
    if metallb_enabled:
        header("Installing [green]metallb[/green] so we have an IP address pool",
               '🛜')
        if metallb_dict['init']['enabled']:
            cidr = metallb_dict['init']['values']['address_pool']
            if not cidr:
                m = "[green]Please enter a comma seperated list of IPs or CIDRs"
                cidr = Prompt.ask(m).split(',')

            configure_metallb(k8s_obj, cidr)

    # ingress controller: so we can accept traffic from outside the cluster
    if ingress_nginx_enabled:
        # nginx just because that's most supported, treafik support may be added later
        header("Installing [green]ingress-nginx-controller[/green] to access web"
               " apps outside the cluster", "🌐")
        configure_ingress_nginx(k8s_obj, k8s_distro)

    # manager SSL/TLS certificates via lets-encrypt
    header("Installing [green]cert-manager[/green] for TLS certificates...", '📜')
    if cert_manager_dict["enabled"]:
        configure_cert_manager(k8s_obj, cert_manager_dict['init'])

    # then we install argo cd if it's enabled
    if argo_enabled:
        configure_argocd(k8s_obj,
                         bw, 
                         argo_secrets_plugin_enabled,
                         plugin_secrets)

    if ingress_nginx_enabled and argo_enabled:
        install_ingress_nginx_argocd_app(k8s_obj, ingress_dict)


def setup_federated_apps(k8s_obj: K8s,
                         api_tls_verify: bool = False,
                         nextcloud_dict: dict = {},
                         mastodon_dict: dict = {},
                         matrix_dict: dict = {},
                         zitadel_hostname: str = "",
                         zitadel_obj: Zitadel = None,
                         bw: BwCLI = None) -> None:
    """
    Setup any federated apps with initialization supported
    """
    if nextcloud_dict['enabled']:
        configure_nextcloud(k8s_obj, nextcloud_dict, bw, zitadel_obj)

    if mastodon_dict['enabled']:
        configure_mastodon(k8s_obj, mastodon_dict, bw)

    if matrix_dict['enabled']:
        configure_matrix(k8s_obj, matrix_dict, zitadel_obj, bw)
