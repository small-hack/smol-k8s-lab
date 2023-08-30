#!/usr/bin/env python3.11
"""
       Name: external_secrets
DESCRIPTION: configures external secrets, currently only with gitlab
             hopefully with more supported providers in the future
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
import logging as log
from smol_k8s_lab.k8s_tools.argocd_util import install_with_argocd, wait_for_argocd_app
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.k8s_tools.kubernetes_util import apply_custom_resources
from smol_k8s_lab.utils.bw_cli import BwCLI
from smol_k8s_lab.utils.pretty_printing.console_logging import sub_header
from smol_k8s_lab.utils.subproc import subproc


def configure_external_secrets(k8s_obj: K8s,
                               eso_dict: dict,
                               bweso_dict: dict = {},
                               distro: str = "",
                               bitwarden: BwCLI = None) -> True:
    """
    configure external secrets and provider. (and optionally bweso)
    """
    install_with_argocd(k8s_obj, 'external-secrets-operator', eso_dict['argo'])
    wait_for_argocd_app('external-secrets-operator')

    if bweso_dict['enabled']:
        setup_bweso(k8s_obj, distro, bweso_dict['argo'], bitwarden)
    return True


def setup_bweso(k8s_obj: K8s,
                distro: str,
                bweso_argo_dict: dict = {},
                bitwarden: BwCLI = None):
    """
    Creates an initial secret for use with the bitwarden provider for ESO
    """
    sub_header("Installing the Bitwarden External Secrets Provider...")

    # this is a standard k8s secrets yaml
    k8s_obj.create_secret('bweso-login', 'external-secrets',
                          {"BW_PASSWORD": bitwarden.password,
                           "BW_CLIENTSECRET": bitwarden.client_secret,
                           "BW_CLIENTID": bitwarden.client_id,
                           "BW_HOST": bitwarden.host})

    if distro == 'kind':
        image = "docker.io/jessebot/bweso:v0.2.0"
        cmds = [f"docker pull --platform=linux/amd64 {image}",
                f"kind load docker-image {image} --name smol-k8s-lab-kind"]
        subproc(cmds)

    if bweso_argo_dict.get('part_of_app_of_apps', None):
        log.debug("Looks like this app is actually part of an app of apps "
                  "that will be deployed")
        return True

    install_with_argocd(k8s_obj, 'bitwarden-eso-provider', bweso_argo_dict)
    return True


def setup_gitlab_provider(external_secrets_config: dict):
    """
    setup the gitlab external secrets operator config
    Accepts dict as arg:
    dict = {'namespace': 'somenamespace', 'access_token': 'tokenhere'}
    """
    gitlab_access_token = external_secrets_config['access_token']
    gitlab_namespace = external_secrets_config['namespace']

    # create the namespace if does not exist
    subproc([f'kubectl create namespace {gitlab_namespace}'], error_ok=True)

    # this currently only works with gitlab
    gitlab_secret = {'apiVersion': 'v1',
                     'kind': 'Secret',
                     'metadata': {'name': 'gitlab-secret',
                                  'namespace': gitlab_namespace,
                                  'labels': {'type': 'gitlab'}},
                     'type': 'Opaque',
                     'stringData': {'token': gitlab_access_token}}

    apply_custom_resources([gitlab_secret])
