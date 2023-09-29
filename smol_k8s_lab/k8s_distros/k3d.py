#!/usr/bin/env python3.11
"""
       Name: k3d
DESCRIPTION: install k3d :D Not affiliated with k3s, rancher, or suse. just a fan
     AUTHOR: @Jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from ..utils.rich_cli.console_logging import sub_header
from ..utils.subproc import subproc
from ..constants import XDG_CACHE_DIR
import logging as log
from yaml import dump


def install_k3d_cluster(k3s_cli_args: list,
                        kubelet_args: dict,
                        control_plane_nodes: int = 1,
                        worker_nodes: int = 0,
                        cluster_name: str = 'smol-k8s-lab-k3d') -> bool:
    """
    python installation for k3d
    returns true if it worked
    """
    sub_header("Creating k3d cluster...")

    # base config for k3s
    k3d_cfg = {"apiVersion": "k3d.io/v1alpha5",
               "kind": "Simple",
               "metadata": {"name": cluster_name}}

    # filter for which nodes to apply which k3s args to
    node_filters = []

    # only specify server if there's more control_plane_nodes
    if control_plane_nodes > 0:
        k3d_cfg["servers"] = control_plane_nodes
        node_filters.append("server:*")

    # only specify agents if there's more than one worker_node
    if worker_nodes > 0:
        k3d_cfg["agents"] = worker_nodes
        node_filters.append("agent:*")

    # we attempt to append each kubelet-arg as an option
    if kubelet_args:
        k3d_cfg['options'] = {'k3s': {"extraArgs": []}}
        for key, value in kubelet_args.items():
            cli_arg = f"--kubelet-arg={key}={value}"
            arg_dict = {"arg": cli_arg, "nodeFilters": node_filters.copy()}

            k3d_cfg['options']['k3s']['extraArgs'].append(arg_dict)

    # these are the rest of the k3s specific arguments
    if k3s_cli_args:
        if not k3d_cfg.get('k3s', None):
            k3d_cfg['options'] = {'k3s': {"extraArgs": []}}

        for cli_arg in k3s_cli_args:
            arg_dict = {"arg": cli_arg, "nodeFilters": node_filters.copy()}
            k3d_cfg['options']['k3s']['extraArgs'].append(arg_dict)

    cfg_file = f"{XDG_CACHE_DIR}/k3d-config.yaml"

    # write out the config file we just finished
    with open(cfg_file, 'w') as k3d_cfg_file:
        dump(k3d_cfg, k3d_cfg_file)

    # actually running the k3d command
    res = subproc([f'k3d cluster create --config {cfg_file}'])
    log.info(res)
    return True


def uninstall_k3d_cluster():
    """
    remove k3d
    """
    subproc(['k3d cluster delete'])
    return True
