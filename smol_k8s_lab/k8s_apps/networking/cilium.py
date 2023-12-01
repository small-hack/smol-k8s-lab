#!/usr/bin/env python3.11
"""
       Name: cilium
DESCRIPTION: configures cilium
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
import logging as log
from smol_k8s_lab.k8s_tools.helm import Helm
from smol_k8s_lab.constants import XDG_CACHE_DIR
from os import path
import yaml


def configure_cilium(cilium_dict: dict):
    """
    installs cilium from the manifests in their official repo
    """
    log.info("Installing Cilium now")

    cilium_hostname = cilium_dict['argo']['secret_keys']['hostname']

    values = {"operator": {"replicas": 1},
              "hubble": {"relay": {"enabled": True},
                         "ui": {"enabled": True,
                                "ingress": {"enabled": True,
                                            "className": "nginx",
                                            "hosts": [cilium_hostname],
                                            "tls": [
                                                {"secretName": "cilium-tls",
                                                 "hosts": [cilium_hostname]}
                                                ]
                                            }
                                }
                         }
              }

    # this creates a values.yaml from the val dict above
    values_file_name = path.join(XDG_CACHE_DIR, 'cilium_values.yaml')
    with open(values_file_name, 'w') as values_file:
        yaml.dump(values, values_file)

    # install chart and wait
    release = Helm.chart(release_name='cilium',
                         chart_name='cilium/cilium',
                         namespace='cilium',
                         values_file=values_file_name)
    release.install(True)

    return True
