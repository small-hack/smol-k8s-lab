#!/usr/bin/env python3.11
"""
       Name: cilium
DESCRIPTION: configures cilium
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
import logging as log
from smol_k8s_lab.k8s_tools.helm import Helm


def configure_cilium():
    """
    installs cilium from the manifests in their official repo

    """
    log.info("Installing Cilium now")

    # install chart and wait
    release = Helm.chart(release_name='cilium',
                         chart_name='cilium/cilium',
                         chart_version="1.14.1",
                         namespace='cilium',
                         set_options={'operator.replicas': 1})
    release.install(True)

    return True
