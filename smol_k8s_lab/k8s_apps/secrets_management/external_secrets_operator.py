#!/usr/bin/env python3.11
"""
       Name: external_secrets
DESCRIPTION: configures external secrets, currently only with Bitwarden and GitLab
             hopefully with more supported providers in the future
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from smol_k8s_lab.bitwarden.bw_cli import BwCLI
from smol_k8s_lab.k8s_tools.argocd_util import install_with_argocd, wait_for_argocd_app
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.utils.subproc import subproc


def configure_external_secrets(k8s_obj: K8s,
                               eso_dict: dict,
                               eso_provider: str = "",
                               distro: str = "",
                               bitwarden: BwCLI = None) -> None:
    """
    configure external secrets and provider. (and optionally bweso or gitlab)
    """
    k8s_obj.create_namespace("external-secrets")

    if eso_provider == "bitwarden":
        setup_bweso_provider(k8s_obj, distro, bitwarden)
    elif eso_provider == "gitlab":
        setup_gitlab_provider(k8s_obj, eso_dict['init']['values']['gitlab_access_token'])

    install_with_argocd(k8s_obj, 'external-secrets-operator', eso_dict['argo'])
    wait_for_argocd_app('external-secrets-operator')

    if bitwarden:
        # wait for bitwarden external secrets provider to be up
        wait_for_argocd_app('bitwarden-eso-provider', retry=True)


def setup_bweso_provider(k8s_obj: K8s, distro: str, bitwarden: BwCLI = None) -> None:
    """
    Creates an initial secret for use with the bitwarden provider for ESO
    """
    # this is a standard k8s secrets yaml
    k8s_obj.create_secret('bweso-login',
                          'external-secrets',
                          {"BW_PASSWORD": bitwarden.password,
                           "BW_CLIENTSECRET": bitwarden.client_secret,
                           "BW_CLIENTID": bitwarden.client_id,
                           "BW_APPID": "external-secrets-operator-bitwarden-provider",
                           "BW_HOST": bitwarden.host})

    if distro == 'kind':
        image = "docker.io/jessebot/bweso:v0.4.0"
        cmds = [f"docker pull --platform=linux/amd64 {image}",
                f"kind load docker-image {image} --name smol-k8s-lab-kind"]
        subproc(cmds)


def setup_gitlab_provider(k8s_obj: K8s, gitlab_access_token: str) -> None:
    """
    setup the GitLab external secrets operator provider config by creating a
    secret with the GitLab access token
    """
    k8s_obj.create_secret('gitlab-secret',
                          'external-secrets',
                          {'token': gitlab_access_token})
