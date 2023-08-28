#!/usr/bin/env python3.11
"""
       Name: kind
DESCRIPTION: create or delete a kind cluster, part of smol-k8s-lab
     AUTHOR: <https://github.com/jessebot>
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
import logging as log
from os import path
from shutil import which
from ..pretty_printing.console_logging import sub_header
from ..constants import PWD
from ..utils.subproc import subproc


def install_kind_cluster():
    """
    Run installation process for kind and create cluster
    returns True
    """
    # make sure kind is installed first, and if not, install it
    if not which("kind"):
        msg = ("ʕ•́ᴥ•̀ʔ [b]kind[/b] is [warn]not installed[/warn]. "
               "[i]We'll install it for you.[/i] ʕᵔᴥᵔʔ")
        sub_header(msg)
        log.debug("Installing kind with brew...")
        subproc(['brew install kind'], spinner=True)

    log.debug("Creating a kind cluster...")

    # use our pre-configured kind file to install a small cluster
    full_path = path.join(PWD, 'config/kind_cluster_config.yaml')
    cmd = f"kind create cluster --name smol-k8s-lab-kind --config={full_path}"
    subproc([cmd])

    return True


def delete_kind_cluster():
    """
    delete kind cluster, if kind exists
    returns True
    """
    er = "smol-k8s-lab hasn't installed a [green]kind[/green] cluster here yet"
    if which('kind'):
        if 'smol-k8s-lab-kind' in subproc(['kind get clusters']):
            subproc(['kind delete cluster --name smol-k8s-lab-kind'])
        else:
            sub_header(er, False, False)
    else:
        log.debug("Kind is not installed.")
        sub_header("Kind is not installed.", False, False)

    return True
