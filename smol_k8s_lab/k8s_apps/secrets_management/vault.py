#!/usr/bin/env python3.11
"""
       Name: vault
DESCRIPTION: configures vault app and secrets operator
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version python3
             vault itself has a custom license that you can view at
             smol-k8s-lab do not claim any of their code
"""
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_tools.argocd_util import (install_with_argocd,
                                                check_if_argocd_app_exists,
                                                wait_for_argocd_app)
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
# from smol_k8s_lab.utils.passwords import create_password
from smol_k8s_lab.utils.rich_cli.console_logging import header
from smol_k8s_lab.utils.subproc import subproc

from logging import log


def configure_vault(k8s_obj: K8s, vault_dict: dict, bitwarden: BwCLI = None) -> None:
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
        log.info("Vault init enabled. We'll proceed with the unsealing process")
        initialize_vault(argo_dict['namespace'], bitwarden)


def initialize_vault(namespace: str, bitwarden: BwCLI = None):
    """ 
    initializes vault and sets up the keys. Puts keys in bitwarden, if BwCLI
    object is passed in
    """
    # first get the vault pod
    cmd = ("kubectl get pods "
           "--selector='app.kubernetes.io/name=vault' "
           f"--namespace {namespace} "
           "--no-headers --custom-columns=NAME:.metadata.name")
    vault_pods = subproc([cmd]).split()

    # initialize vault, which will produce something like:
    # Unseal Key 1: MBFSDepD9E6whREc6Dj+k3pMaKJ6cCnCUWcySJQymObb
    # Unseal Key 2: zQj4v22k9ixegS+94HJwmIaWLBL3nZHe1i+b/wHz25fr
    # Unseal Key 3: 7dbPPeeGGW3SmeBFFo04peCKkXFuuyKc8b2DuntA4VU5
    # Unseal Key 4: tLt+ME7Z7hYUATfWnuQdfCEgnKA2L173dptAwfmenCdf
    # Unseal Key 5: vYt9bxLr0+OzJ8m7c7cNMFj7nvdLljj0xWRbpLezFAI9
    # Initial Root Token: s.zJNwZlRrqISjyBHFMiEca6GF
    cmd = (f"kubectl exec --stdin=true --tty=true {vault_pods[0]} -- "
           "vault operator init")
    key_lines = subproc([cmd], shell=True, universal_newlines=True).split('\n')
    root_token = key_lines.pop().split()[3]

    # used for unsealing, and we'll save up them to print at the end if no bitwarden
    keys = []
    # if bitwarden is enabled, we'll create one item with many custom fields
    if bitwarden:
        bw_objs = [create_custom_field('rootToken', root_token)]

    # iterate through each key and grab only the key field
    for index, key_line in enumerate(key_lines):
        # this should be the key only
        key = key_line.split()[3]
        keys.append(key)
        if bitwarden:
            bw_objs.append(create_custom_field(f'unsealKey{str(index)}', key))

    # store these keys in bitwarden for later use
    if bitwarden:
        bitwarden.create_login(name="vault-unsealing-key",
                               item_url="",
                               user="root",
                               password="see custom fields",
                               fields=bw_objs)

    # unseal each pod with each key...
    for pod in vault_pods:
        cmds = []
        # Unseal the Vault server with the key shares until the key threshold is met
        for key in keys:
            cmds.append(f"kubectl exec --stdin=true --tty=true {pod} -- "
                        f"vault operator unseal {key}")
        subproc(cmds, shell=True, universal_newlines=True)
