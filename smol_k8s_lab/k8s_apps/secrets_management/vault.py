#!/usr/bin/env python3.11
"""
       Name: vault
DESCRIPTION: configures vault app and secrets operator
     AUTHOR: @jessebot
    LICENSE: The setup script is licensed under:
               GNU AFFERO GENERAL PUBLIC LICENSE Version 3 and higher

             Hashicorp Vault has a custom license that you can view at their repo:
                 https://github.com/hashicorp/vault/blob/main/LICENSE

             smol-k8s-lab do not claim any of Vault as our own and we do not
             provide any paid support for Vault. If support is needed for the
             Vault components of smol-k8s-lab, it must be done unpaid via the
             smol-k8s-lab community or via an official enterprise contract from
             official Hashicorp channels.
"""

# internal libraries
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_tools.argocd_util import ArgoCD
from smol_k8s_lab.utils.rich_cli.console_logging import header
from smol_k8s_lab.utils.run.subproc import subproc

# external libraries
import logging as log
from time import sleep


def configure_vault(argocd: ArgoCD,
                    vault_dict: dict,
                    bitwarden: BwCLI = None) -> None:
    """
    configures the hashicorp vault helm chart
    """
    argo_dict = vault_dict['argo']

    header("Installing the Hashicorp Vault app...", "🔑")
    installed_app = argocd.install_app('vault', argo_dict, True)

    # get any secret keys passed in
    secrets = vault_dict['argo']['secret_keys']
    if secrets:
        vault_cluster_name = secrets['cluster_name']

    init_dict = vault_dict['init']
    if init_dict['enabled'] and not installed_app:
        log.info("Vault init enabled. We'll proceed with the unsealing process")
        initialize_vault(argo_dict['namespace'], vault_cluster_name, bitwarden)


def initialize_vault(namespace: str,
                     vault_cluster_name: str = "",
                     bitwarden: BwCLI = None):
    """
    initializes vault and sets up the keys. Puts keys in bitwarden, if BwCLI
    object is passed in
    """
    # first get the vault pod
    vault_pods = None
    cmd = (f"kubectl get pods -l app.kubernetes.io/name=vault -n {namespace} "
           "--no-headers -o custom-columns=NAME:.metadata.name")

    # it might fail the first time, though, so keep trying...
    while not vault_pods:
        vault_pods = subproc([cmd])
        sleep(5)

    pods = vault_pods.split()
    # initialize vault, which will produce something like:
    # Unseal Key 1: MBFSDepD9E6whREc6Dj+k3pMaKJ6cCnCUWcySJQymObb
    # Unseal Key 2: zQj4v22k9ixegS+94HJwmIaWLBL3nZHe1i+b/wHz25fr
    # Unseal Key 3: 7dbPPeeGGW3SmeBFFo04peCKkXFuuyKc8b2DuntA4VU5
    # Unseal Key 4: tLt+ME7Z7hYUATfWnuQdfCEgnKA2L173dptAwfmenCdf
    # Unseal Key 5: vYt9bxLr0+OzJ8m7c7cNMFj7nvdLljj0xWRbpLezFAI9
    # Initial Root Token: s.zJNwZlRrqISjyBHFMiEca6GF
    cmd = (f"kubectl exec -n {namespace} --stdin=true --tty=true {pods[0]}"
           " -- vault operator init")
    key_lines_str = subproc([cmd], decode_ascii=True, quiet=True)
    key_lines = key_lines_str.split('\r\n')

    root_token_line = key_lines.pop(6)
    root_token = root_token_line.split(' ')[3]

    # used for unsealing, and we'll save up them to log.info at the end if no bitwarden
    keys = []
    # if bitwarden is enabled, we'll create one item with many custom fields
    if bitwarden:
        bw_objs = [create_custom_field('rootToken', root_token)]

    # iterate through each key and grab only the key field
    for key_line in key_lines[:4]:
        # this gets us both the key number and the value
        key_value_list = key_line.split(": ")
        # this is just UnsealKey1 or whatever number we're on
        key_name = key_value_list[0].replace(" ", "")
        # this is the actual key we need to keep secret
        key = key_value_list[1]
        keys.append(key)
        if bitwarden:
            bw_objs.append(create_custom_field(key_name, key))

    # store these keys in bitwarden for later use
    if bitwarden:
        bitwarden.create_login(name="vault-unsealing-key",
                               item_url=vault_cluster_name,
                               user="root",
                               password="see custom fields",
                               fields=bw_objs)

    # unseal each pod with each key...
    for pod in pods:
        cmds = []
        # Unseal the Vault server with the key shares until the key threshold is met
        for key in keys:
            cmds.append(f"kubectl exec -n {namespace} --stdin=true --tty=true {pod} -- "
                        f"vault operator unseal {key}")
        subproc(cmds, quiet=True)

    log.info("Vault is initialized and unsealed")


if __name__ == '__main__':
    initialize_vault('vault')
