#!/usr/bin/env python3.11
"""
       Name: cert_manager
DESCRIPTION: helm install, and optionally configure, cert manager
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from smol_k8s_lab.k8s_tools.helm import Helm
from smol_k8s_lab.k8s_tools.argocd_util import ArgoCD
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.bitwarden.bw_cli import BwCLI
from smol_k8s_lab.utils.value_from import extract_secret
import logging as log


def configure_cert_manager(k8s_obj: K8s) -> None:
    """
    Installs cert-manager helm chart and optionally creates letsencrypt acme
    ClusterIssuers for both staging and production if email_addr is passed in
    """

    # install chart and wait
    release = Helm.chart(release_name='cert-manager',
                         chart_name='jetstack/cert-manager',
                         namespace='cert-manager',
                         set_options={'installCRDs': 'true'})
    release.install(wait=True)


def create_cluster_issuers(init_values: dict,
                           k8s_obj: K8s = None,
                           argocd: ArgoCD = None,
                           bw: BwCLI = None) -> None:
    """
    create ClusterIssuers for cert manager
    """
    solver = init_values.get('cluster_issuer_acme_challenge_solver',
                             "http01").lower()
    if solver == "dns01":
        # create the cloudflare api token secret
        provider = init_values.get("cluster_issuer_acme_dns01_provider", "")
        if provider == "cloudflare":
            token = extract_secret(init_values['cloudflare_api_token'])
            if not bw and not argocd:
                k8s_obj.create_secret("cloudflare-api-token",
                                      "cert-manager",
                                      {"token": token})
            else:
                token_id = bw.create_login(
                        name="cert-manager-cloudflare-api-token",
                        item_url="certmanager",
                        password=token
                        )

                if argocd:
                    argocd.update_appset_secret(
                            {'cert_manager_cloudflare_api_token': token_id}
                            )

            challenge = {"cloudflare": {
                            "apiTokenSecretRef": {
                                "name": "cloudflare-api-token",
                                "key": "token"
                                }
                            }
                        }
        else:
            log.error("We currently only support cloudflare as the DNS "
                      "provider for the ACME Issuer type in cert-manager. "
                      f"If you'd like to see {provider} supported, please "
                      "submit a PR and we'll take a look!")
    else:
        challenge = {'ingress': {'class': 'nginx'}}

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
                'acme': {
                    'email':  init_values['email'],
                    'server': acme_staging,
                    'privateKeySecretRef': {'name': private_key_ref},
                    'solvers': [{solver: challenge}]
                    }
                }
            }

        # backup plan till above issue is resolved
        k8s_obj.apply_custom_resources([issuers_dict])
