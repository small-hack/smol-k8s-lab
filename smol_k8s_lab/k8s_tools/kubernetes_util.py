#!/usr/bin/env python3.11
"""
       Name: kubernetes_util
DESCRIPTION: generic kubernetes utilities
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""

from os import path
from yaml import dump
from ..env_config import XDG_CACHE_DIR
from ..subproc import subproc, simple_loading_bar


def apply_manifests(manifest_file_name="", namespace="default", deployment="",
                    selector="component=controller"):
    """
    applies a manifest and waits with a nice loading bar
    """
    apply = f"kubectl apply --wait -f {manifest_file_name}"

    rollout = f"kubectl rollout status -n {namespace} deployment/{deployment}"

    wait = (f"kubectl wait --for=condition=ready pod --selector={selector} "
            f"--timeout=90s -n {namespace}")

    # loops with progress bar until this succeeds
    subproc([apply, rollout, wait])
    return True


def apply_custom_resources(custom_resource_dict_list):
    """
    Does a kube apply on a custom resource dict, and retries if it fails
    using loading bar for progress
    """
    k_cmd = 'kubectl apply --wait -f '
    commands = {}

    # Write YAML data to '{XDG_CACHE_DIR}/{resource_name}.yaml'.
    for custom_resource_dict in custom_resource_dict_list:
        resource_name = "_".join([custom_resource_dict['kind'],
                                  custom_resource_dict['metadata']['name']])
        yaml_file_name = path.join(XDG_CACHE_DIR, f'{resource_name}.yaml')
        with open(yaml_file_name, 'w') as cr_file:
            dump(custom_resource_dict, cr_file)
        commands[f'Installing {resource_name}'] = k_cmd + yaml_file_name

    # loops with progress bar until this succeeds
    simple_loading_bar(commands)
