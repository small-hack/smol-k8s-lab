#!/usr/bin/env python3.11
"""
       Name: kyverno
DESCRIPTION: install kyverno, a security policy manager for k8s
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from ..k8s_tools.homelabHelm import helm


def install_kyverno():
    """
    does a helm install of kyverno
    """
    release = helm.chart(release_name='kyverno',
                         chart_name='kyverno/kyverno',
                         namespace='kyverno')
    release.install()
    return True
