#!/usr/bin/env python3.11
"""
       Name: external_secrets
DESCRIPTION: configures external secrets, currently only with gitlab
             hopefully with more supported providers in the future
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from ..k8s_tools.homelabHelm import helm
from ..k8s_tools.kubernetes_util import apply_custom_resources
from ..subproc import subproc
from ..console_logging import header


def configure_external_secrets(external_secrets_config):
    """
    configure external secrets and provider. currently only works with gitlab
    Accepts dict as arg:
    dict = {'namespace': 'somenamespace', 'access_token': 'tokenhere'}
    """

    header("Installing External Secrets Operator...")
    release = helm.chart(release_name='external-secrets-operator',
                         chart_name='external-secrets/external-secrets',
                         chart_version='0.6.1',
                         namespace='external-secrets')
    release.install(True)

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
    return
