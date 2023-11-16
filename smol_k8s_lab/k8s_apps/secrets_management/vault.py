#!/usr/bin/env python3.11
"""
       Name: vault
DESCRIPTION: configures vault app and secrets operator
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version python3
             vault itself has a custom license that you can view at
             smol-k8s-lab do not claim any of their code
"""
from smol_k8s_lab.k8s_tools.argocd_util import (install_with_argocd,
                                                check_if_argocd_app_exists,
                                                wait_for_argocd_app)
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
# from smol_k8s_lab.utils.passwords import create_password
from smol_k8s_lab.utils.rich_cli.console_logging import header

from logging import log


def configure_vault(k8s_obj: K8s, vault_dict: dict) -> None:
    """
    configures the hashicorp vault helm chart
    """
    # check immediately if this app is installed
    app_installed = check_if_argocd_app_exists('vault')

    header("Installing the vault app and Secrets operator...", "🔑")
    argo_dict = vault_dict['argo']

    # get any secret keys passed in
    secrets = vault_dict['argo']['secret_keys']
    if secrets:
        vault_hostname = secrets['hostname']
        log.debug(vault_hostname)

    if not app_installed:
        install_with_argocd(k8s_obj, 'vault', argo_dict)
        wait_for_argocd_app('vault')

    init_dict = vault_dict['init']
    if init_dict['enabled']:
        log.info("Vault init is enabled, so we'll proceed with the unsealing process")
