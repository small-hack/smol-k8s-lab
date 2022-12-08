#!/usr/bin/env python3.11
"""
       Name: k3s
DESCRIPTION: install k3s :D
     AUTHOR: @Jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
import requests
from os import chmod, remove
from pathlib import Path
import stat
from ..env_config import HOME_DIR
from ..subproc import subproc


def install_k3s_cluster():
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
    cmd = ('./install.sh --disable=servicelb --disable=traefik '
           '--write-kubeconfig-mode=647')
    subproc([cmd], spinner=False)

    # create the ~/.kube directory if it doesn't exist
    Path(f'{HOME_DIR}/.kube').mkdir(exist_ok=True)

    # Grab the kubeconfig and copy it locally
    cp = f'sudo cp /etc/rancher/k3s/k3s.yaml {HOME_DIR}/.kube/kubeconfig'

    # change the permissions os that it doesn't complain
    chmod_cmd = f'sudo chmod 644 {HOME_DIR}/.kube/kubeconfig'

    # run both commands one after the other
    subproc([cp, chmod_cmd], spinner=True)

    # remove the script after we're done
    remove('./install.sh')

    return


def uninstall_k3s():
    """
    uninstall k3s
    """
    subproc(['k3s-uninstall.sh'], error_ok=True, spinner=False)
