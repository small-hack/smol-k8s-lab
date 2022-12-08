#!/usr/bin/env python3.11
"""
       Name: kind
DESCRIPTION: install or uninstall kind cluster
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from os import path
from shutil import which
from ..env_config import PWD, CONSOLE
from ..subproc import subproc


def install_kind_cluster():
    """
    python installation process for kind
    """
    # make sure kind is installed first, and if not, install it
    if not which("kind"):
        msg = ("ʕ•́ᴥ•̀ʔ [b]kind[/b] is [warn]not installed[/warn]. "
               "[i]We'll install it for you.[/i] ʕᵔᴥᵔʔ")
        CONSOLE.print(msg, justify='center')
        subproc(['brew install kind'], spinner=True)

    # then use our pre-configured kind file to install a small cluster
    full_path = path.join(PWD, 'distros/kind/kind_cluster_config.yaml')
    subproc([f"kind create cluster --config={full_path}"], spinner=True)
    return


def uninstall_kind_cluster():
    """
    uninstall kind cluster
    """
    subproc(['kind delete cluster'])
