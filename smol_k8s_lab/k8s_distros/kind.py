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
from ..console_logging import sub_header
from ..env_config import PWD
from ..subproc import subproc


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
    subproc([f"kind create cluster --config={full_path}"])

    return True


def delete_kind_cluster():
    """
    delete kind cluster, if kind exists
    returns True
    """
    if which('kind'):
        subproc(['kind delete cluster'])
    else:
        log.debug("Kind is not installed.")
        sub_header("Kind is not installed.", False, False)

    return True
