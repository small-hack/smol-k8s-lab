#!/usr/bin/env python3.11
"""
       Name: kind
DESCRIPTION: create or delete a kind cluster
     AUTHOR: github.com/jessebot/smol-k8s-lab
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
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
        subproc(['brew install kind'], spinner=True)

    # then use our pre-configured kind file to install a small cluster
    full_path = path.join(PWD, 'distros/kind/kind_cluster_config.yaml')
    subproc([f"kind create cluster --config={full_path}"], spinner=True)

    return True


def delete_kind_cluster():
    """
    delete kind cluster
    returns True
    """
    subproc(['kind delete cluster'])
    return True
