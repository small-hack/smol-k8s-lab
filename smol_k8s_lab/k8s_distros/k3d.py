#!/usr/bin/env python3.11
"""
       Name: k3d
DESCRIPTION: install k3d :D Not affiliated with k3s, rancher, or suse. just a fan
     AUTHOR: @Jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from ..rich_cli.console_logging import sub_header
from ..utils.subproc import subproc


def install_k3d_cluster(kubelet_args: list, k3s_cli_args: list) -> bool:
    """
    python installation for k3d
    returns true if it worked
    """
    cluster_name = 'smol-k8s-lab-k3d'
    install_cmd = f'k3d create cluster {cluster_name}'

    if kubelet_args:
        for arg in kubelet_args:
            install_cmd += f" --k3s-arg '--kubelet-arg={arg}'"

    if k3s_cli_args:
        for cli_arg in k3s_cli_args:
            install_cmd += f" --k3s-arg '{cli_arg}'"

    sub_header("Creating k3d cluster...")
    subproc([install_cmd])
    return True


def uninstall_k3d_cluster():
    """
    remove k3d
    """
    subproc(['k3d delete cluster'])
    return True
