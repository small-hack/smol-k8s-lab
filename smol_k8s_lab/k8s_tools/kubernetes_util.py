#!/usr/bin/env python3.11
"""
       Name: kubernetes_util
DESCRIPTION: generic kubernetes utilities
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""

from base64 import b64decode as b64dec
from base64 import standard_b64encode as b64enc
from os import path
from yaml import dump, safe_load
import logging as log
from .k8s_lib import K8s
from ..constants import XDG_CACHE_DIR
from ..utils.subproc import subproc, simple_loading_bar


def apply_manifests(manifest_file_name: str,
                    namespace: str = "default",
                    deployment: str = "",
                    selector: str = "component=controller"):
    """
    applies a manifest and waits with a nice loading bar if deployment
    """
    cmds = [f"kubectl apply --wait -f {manifest_file_name}"]

    if deployment:
        # these commands let us monitor a deployment rollout
        cmds.append(f"kubectl rollout status -n {namespace} "
                   f"deployment/{deployment}")

        cmds.append("kubectl wait --for=condition=ready pod --selector="
                   f"{selector} --timeout=90s -n {namespace}")

    # loops with progress bar until this succeeds
    subproc(cmds)
    return True


def apply_custom_resources(custom_resource_dict_list: dict):
    """
    Does a kube apply on a custom resource dict, and retries if it fails
    using loading bar for progress
    """
    k_cmd = 'kubectl apply --wait -f '
    commands = {}
    log.debug(custom_resource_dict_list)

    # Write YAML data to f'{XDG_CACHE_DIR}/{resource_name}.yaml'.
    for custom_resource_dict in custom_resource_dict_list:
        resource_name = "_".join([custom_resource_dict['kind'],
                                  custom_resource_dict['metadata']['name']])
        yaml_file_name = path.join(XDG_CACHE_DIR, f'{resource_name}.yaml')
        with open(yaml_file_name, 'w') as cr_file:
            dump(custom_resource_dict, cr_file)
        commands[f'Installing {resource_name}'] = k_cmd + yaml_file_name

    # loops with progress bar until this succeeds
    simple_loading_bar(commands)


def update_secret_key(k8s_obj: K8s,
                      secret_name: str,
                      secret_namespace: str,
                      updated_values_dict: dict,
                      in_line_key_name: str = 'secret_vars.yaml') -> True:
    """
    update a key in a k8s secret
    if in_line_key_name is set to a key name, you can specify a base key in a
    secret that contains an inline yaml block
    """
    secret_data = k8s_obj.get_secret(secret_name, secret_namespace)['data']
    log.debug(secret_data)

    # if this is a secret with a filename key and then inline yaml inside...
    if in_line_key_name:
        file_key = secret_data[in_line_key_name]
        decoded_data  = b64dec(str.encode(file_key)).decode('utf8')
        # load the yaml as a python dictionary
        in_line_yaml = safe_load(decoded_data)
        # for each key, updated_value in updated_values_dict
        for key, updated_value in updated_values_dict.items():
           # update the in-line yaml
           in_line_yaml[key] = updated_value
        k8s_obj.delete_secret(secret_name, secret_namespace)
        # update the inline yaml for the dict we'll feed back to
        k8s_obj.create_secret(secret_name,
                              secret_namespace,
                              in_line_yaml,
                              in_line_key_name)
    else:
        for key, updated_value in updated_values_dict.items():
           # update the keys in the secret yaml one by one
           secret_data[key] = b64enc(bytes(updated_value))
        k8s_obj.delete_secret(secret_name, secret_namespace)
        k8s_obj.create_secret(secret_name, secret_namespace, secret_data)
    return True
