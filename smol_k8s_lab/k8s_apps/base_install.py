#!/usr/bin/env python3.11
"""
       Name: base_install
DESCRIPTION: installs helm repos, updates them, and installs charts for metallb,
             cert-manager, and ingress-nginx
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from rich.prompt import Prompt
from ..pretty_printing.console_logging import header
from ..k8s_tools.homelabHelm import prepare_helm
from ..k8s_tools.k8s_lib import K8s


def install_base_apps(k8s_obj: K8s,
                      k8s_distro: str = "",
                      metallb_dict: dict = {},
                      cert_manager_dict: dict = {},
                      argo_enabled: bool = False,
                      argo_secrets_enabled: bool = False) -> bool:
    """ 
    Helm installs all base apps: metallb, ingess-nginx, and cert-manager
    All Needed for getting Argo CD up and running.
    """
    metallb_enabled = metallb_dict['enabled']
    # make sure helm is installed and the repos are up to date
    prepare_helm(k8s_distro, metallb_enabled, argo_enabled, 
                 argo_secrets_enabled)

    # needed for metal (non-cloud provider) installs
    if metallb_enabled:
        header("Installing [b]metallb[/b] so we have an IP address pool.")
        from ..k8s_apps.metallb import configure_metallb
        if metallb_dict['init']['enabled']:
            cidr = metallb_dict['init']['values']['address_pool']
            if not cidr:
                m = "[green]Please enter a comma seperated list of IPs or CIDRs"
                cidr = Prompt.ask(m).split(',')

            configure_metallb(cidr)

    # ingress controller: so we can accept traffic from outside the cluster
    # nginx just because that's most supported, treafik support may be added later
    header("Installing [b]ingress-nginx-controller[/b]...")
    from ..k8s_apps.nginx_ingress_controller import configure_ingress_nginx
    configure_ingress_nginx(k8s_distro)

    # manager SSL/TLS certificates via lets-encrypt
    header("Installing [b]cert-manager[/b] for TLS certificates...")
    from ..k8s_apps.cert_manager import configure_cert_manager
    cert_manager_init = cert_manager_dict['init']['enabled']
    if cert_manager_init:
        email = cert_manager_dict['init']['values']['email']
    else:
        email = ""
    configure_cert_manager(k8s_obj, email)

    # success!
    return True
