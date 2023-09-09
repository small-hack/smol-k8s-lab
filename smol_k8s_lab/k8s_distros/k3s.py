#!/usr/bin/env python3.11
"""
       Name: k3s
DESCRIPTION: install k3s :D
     AUTHOR: @Jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
import logging as log
import json
from os import chmod, remove
import requests
import stat
from ..constants import USER, KUBECONFIG, XDG_CACHE_DIR
from ..utils.subproc import subproc


def install_k3s_cluster(disable_servicelb: bool,
                        cilium_enabled: bool,
                        additonal_arguments: list,
                        max_pods: int):
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

    # we will edit this file before the install: /etc/rancher/k3s/kubelet.config
    # so that we can change the max number of pods on this node
    kube_config = {'apiVersion': 'kubelet.config.k8s.io/v1beta1',
                   'kind': 'KubeletConfiguration',
                   'maxPods': max_pods}
    kube_cache = XDG_CACHE_DIR + '/kubelet.config'
    with open(kube_cache, 'w') as kubelet_cfg:
        json.dump(kube_config, kubelet_cfg)

    subproc(['sudo mkdir -p /etc/rancher/k3s',
             f'sudo mv {kube_cache} /etc/rancher/k3s/kubelet.config'])

    # create the k3s cluster (just one server node)
    cmd = ('./install.sh '
           '--disable=traefik '
           '--write-kubeconfig-mode=700 '
           '--secrets-encryption '
           '--kubelet-arg=config=/etc/rancher/k3s/kubelet.config')

    if disable_servicelb:
        cmd += ' --disable=servicelb'

    if cilium_enabled:
        cmd += ' --flannel-backend=none --disable-network-policy'

    # add additional arguments to k3s if there are any
    if additonal_arguments:
        for argument in additonal_arguments:
            cmd += f" {argument}"

    subproc([cmd], spinner=False)

    log.info(f"Updating your {KUBECONFIG}")

    k3s_kubeconfig = "/etc/rancher/k3s/k3s.yaml"
    # Grab the kubeconfig and copy it locally
    cp = f'sudo cp {k3s_kubeconfig} {KUBECONFIG}'

    # change the mode (permissions) of kubeconfig so that it doesn't complain
    chmod_cmd = f'sudo chmod 600 {KUBECONFIG}'
    # change the owner to the current user running this script
    chown_cmd = f'sudo chown {USER}: {KUBECONFIG}'

    # rename the cluster in your kubeconfig to smol-k8s-lab-k3s
    cluster_rename = "kubectl config rename-context default smol-k8s-lab-k3s"

    # run all 3 commands one after the other
    subproc([cp, chmod_cmd, chown_cmd, cluster_rename])

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
