#!/usr/bin/env python3.11
"""
       Name: keycloak 
DESCRIPTION: configure keycloak 
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from ..k8s_tools.homelabHelm import helm


def configure_keycloak():
    """
    installs keycloak helm chart
    """

    # install chart and wait
    release = helm.chart(release_name='keycloak',
                         chart_name='keycloak',
                         chart_version="1.12.0",
                         namespace='keycloak')
    release.install(True)

    return True
