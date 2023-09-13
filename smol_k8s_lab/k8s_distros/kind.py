#!/usr/bin/env python3.11
"""
       Name: kind
DESCRIPTION: create or delete a kind cluster, part of smol-k8s-lab
     AUTHOR: <https://github.com/jessebot>
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from ..constants import XDG_CACHE_DIR
from ..utils.rich_cli.console_logging import sub_header
from ..utils.subproc import subproc
import logging as log
from os import path
from shutil import which
from yaml import dump


def install_kind_cluster(kubelet_args: dict = {}, disable_cni: bool = False):
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

    kind_cfg = path.join(XDG_CACHE_DIR, 'kind_cfg.yaml')
    build_kind_config(kind_cfg)

    cmd = f"kind create cluster --name smol-k8s-lab-kind --config={kind_cfg}"
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


def build_kind_config(kind_cfg: str = "~/.config/smol-k8s-lab/kind_cfg.yaml",
                      kubelet_extra_args: dict = {},
                      networking_args: dict = {},
                      nodes: int = 1):
    """
    builds a kind config including any extra networking 
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
        # adding any extra kubelet args you'd like to the kind node
        kube_adm_config = {
                'kind': 'InitConfiguration',
                'nodeRegistration': {
                    'kubeletExtraArgs': kubelet_extra_args
                    }
                }

        # only add extra kubelet args if any were passed in
        node_config['kubeadmConfigPatches'] = [dump(kube_adm_config)]

    kind_cfg = {
            'kind': 'Cluster',
            'apiVersion': 'kind.x-k8s.io/v1alpha4',
            'name': 'smol-k8s-lab-kind',
            'nodes': [node_config]
            }

    # if networking args were passed in
    if networking_args:
        kind_cfg["networking"] = networking_args

    # if we're testing more than one node
    if nodes > 1:
        worker_config = node_config
        worker_config['role'] = 'worker'
        for node in range(nodes):
            kind_cfg['nodes'].append(worker_config)

    # this creates a kind_cfg.yaml from the kind_cfg dict above
    with open(kind_cfg, 'w') as kind_config_file:
        dump(kind_cfg, kind_config_file)

    return kind_config_file
