#!/usr/bin/env python3.11
"""
       Name: kubernetes_util
DESCRIPTION: generic kubernetes utilities
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""

from base64 import standard_b64encode as b64enc
from base64 import b64decode as b64dec
import json
from os import path, remove
import yaml
from yaml import dump
from ..constants import XDG_CACHE_DIR
from ..subproc import subproc, simple_loading_bar


def apply_manifests(manifest_file_name="", namespace="default", deployment="",
                    selector="component=controller"):
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


# this lets us do multi line yaml values
yaml.SafeDumper.org_represent_str = yaml.SafeDumper.represent_str


# this too
def repr_str(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar(u'tag:yaml.org,2002:str', data,
                                       style='|')
    return dumper.org_represent_str(data)


def create_secret(secret_name: str, secret_namespace: str, secret_dict: dict,
                  in_line: bool = False, additonal_labels: dict = None):
    """
    create a k8s secret accessible by Argo CD
    """

    # make sure the namespace we're installing into exists
    try:
        subproc([f"kubectl get namespace {secret_namespace}"])
    except Exception:
        subproc([f"kubectl create namespace {secret_namespace}"])

    if in_line:
        # these are all app secrets we collected at the start of the script
        secret_keys = yaml.dump(secret_dict)

        # this is a standard k8s secrets yaml
        secret_yaml = {'apiVersion': 'v1',
                       'kind': 'Secret',
                       'metadata': {'name': secret_name,
                                    'namespace': secret_namespace},
                       'stringData': {'secret_vars.yaml': secret_keys}}
    else:
        # base64 encode all the values
        for key, value in secret_dict.items():
            secret_dict[key] = b64enc(value)

        # this is a standard k8s secrets yaml
        secret_yaml = {'apiVersion': 'v1',
                       'kind': 'Secret',
                       'metadata': {'name': secret_name,
                                    'namespace': secret_namespace},
                       'data': secret_dict}

    if additonal_labels:
        secret_yaml['metadata']['labels'] = additonal_labels

    secrets_file_name = path.join(XDG_CACHE_DIR, f'secret-{secret_name}.yaml')

    # write out the file to be applied
    with open(secrets_file_name, 'w') as secret_file:
        yaml.safe_dump(secret_yaml, secret_file)

    apply_manifests(secrets_file_name)

    # clean up the secret, because we shouldn't keep that around
    remove(secrets_file_name)

    return True


def update_secret_key(secret_name: str, secret_namespace: str,
                      updated_values_dict: dict = {},
                      in_line: bool = False,
                      in_line_file_name: str = 'secret_vars.yaml'):
    """
    update a key in a k8s secret accessible by Argo CD
    if in_line is set to True, you can specify a base key in a secret that
    contains an inline yaml block
    """
    cm = f"kubectl get secret -n {secret_namespace} {secret_namespace} -o json"
    k8s_secret = json.loads(subproc([cm]))
    secret_data = k8s_secret['data']

    # if this is a secret with a filename key and then inline yaml inside...
    if in_line and in_line_file_name:
        # load the yaml as a python dictionary
        in_line_yaml = yaml.safe_load(b64dec(secret_data[in_line_file_name]))
        # for each key, updated_value in updated_values_dict
        for key, updated_value in updated_values_dict.items():
           # update the in-line yaml
           in_line_yaml[key] = updated_value
        # update the inline yaml for the dict we'll feed back to 
        k8s_secret['data'][in_line_file_name] = b64enc(yaml.dump(in_line_yaml))
    else:
        for key, updated_value in updated_values_dict.items():
           # update the keys in the secret yaml one by one
           secret_data[key] = b64enc(updated_value)
        k8s_secret['data'] = secret_data

    secrets_file_name = path.join(XDG_CACHE_DIR, f'secret-{secret_name}.yaml')
    # write out the file to be applied
    with open(secrets_file_name, 'w') as secret_file:
        yaml.safe_dump(k8s_secret, secret_file)

    # clean up the secret, because we shouldn't keep that around
    remove(secrets_file_name)

    return True
