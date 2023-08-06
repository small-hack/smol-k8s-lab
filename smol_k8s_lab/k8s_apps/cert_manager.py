#!/usr/bin/env python3.11
"""
       Name: cert_manager
DESCRIPTION: configure cert manager
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from ..k8s_tools.homelabHelm import helm
from ..k8s_tools.kubernetes_util import apply_custom_resources


def configure_cert_manager(email_addr):
    """
    installs cert-manager helm chart and letsencrypt clusterissuers
    """

    # install chart and wait
    release = helm.chart(release_name='cert-manager',
                         chart_name='jetstack/cert-manager',
                         chart_version="1.12.3",
                         namespace='kube-system',
                         set_options={'installCRDs': 'true'})
    release.install(True)

    # we create a ClusterIssuer for both staging and prod
    issuers = []
    acme_staging = 'https://acme-staging-v02.api.letsencrypt.org/directory'
    for issuer in ['letsencrypt-prod', 'letsencrypt-staging']:
        if issuer == "letsencrypt-prod":
            acme_staging = acme_staging.replace("staging-", "")
        issuers.append({
            'apiVersion': 'cert-manager.io/v1',
            'kind': 'ClusterIssuer',
            'metadata': {'name': issuer},
            'spec': {'acme': {'email': email_addr,
                              'server': acme_staging,
                              'privateKeySecretRef': {
                                  'name': 'letsencrypt-staging'
                                  },
                              'solvers': [{'http01': {'ingress':
                                                      {'class': 'nginx'}}}]
                               }}})

    apply_custom_resources(issuers)
    return True
