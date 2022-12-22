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
from ..env_config import USER, KUBECONFIG
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
           '--write-kubeconfig-mode=700')
    subproc([cmd], spinner=False)

    log.info(f"Updating your {KUBECONFIG}")

    # Grab the kubeconfig and copy it locally
    cp = f'sudo cp /etc/rancher/k3s/k3s.yaml {KUBECONFIG}'

    # change the permissions os that it doesn't complain
    chmod_cmd = f'sudo chmod 600 {KUBECONFIG}'
    chown_cmd = f'sudo chown {USER}: {KUBECONFIG}'

    # run both commands one after the other
    subproc([cp, chmod_cmd, chown_cmd])

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
