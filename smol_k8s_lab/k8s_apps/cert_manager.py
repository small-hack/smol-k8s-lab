#!/usr/bin/env python3.11
"""
       Name: cert_manager
DESCRIPTION: configure cert manager
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from ..k8s_tools.homelabHelm import helm
from ..k8s_tools.k8s_lib import K8s
from ..k8s_tools.kubernetes_util import apply_custom_resources


def configure_cert_manager(k8s_obj: K8s, email_addr: str = "") -> True:
    """
    Installs cert-manager helm chart and letsencrypt clusterIssuers for both
    staging and production
    """

    # install chart and wait
    release = helm.chart(release_name='cert-manager',
                         chart_name='jetstack/cert-manager',
                         chart_version="1.12.3",
                         namespace='ingress',
                         set_options={'installCRDs': 'true'})
    release.install(True)

    # we create a ClusterIssuer for both staging and prod
    acme_staging = "https://acme-staging-v02.api.letsencrypt.org/directory"
    for issuer in ['letsencrypt-staging', 'letsencrypt-prod']:
        if issuer == "letsencrypt-prod":
            acme_staging = acme_staging.replace("staging-", "")
        issuers_dict = {
            'apiVersion': "cert-manager.io/v1",
            'kind': 'ClusterIssuer',
            'metadata': {'name': issuer},
            'spec': {
                'acme': {'email': email_addr,
                         'server': acme_staging,
                         'privateKeySecretRef': {
                             'name': "letsencrypt-staging"
                             },
                             'solvers': [
                                 {'http01': {'ingress': {'class': 'nginx'}}}
                                 ]
                              }
                     }
            }

        # not working: https://github.com/kubernetes-client/python/issues/2103
        # k8s_obj.create_from_manifest_dict(api_group="cert-manager.io",
        #                                   api_version="v1",
        #                                   namespace='ingress',
        #                                   plural_obj_name='clusterissuers',
        #                                   manifest_dict=issuers_dict)

        # backup plan till above issue is resolved
        apply_custom_resources([issuers_dict])

    return True
