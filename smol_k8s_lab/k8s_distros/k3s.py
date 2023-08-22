#!/usr/bin/env python3.11
"""
       Name: k3s
DESCRIPTION: install k3s :D
     AUTHOR: @Jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
import logging as log
from os import chmod, remove
import requests
import stat
from ..pretty_printing.console_logging import sub_header
from ..constants import USER, KUBECONFIG
from ..subproc import subproc


def install_k3s_cluster(disable_servicelb=True, additonal_arguments=[]):
    """
    python installation for k3s, emulates curl -sfL https://get.k3s.io | sh -
    Notes: --flannel-backend=none will break k3s on metal
    """
    # download the k3s installer if we don't have it here already
    url = requests.get("https://get.k3s.io")
    k3s_installer_file = open("./install.sh", "wb")
    k3s_installer_file.write(url.content)
    k3s_installer_file.close()

    # make sure we can actually execute the script
    chmod("./install.sh", stat.S_IRWXU)

    # create the k3s cluster (just one server node)
    cmd = ('./install.sh --disable=traefik --write-kubeconfig-mode=700 '
           '--secrets-encryption')

    if disable_servicelb:
        cmd += ' --disable=servicelb'

    # add additional arguments to k3s if there are any
    if additonal_arguments:
        for argument in additonal_arguments:
            cmd += ' ' + argument

    subproc([cmd], spinner=False)

    log.info(f"Updating your {KUBECONFIG}")

    k3s_kubeconfig = "/etc/rancher/k3s/k3s.yaml"
    # Grab the kubeconfig and copy it locally
    cp = f'sudo cp {k3s_kubeconfig} {KUBECONFIG}'

    # change the mode (permissions) of kubeconfig so that it doesn't complain
    chmod_cmd = f'sudo chmod 600 {KUBECONFIG}'
    # change the owner to the current user running this script
    chown_cmd = f'sudo chown {USER}: {KUBECONFIG}'

    # rename the cluster in your kubeconfig to smol-k8s-lab-k3s
    cluster_rename = "kubectl config rename-context default smol-k8s-lab-k3s"

    # run all 3 commands one after the other
    subproc([cp, chmod_cmd, chown_cmd, cluster_rename])

    # remove the script after we're done
    remove('./install.sh')

    return True


def uninstall_k3s(context: dict = {}):
    """
    uninstall k3s if k3s is present
    returns True
    """
    cmds = ["k3s-uninstall.sh",
            f"kubectl config delete-cluster {context['cluster']}",
            f"kubectl config delete-context {context['context']}"]

    subproc(cmds, spinner=False)

    return True
