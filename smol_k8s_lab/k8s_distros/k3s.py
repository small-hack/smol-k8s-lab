#!/usr/bin/env python3.11
"""
       Name: k3s
DESCRIPTION: install k3s :D not affiliated with rancher, suse, or k3s
     AUTHOR: @Jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from ..constants import USER, KUBECONFIG
from ..constants import XDG_CACHE_DIR
from ..utils.subproc import subproc
import logging as log
import json
from os import chmod, remove, path
import requests
import stat
from ruamel.yaml import YAML


def install_k3s_cluster(cluster_name: str,
                        extra_k3s_cli_args: list = [],
                        kubelet_extra_args: dict = {}):
    """
    python installation for k3s, emulates curl -sfL https://get.k3s.io | sh -
    Notes: --flannel-backend=none will break k3s on metal
    """
    # download the k3s installer if we don't have it here already
    url = requests.get("https://get.k3s.io")
    k3s_installer_file = open("./install.sh", "wb")
    k3s_installer_file.write(url.content)
    k3s_installer_file.close()

    # make sure we can actually execute the script
    chmod("./install.sh", stat.S_IRWXU)

    # create the k3s cluster (just one server node)
    install_cmd = './install.sh --write-kubeconfig-mode=700'

    # add additional arguments to k3s if there are any
    if extra_k3s_cli_args:
        for argument in extra_k3s_cli_args:
            install_cmd += f" {argument}"

    # override the default kubelet config
    if kubelet_extra_args:
        # we'll edit this file before install: /etc/rancher/k3s/kubelet.config
        # so that we can change the max number of pods on this node
        kube_config = {'apiVersion': 'kubelet.config.k8s.io/v1beta1',
                       'kind': 'KubeletConfiguration'}

        kube_config = kube_config | kubelet_extra_args

        kube_cache = XDG_CACHE_DIR + '/kubelet.config'
        with open(kube_cache, 'w') as kubelet_cfg:
            json.dump(kube_config, kubelet_cfg)

        subproc(['sudo mkdir -p /etc/rancher/k3s',
                 f'sudo mv {kube_cache} /etc/rancher/k3s/kubelet.config'])

        install_cmd += ' --kubelet-arg=config=/etc/rancher/k3s/kubelet.config'

    subproc([install_cmd], spinner=False)

    # adds our newly created cluster for k3s to the user's kubeconfig
    update_user_kubeconfig(cluster_name)

    # remove the script after we're done
    remove('./install.sh')

    return True


def uninstall_k3s(context: dict = {}):
    """
    uninstall k3s and cleans up your kubeconfig as well
    returns True
    """
    log.debug("Uninstalling k3s")
    cmds = ["k3s-uninstall.sh",
            f"kubectl config delete-cluster {context['cluster']}",
            f"kubectl config delete-context {context['context']}",
            f"kubectl config delete-user {context['user']}"]

    subproc(cmds, spinner=False)

    return True


def update_user_kubeconfig(cluster_name: str = 'smol-k8s-lab-k3s'):
    """
    update the user's kubeconfig with the cluster, user, and context for the new 
    cluster by grabbing the k3s generated kubeconfig and using it to update your
    current kubeconfig. Handles both existing kubeconfig and none at all.

    cluster_name: string - the name you'd like to give to the cluster and context
    """
    safe_yaml = YAML(typ='safe')
    yaml = YAML()

    # Grab the kubeconfig and copy it locally
    k3s_yml = subproc(['sudo /bin/cat /etc/rancher/k3s/k3s.yaml'])
    k3s_kubecfg = safe_yaml.load(k3s_yml)

    # update name of cluster, user, and context from default to smol-k8s-lab-k3s
    k3s_kubecfg['clusters'][0]['name'] = cluster_name
    k3s_kubecfg['users'][0]['name'] = cluster_name
    k3s_kubecfg['contexts'][0]['name'] = cluster_name
    k3s_kubecfg['contexts'][0]['context']['cluster'] = cluster_name
    k3s_kubecfg['contexts'][0]['context']['user'] = cluster_name

    # if the kubeconfig already exists and is not empty, we update it
    if path.exists(KUBECONFIG):
        log.info(f"Updating your {KUBECONFIG} ↑")
        with open(KUBECONFIG, 'r') as user_kubeconfig:
            existing_config = safe_yaml.load(user_kubeconfig)

        if existing_config:
            # append new cluster, user and context
            existing_config['clusters'].extend(k3s_kubecfg['clusters'])
            existing_config['users'].extend(k3s_kubecfg['users'])
            existing_config['contexts'].extend(k3s_kubecfg['context'])

            # update the current-context to ours :)
            existing_config['current-context'] = cluster_name

            # write back the updated user kubeconfig file
            with open(KUBECONFIG, 'w') as user_kubeconfig:
                yaml.dump(existing_config, user_kubeconfig)
    else:
        log.info(f"Creating your new {KUBECONFIG} ✨")

        # write updated k3s kubeconfig with new names for context, cluster, user
        with open(KUBECONFIG, 'w') as user_kubeconfig:
            yaml.dump(k3s_kubecfg, user_kubeconfig)

    # change the mode (permissions) of kubeconfig so that it doesn't complain
    # and change the owner to the current user running this script
    subproc([f'sudo chmod 600 {KUBECONFIG}',
             f'sudo chown {USER}: {KUBECONFIG}'])
