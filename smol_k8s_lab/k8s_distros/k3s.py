#!/usr/bin/env python3.11
"""
       Name: k3s
DESCRIPTION: install k3s :D not affiliated with rancher, suse, or k3s
     AUTHOR: @Jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
# local libraries
from ..constants import USER, KUBECONFIG
from ..constants import XDG_CACHE_DIR
from ..utils.subproc import subproc

# external libraries
import logging as log
from os import chmod, remove, path
import requests
import stat
from ruamel.yaml import YAML


def install_k3s_cluster(cluster_name: str,
                        extra_k3s_parameters: dict = {
                            "write-kubeconfig-mode": 700
                            }
                        ) -> None:
    """
    python installation for k3s, emulates curl -sfL https://get.k3s.io | sh -
    Notes: --flannel-backend=none will break k3s on metal
    """
    # always prepend k3s- to the beginning of the cluster name
    if not cluster_name.startswith("k3s-"):
        cluster_name = "k3s-" + cluster_name

    # download the k3s installer if we don't have it here already
    url = requests.get("https://get.k3s.io")
    k3s_installer_file = open("./install.sh", "wb")
    k3s_installer_file.write(url.content)
    k3s_installer_file.close()

    # make sure we can actually execute the script
    chmod("./install.sh", stat.S_IRWXU)

    # for creating a config file for k3s
    k3s_yaml_file = XDG_CACHE_DIR + '/k3s.yml'
    # install command to create k3s cluster (just one server, control plane, node)
    install_cmd = f'./install.sh --config {k3s_yaml_file}'

    config_dict = extra_k3s_parameters

    # write out the k3s config
    yaml = YAML()
    with open(k3s_yaml_file, 'w') as k3s_cfg:
        yaml.dump(config_dict, k3s_cfg)

    subproc([install_cmd], spinner=False)

    # adds our newly created cluster for k3s to the user's kubeconfig
    update_user_kubeconfig(cluster_name)

    # remove the script after we're done
    remove('./install.sh')


def uninstall_k3s(cluster_name: str) ->  str:
    """
    uninstall k3s and cleans up your kubeconfig as well
    returns True
    """
    log.debug("Uninstalling k3s")
    cmds = ["k3s-uninstall.sh",
            f"kubectl config delete-cluster {cluster_name}",
            f"kubectl config delete-context {cluster_name}",
            f"kubectl config delete-user {cluster_name}"]

    res = subproc(cmds, spinner=False, error_ok=True)

    if isinstance(res, list):
        return res.join('\n')
    else:
        return res


def update_user_kubeconfig(cluster_name: str = 'smol-k8s-lab-k3s') -> None:
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
    # also make sure the current context is set to the same cluster name
    k3s_kubecfg['current-context'] = cluster_name

    # if the kubeconfig already exists and is not empty, we update it
    if path.exists(KUBECONFIG):
        log.info(f"↑ Updating your KUBECONFIG: {KUBECONFIG}")
        with open(KUBECONFIG, 'r') as user_kubeconfig:
            try:
                existing_config = safe_yaml.load(user_kubeconfig)
            except Exception as e:
                log.error(e)

        if existing_config:
            for obj in ['clusters', 'users', 'contexts']:
                # if there is already an object array, just append our thing to that
                if existing_config.get(obj, None):
                    existing_config[obj].extend(k3s_kubecfg[obj])
                # if there is no object array or it is empty, create one with our thing in it
                else:
                    existing_config[obj] = k3s_kubecfg[obj]

            # update the current-context to ours :)
            existing_config['current-context'] = cluster_name

            # write back the updated user kubeconfig file
            with open(KUBECONFIG, 'w') as user_kubeconfig:
                yaml.dump(existing_config, user_kubeconfig)
        else:
            log.info("Looks like your KUBECONFIG is empty, we'll fill it in for you.")
            # write updated k3s kubeconfig with new names for context, cluster, user
            with open(KUBECONFIG, 'w') as user_kubeconfig:
                yaml.dump(k3s_kubecfg, user_kubeconfig)
    else:
        log.info(f"Creating your new {KUBECONFIG} ✨")

        # write updated k3s kubeconfig with new names for context, cluster, user
        with open(KUBECONFIG, 'w') as user_kubeconfig:
            yaml.dump(k3s_kubecfg, user_kubeconfig)

    # change the mode (permissions) of kubeconfig so that it doesn't complain
    # and change the owner to the current user running this script
    subproc([f'sudo chmod 600 {KUBECONFIG}',
             f'sudo chown {USER}: {KUBECONFIG}'])
