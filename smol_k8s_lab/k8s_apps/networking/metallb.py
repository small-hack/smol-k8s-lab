#!/usr/bin/env python3.11
"""
       Name: metallb
DESCRIPTION: configures metallb
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
import logging as log
from smol_k8s_lab.k8s_tools.kubernetes_util import (apply_custom_resources,
                                                    apply_manifests)


def configure_metallb(address_pool: list = []):
    """
    installs metallb from the manifests in their official repo

    Optionally accepts address_pool arg, list of ip addresses or CIDRs to create
    an IPaddressPool and L2Advertisement. If address_pool is not passed in or
    is "", then we don't create IPaddressPool or L2Advertisement
    """
    url = ("https://raw.githubusercontent.com/metallb/metallb/v0.13.11/config/"
           "manifests/metallb-native.yaml")

    # install manifest and wait
    apply_manifests(url, "metallb-system", "controller",
                    "component=controller")

    if address_pool:
        # metallb requires a address pool configured and a layer 2 advertisement CR
        log.info("Installing IPAddressPool and L2Advertisement custom resources.")

        ip_pool_cr = {'apiVersion': 'metallb.io/v1beta1',
                      'kind': 'IPAddressPool',
                      'metadata': {'name': 'default',
                                   'namespace': 'metallb-system'},
                      'spec': {'addresses': address_pool}}

        l2_advert_cr = {'apiVersion': 'metallb.io/v1beta1',
                        'kind': 'L2Advertisement',
                        'metadata': {'name': 'default',
                                     'namespace': 'metallb-system'}}

        apply_custom_resources([ip_pool_cr, l2_advert_cr])

    return True
