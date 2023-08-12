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
from shutil import which
import stat
from ..console_logging import sub_header
from ..constants import USER, KUBECONFIG
from ..subproc import subproc


def install_k3s_cluster(disable_servicelb=True, additonal_arguments=[]):
    """
    python installation for k3s, emulates curl -sfL https://get.k3s.io | sh -
    Notes: --flannel-backend=none will break k3s on metal
    """
    cmd = "kubectl config get-clusters"
    clusters = subproc([cmd])
    if 'smol-k8s-lab-k3s' in clusters:
        log.info("K3s cluster detected in $KUBECONFIG. Checking if it's up.")
        cmd = "kubectl get pods"
        try:
            subproc([cmd])
        except Exception as e:
            log.info(e)
            log.info("Looks like the current k3s cluster is not operational.")
        else:
            # exit this function because k3s is already installed
            return

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

    # Grab the kubeconfig and copy it locally
    cp = f'sudo cp /etc/rancher/k3s/k3s.yaml {KUBECONFIG}'

    # change the mode (permissions) of kubeconfig so that it doesn't complain
    chmod_cmd = f'sudo chmod 600 {KUBECONFIG}'
    # change the owner to the current user running this script
    chown_cmd = f'sudo chown {USER}: {KUBECONFIG}'
    # rename the cluster in your kubeconfig to smol-k8s-lab-k3s
    cluster_rename = f"sed -i 's/default/smol-k8s-lab-k3s/g' {KUBECONFIG}"

    # run all 3 commands one after the other
    subproc([cp, chmod_cmd, chown_cmd, cluster_rename])

    # remove the script after we're done
    remove('./install.sh')

    return True


def uninstall_k3s():
    """
    uninstall k3s if k3s is present
    returns True
    """
    if which('k3s-uninstall.sh'):
        subproc(['k3s-uninstall.sh'], error_ok=True, spinner=False)
    else:
        log.debug("K3s is already uninstalled.")
        sub_header("K3s is already uninstalled.", False, False)

    return True
