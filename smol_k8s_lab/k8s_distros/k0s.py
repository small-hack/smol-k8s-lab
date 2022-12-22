#!/usr/bin/env python3.11
"""
       Name: k0s
DESCRIPTION: Install k0s
    AUTHORS: <https://github.com/cloudymax>, <https://github.com/jessebot>
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""

import logging as log
from os import path, chmod, remove
from requests import get
from shutil import which
from socket import gethostname
import stat

from ..subproc import subproc, simple_loading_bar
from ..env_config import USER, KUBECONFIG
from ..console_logging import sub_header


HOSTNAME = gethostname()


def install_k0s_cluster():
    """
    python installation for k0s
    """
    installer_url = "https://get.k0s.sh"
    install_path = "./install_k0s.sh"

    # download the installer if we don't have it here already
    FILE_EXISTS = path.exists(install_path)

    if FILE_EXISTS is not True:
        website = get(installer_url)
        new_file = open(install_path, "wb")
        new_file.write(website.content)
        new_file.close()

    # make sure we can actually execute the script
    chmod(install_path, stat.S_IRWXU)

    # Installs the k0s cli if needed
    install = f'sudo {install_path}'

    # Creates a single-node cluster
    create = 'sudo k0s install controller --single'

    # Uses a service to persist cluster through reboot
    persist = 'sudo k0s start'

    subproc([install, create, persist], spinner=True)

    # cleanup the installer file
    remove(install_path)

    task_text = 'Waiting for node to become active...'
    task_command = ('sudo k0s kubectl wait --for=condition=ready node ' +
                    HOSTNAME)
    simple_loading_bar({task_text: task_command}, time_to_wait=300)

    log.info("Creating kubeconfig for k0s cluster...")
    # create a kube config
    create_config = 'sudo k0s kubeconfig admin'
    kubeconfig = subproc([create_config], spinner=False)

    # we still have to write the output of the above command to a file
    with open(KUBECONFIG, "w") as kubefile:
        for line in kubeconfig:
            kubefile.write(line)

    # sometimes this is owned by root, so we need to fix the permissions
    chmod_config = f'sudo chmod 600 {KUBECONFIG}'
    chown_config = f'sudo chown {USER}: {KUBECONFIG}'
    subproc([chmod_config, chown_config], spinner=False)

    return


def uninstall_k0s():
    """
    Stop the k0s cluster, then remove all associated resources.
    """
    if which('k0s'):
        subproc(['sudo k0s stop'], error_ok=True)
        subproc(['sudo k0s reset'], error_ok=True)
    else:
        log.debug("K0s is already uninstalled.")
        sub_header("K0s is already uninstalled.", False, False)

    return True
