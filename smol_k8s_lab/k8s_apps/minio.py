#!/usr/bin/env python3.11
"""
       Name: minio
DESCRIPTION: install minio, a local S3 compatible object store
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from ..k8s_tools.homelabHelm import helm


def install_kyverno():
    """
    does a helm install of minio
    """
    release = helm.chart(release_name='minio',
                         chart_name='minio/minio',
                         namespace='minio')
    release.install()
    return True
