#!/usr/bin/env python3.11
"""
       Name: kind
DESCRIPTION: create or delete a kind cluster, part of smol-k8s-lab
     AUTHOR: <https://github.com/jessebot>
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from ..constants import XDG_CACHE_DIR
from ..utils.rich_cli.console_logging import sub_header
from ..utils.run.subproc import subproc
import logging as log
from os import path
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import PreservedScalarString as pss
from shutil import which
from sys import exit


yaml = YAML()

# https://pypi.org/project/ruamel.yaml.string/
safe_yaml = YAML(typ=['rt', 'string'])


def create_kind_cluster(cluster_name: str,
                        kubelet_args: dict = {},
                        networking_args: dict = {},
                        control_plane_nodes: int = 1,
                        worker_nodes: int = 1) -> True:
    """
    Run installation process for kind and create cluster
    returns True
    """

    # make sure kind is installed first, and if not, install it
    if not which("kind"):
        msg = ("ʕ•́ᴥ•̀ʔ [b]kind[/b] is [warn]not installed[/warn]. "
               "[i]We'll try to install it for you.[/i] ʕᵔᴥᵔʔ")
        sub_header(msg)
        if which("brew"):
            log.debug("Installing kind with brew...")
            subproc(['brew install kind'], spinner=True)
        else:
            log.error("Sorry, you don't have brew installed. :( " + \
                      "Please install [b]kind[/b] and run smol-k8s-lab again")
            exit()

    log.debug("Creating a kind cluster...")

    kind_cfg = path.join(XDG_CACHE_DIR, 'kind_cfg.yaml')
    build_kind_config(kind_cfg, kubelet_args, networking_args,
                      control_plane_nodes, worker_nodes)

    cmd = f"kind create cluster --name {cluster_name} --config={kind_cfg}"
    subproc([cmd])

    return True


def delete_kind_cluster(cluster_name: str = "smol-k8s-lab") -> True:
    """
    delete kind cluster by name, if kind exists
    returns True
    """
    er = "smol-k8s-lab hasn't installed a [green]kind[/green] cluster here yet"
    if which('kind'):
        if cluster_name in subproc(['kind get clusters']):
            subproc([f'kind delete cluster --name {cluster_name}'])
        else:
            sub_header(er, False, False)
    else:
        log.debug("Kind is not installed.")
        sub_header("Kind is not installed.", False, False)

    return True


def build_kind_config(cfg_file: str = "~/.config/smol-k8s-lab/kind_cfg.yaml",
                      kubelet_extra_args: dict = {},
                      networking_args: dict = {},
                      control_plane_nodes: int = 1,
                      worker_nodes: int = 0) -> None:
    """
    builds a kind config including any extra kubelet or networking args and then
    writes it to a yaml in our cache dir
    """
    node_config = {'role': 'control-plane',
                   'extraPortMappings': [
                       {'containerPort': 80,
                         'hostPort': 80,
                         'protocol': 'TCP'},
                       {'containerPort': 443,
                        'hostPort': 443,
                        'protocol': 'TCP'}
                       ]
                   }

    if kubelet_extra_args:
        for arg, value in kubelet_extra_args.items():
            kubelet_extra_args[arg] = f'"{value}"'

        # adding any extra kubelet args you'd like to the kind node
        kube_adm_config = {
                'kind': 'InitConfiguration',
                'nodeRegistration': {
                    'kubeletExtraArgs': kubelet_extra_args
                    }
                }

        # only add extra kubelet args if any were passed in
        node_config['kubeadmConfigPatches'] = [
                pss(safe_yaml.dump_to_string(kube_adm_config)).replace("'","")
                ]

    kind_cfg = {
            'kind': 'Cluster',
            'apiVersion': 'kind.x-k8s.io/v1alpha4',
            'name': 'smol-k8s-lab-kind',
            'nodes': [node_config.copy()]
            }

    # if networking args were passed in
    if networking_args:
        kind_cfg["networking"] = networking_args.copy()

    # if we're testing more than one control plane node
    if control_plane_nodes > 1:
        for node in range(control_plane_nodes):
            kind_cfg['nodes'].append(node_config)

    # if we're testing more than one worker node
    if worker_nodes > 0:
        worker_config = node_config
        worker_config['role'] = 'worker'
        for node in range(worker_nodes):
            kind_cfg['nodes'].append(worker_config)

    # this creates a kind_cfg.yaml from the kind_cfg dict above
    with open(cfg_file, 'w') as kind_config_file:
        yaml.dump(kind_cfg, kind_config_file)
