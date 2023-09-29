#!/usr/bin/env python3.11
"""
       Name: k3d
DESCRIPTION: install k3d :D Not affiliated with k3s, rancher, or suse. just a fan
     AUTHOR: @Jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from ..utils.rich_cli.console_logging import sub_header
from ..utils.subproc import subproc


def install_k3d_cluster(k3s_cli_args: list,
                        kubelet_args: dict,
                        control_plane_nodes: int = 1,
                        worker_nodes: int = 0) -> bool:
    """
    python installation for k3d
    returns true if it worked
    """
    sub_header("Creating k3d cluster...")

    cluster_name = 'smol-k8s-lab-k3d'
    install_cmd = f'k3d cluster create {cluster_name}'

    # one server node always, but if the user wants more than one node, we
    # create the rest as agents for now
    install_cmd += f' --servers {control_plane_nodes} --agents {worker_nodes}'

    # we attempt to append each kubelet-arg as an option
    if kubelet_args:
        for key, value in kubelet_args.items():
            install_cmd += f" --k3s-arg '--kubelet-arg={key}={value}'"

    if k3s_cli_args:
        for cli_arg in k3s_cli_args:
            install_cmd += f" --k3s-arg '{cli_arg}'"

    subproc([install_cmd])
    return True


def uninstall_k3d_cluster():
    """
    remove k3d
    """
    subproc(['k3d cluster delete'])
    return True
