#!/usr/bin/env python3.11
"""
       Name: external_secrets
DESCRIPTION: configures external secrets, currently only with gitlab
             hopefully with more supported providers in the future
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from ..pretty_printing.console_logging import header, sub_header
from ..k8s_tools.argocd import install_with_argocd
from ..k8s_tools.k8s_lib import K8s
from ..k8s_tools.kubernetes_util import apply_custom_resources
from ..subproc import subproc
from ..utils.bw_cli import BwCLI


def configure_external_secrets(k8s_obj: K8s,
                               eso_argo_dict: dict = {},
                               bweso_dict: dict = {},
                               bitwarden: BwCLI = None) -> True:
    """
    configure external secrets and provider. (and optionally bweso)
    """
    header("🤫 Installing External Secrets Operator...")
    install_with_argocd('external-secrets-operator', eso_argo_dict)

    if bweso_dict['enabled']:
        setup_bweso(k8s_obj, bweso_dict['argo'], bitwarden)
    return True


def setup_bweso(k8s_obj: K8s, bweso_argo_dict: dict = {},
                bitwarden: BwCLI() = BwCLI()):
    """
    Creates an initial secret for use with the bitwarden provider for ESO
    """
    sub_header("Installing the Bitwarden External Secrets Provider...")
    bw_client_id = bitwarden.clientID
    bw_client_secret = bitwarden.clientSecret
    bw_host = bitwarden.host
    bw_pass = bitwarden.pw

    # this is a standard k8s secrets yaml
    k8s_obj.create_secret('bweso-login', 'external-secrets',
                          {"BW_PASSWORD": bw_pass,
                           "BW_CLIENTSECRET": bw_client_secret,
                           "BW_CLIENTID": bw_client_id,
                           "BW_HOST": bw_host})
    return True


def setup_gitlab_provider(external_secrets_config: dict = {}):
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
