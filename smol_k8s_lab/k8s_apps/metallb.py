#!/usr/bin/env python3.11
"""
       Name: metallb
DESCRIPTION: configures metallb
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
import logging as log
from ..k8s_tools.kubernetes_util import apply_custom_resources, apply_manifests


def configure_metallb(address_pool: str = ""):
    """
    metallb is special because it has Custom Resources:
        IPaddressPool and L2Advertisement
    Requires and accepts one arg:
        address_pool - comma seperated list of IP addresses
    """
    url = ("https://raw.githubusercontent.com/metallb/metallb/v0.13.10/config/"
           "manifests/metallb-native.yaml")

    # install manifest and wait
    apply_manifests(url, "metallb-system", "controller",
                    "component=controller")

    # metallb requires a address pool configured and a layer 2 advertisement CR
    log.info("Installing IPAddressPool and L2Advertisement custom resources.")

    ip_pool_cr = {'apiVersion': 'metallb.io/v1beta1',
                  'kind': 'IPAddressPool',
                  'metadata': {'name': 'default',
                               'namespace': 'metallb-system'},
                  'spec': {'addresses': address_pool.split(',')}}

    l2_advert_cr = {'apiVersion': 'metallb.io/v1beta1',
                    'kind': 'L2Advertisement',
                    'metadata': {'name': 'default',
                                 'namespace': 'metallb-system'}}

    apply_custom_resources([ip_pool_cr, l2_advert_cr])
    return
