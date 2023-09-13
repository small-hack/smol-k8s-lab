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
from ..constants import XDG_CACHE_DIR
from ..rich_cli.console_logging import sub_header
from ..utils.subproc import subproc


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

    build_kind_config()

    cmd = f"kind create cluster --name smol-k8s-lab-kind --config={full_path}"
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


def build_kind_config():
    """
    builds a kind config
    """
    if kubelet_args:
        cluster_config = {"kind": "ClusterConfiguration",
                          "apiServer": {"extraArgs": kubelet_args}}
        node_config = {"kubeadmConfigPatches": cluster_config}

    if disable_cni:
        disabled_default_cni = {"networking": {"disableDefaultCNI": True}}

    extra_args = {"node-labels": "ingress-ready=true"}
    kube_adm_config = {'kind': 'InitConfiguration',
                       'nodeRegistration': {'kubeletExtraArgs': extra_args}}
    kind_cfg = {'kind': 'Cluster',
                'apiVersion': 'kind.x-k8s.io/v1alpha4',
                'name': 'smol-k8s-lab-kind',
                'nodes': [
                    {'role': 'control-plane',
                     'kubeadmConfigPatches': [kube_adm_config],
                     'extraPortMappings': [
                         {'containerPort': 80,
                           'hostPort': 80,
                           'protocol': 'TCP'},
                         {'containerPort': 443,
                          'hostPort': 443,
                          'protocol': 'TCP'}
                         ]
                     }
                    ]
                }

    # this creates a values.yaml from the val dict above
    kind_config_file = path.join(XDG_CACHE_DIR, 'kind_config.yaml')
    with open(kind_config_file, 'w') as values_file:
        yaml.dump(val, values_file)

    return kind_config_file
