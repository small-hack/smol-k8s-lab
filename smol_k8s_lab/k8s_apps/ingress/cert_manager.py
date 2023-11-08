#!/usr/bin/env python3.11
"""
       Name: cert_manager
DESCRIPTION: helm install, and optionally configure, cert manager
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from smol_k8s_lab.k8s_tools.helm import Helm
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
import logging as log


def configure_cert_manager(k8s_obj: K8s, email_addr: str = "") -> None:
    """
    Installs cert-manager helm chart and optionally creates letsencrypt acme
    ClusterIssuers for both staging and production if email_addr is passed in
    """

    # install chart and wait
    release = Helm.chart(release_name='cert-manager',
                         chart_name='jetstack/cert-manager',
                         namespace='cert-manager',
                         set_options={'installCRDs': 'true'})
    release.install(True)

    if email_addr:
        log.info("Creating ClusterIssuers for staging and production.")
        # we create a ClusterIssuer for both staging and prod
        acme_staging = "https://acme-staging-v02.api.letsencrypt.org/directory"
        private_key_ref = "letsencrypt-staging"
        for issuer in ['letsencrypt-staging', 'letsencrypt-prod']:
            if issuer == "letsencrypt-prod":
                acme_staging = acme_staging.replace("staging-", "")
                private_key_ref = private_key_ref.replace("-staging", "-prod")
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
            k8s_obj.apply_custom_resources([issuers_dict])
