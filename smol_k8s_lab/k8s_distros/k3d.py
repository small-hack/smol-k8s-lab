#!/usr/bin/env python3.11
"""
       Name: k3d
DESCRIPTION: install k3d :D
     AUTHOR: @Jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from ..pretty_printing.console_logging import sub_header
from ..utils.subproc import subproc


def install_k3d_cluster() -> bool:
    """
    https://k3d.io/v5.5.2/#install-script
    python installation for k3d
    returns true if it worked
    """
    sub_header("Creating k3d cluster...")
    subproc(['k3d create cluster smol-k8s-lab-k3d'])
    return True
