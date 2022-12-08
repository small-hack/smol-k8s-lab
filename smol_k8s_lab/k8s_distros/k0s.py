#!/usr/bin/env python3.11
"""
       Name: k0s
DESCRIPTION: Install k0s
     AUTHOR: Max!
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""

from os import path, chmod, remove
from pathlib import Path
from requests import get
from socket import gethostname
import stat

from ..subproc import subproc, simple_loading_bar
from ..env_config import HOME_DIR, USER


HOSTNAME = gethostname()
KUBECONFIG_PATH = f'{HOME_DIR}/.kube/kubeconfig'


def install_k0s_cluster():
    """
    python installation for k0s
    """
    INSTALLER_URL = "https://get.k0s.sh"
    INSTALL_PATH = "./install_k0s.sh"

    # download the installer if we don't have it here already
    FILE_EXISTS = path.exists(INSTALL_PATH)

    if FILE_EXISTS is not True:
        website = get(INSTALLER_URL)
        new_file = open(INSTALL_PATH, "wb")
        new_file.write(website.content)
        new_file.close()

    # make sure we can actually execute the script
    chmod(INSTALL_PATH, stat.S_IRWXU)

    # Installs the k0s cli if needed
    install = f'sudo {INSTALL_PATH}'

    # Creates a single-node cluster
    create = ('sudo k0s install controller --single')

    # Uses a service to persist cluster through reboot
    persist = ('sudo k0s start')

    # cleanup the installer file
    remove(INSTALL_PATH)

    subproc([install, create, persist], spinner=True)

    # create the ~/.kube directory if it doesn't exist
    Path(f'{HOME_DIR}/.kube').mkdir(exist_ok=True)

    task_text = 'Waiting for node to become active...'
    task_command = ('sudo k0s kubectl wait --for=condition=ready node ' +
                    HOSTNAME)
    simple_loading_bar({task_text: task_command}, time_to_wait=300)

    # sometimes this is owned by root, so we need to fix the permissions
    if path.exists(KUBECONFIG_PATH):
        chmod_config = f'sudo chmod 644 {KUBECONFIG_PATH}'
        chmod_config = f'sudo chown {USER}: {KUBECONFIG_PATH}'
        subproc([chmod_config], spinner=False)

    # create a kube config
    create_config = 'sudo k0s kubeconfig admin'
    kubeconfig = subproc([create_config], spinner=False)

    # we still have to write the output of the above command to a file
    with open(KUBECONFIG_PATH, "w") as kubefile:
        for line in kubeconfig:
            kubefile.write(line)

    return


def uninstall_k0s():
    """
    Stop the k0s cluster, then remove all associated resources.
    """

    subproc(['sudo k0s stop'], error_ok=True)
    subproc(['sudo k0s reset'], error_ok=True)
    return True
