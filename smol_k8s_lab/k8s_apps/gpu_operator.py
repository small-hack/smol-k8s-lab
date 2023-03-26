#!/usr/bin/env python3.11
"""
       Name: external_secrets
DESCRIPTION: configures external secrets, currently only with gitlab
             hopefully with more supported providers in the future
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from ..k8s_tools.homelabHelm import helm
# from ..k8s_tools.kubernetes_util import apply_custom_resources
from ..subproc import subproc
from ..console_logging import header


def configure_gpu_operator():
    """
    configure external secrets and provider. currently only works with gitlab
    """

    header("Installing GPU Operator...")
    release = helm.chart(release_name='gpu-operator',
                         chart_name='nvidia/gpu-operator',
                         namespace='gpu-operator')
                         # chart_version='',
    release.install(True)


    # create the namespace if does not exist
    subproc(['kubectl create namespace gpu-operator'], error_ok=True)

    # this currently only works with gitlab
    # gitlab_secret = {'apiVersion': 'v1',
    #                  'kind': 'Secret',
    #                  'metadata': {'name': 'gitlab-secret',
    #                               'namespace': gitlab_namespace,
    #                               'labels': {'type': 'gitlab'}},
    #                  'type': 'Opaque',
    #                  'stringData': {'token': gitlab_access_token}}
    # apply_custom_resources([gitlab_secret])
    return
