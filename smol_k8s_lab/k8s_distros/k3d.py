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


# where we write this config
K3D_CFG_FILENAME = f"{XDG_CACHE_DIR}/k3d-config.yaml"


def create_k3d_cluster(cluster_name: str,
                        k3s_yaml: dict,
                        control_plane_nodes: int = 1,
                        worker_nodes: int = 0) -> None:
    """
    python installation for k3d
    """
    sub_header("Creating k3d cluster...")

    k3d_cfg = K3dConfig(cluster_name,
                        k3s_yaml,
                        control_plane_nodes,
                        worker_nodes)
    k3d_cfg.write_yaml()

    # actually running the k3d command
    res = subproc([f'k3d cluster create --config {K3D_CFG_FILENAME}'])
    log.info(res)


def delete_k3d_cluster(cluster_name: str) -> str:
    """
    delete k3d cluster by name
    """
    if cluster_name.startswith("k3d-"):
        cluster_name = cluster_name.replace("k3d-", "")

    res = subproc([f'k3d cluster delete {cluster_name}'])
    return res


class K3dConfig():
    """
    create and update a k3d config file
    """
    def __init__(self,
                 cluster_name: str,
                 k3s_yaml: dict,
                 control_plane_nodes: int = 1,
                 worker_nodes: int = 0) -> None:

        # base config for k3s
        self.k3d_cfg = {"apiVersion": "k3d.io/v1alpha5",
                        "kind": "Simple",
                        "metadata": {"name": cluster_name},
                        "options": {
                            "kubeconfig": {
                                "updateDefaultKubeconfig": True,
                                "switchCurrentContext": True
                                }
                            }
                        }

        # filter for which nodes to apply which k3s args to
        self.node_filters = []

        self.k3d_cfg["servers"] = control_plane_nodes
        # only specify server if there's control_plane_nodes
        if control_plane_nodes > 0:
            self.node_filters.append("server:*")

        self.k3d_cfg["agents"] = worker_nodes
        # only specify agents if there's worker_node
        if worker_nodes > 0:
            self.node_filters.append("agent:*")

        # these are the rest of the k3s specific arguments
        if k3s_yaml:
            if not self.k3d_cfg['options'].get('k3s', None):
                self.k3d_cfg['options']['k3s'] = {"extraArgs": []}

            for arg, value in k3s_yaml.items():
                if isinstance(value, bool):
                    self.create_arg_dict(self.node_filters, arg)

                if isinstance(value, str):
                    self.create_arg_dict(self.node_filters, arg, value)

                elif isinstance(value, list):
                    self.create_arg_dict(self.node_filters, arg, ",".join(value))

    def create_arg_dict(self, node_filters: list, arg: str, value: str = "") -> None:
        """
        creates a small arg dict and writes it to the class's k3d_cfg variable
        """
        if value:
            arg += f"={value}"

        arg_dict = {"arg": f'"--{arg}"', "nodeFilters": self.node_filters.copy()}
        self.k3d_cfg['options']['k3s']['extraArgs'].append(arg_dict)

    def write_yaml(self) -> None:
        # write out the config file we just finished
        with open(K3D_CFG_FILENAME, 'w') as k3d_cfg_file:
            dump(self.k3d_cfg, k3d_cfg_file)
