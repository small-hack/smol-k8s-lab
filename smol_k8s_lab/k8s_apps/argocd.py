#!/usr/bin/env python3.11
"""
       Name: argocd
DESCRIPTION: configure argocd
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
import bcrypt
from os import path
from yaml import dump
from ..bw_cli import BwCLI
from ..console_logging import header, sub_header
from ..env_config import XDG_CACHE_DIR
from ..k8s_tools.homelabHelm import helm


def configure_argocd(argo_cd_domain="", password_manager=False):
    """
    Installs argocd with ingress enabled by default and puts admin pass in a
    password manager, currently only bitwarden is supported
    arg:
        argo_cd_domain:   str, defaults to "", required
        password_manager: bool, defaults to False, optional

    """
    header("Installing 🦑 Argo CD...")

    # this is the base python dict for the values.yaml that is created below
    val = {'dex': {'enabled': False},
           'configs': {'secret': {'argocdServerAdminPassword': ""}},
           'server': {
               'ingress': {
                   'enabled': True,
                   'hosts': [argo_cd_domain],
                   'annotations': {
                       "kubernetes.io/ingress.class": "nginx",
                       "nginx.ingress.kubernetes.io/backend-protocol": "HTTPS",
                       "cert-manager.io/cluster-issuer": "letsencrypt-staging",
                       "kubernetes.io/tls-acme": True,
                       "nginx.ingress.kubernetes.io/ssl-passthrough": True,
                   },
                   'https': True,
                   'tls':  [{'secretName': 'argocd-secret',
                             'hosts': [argo_cd_domain]}]}}}

    # if we're using a password manager, generate a password & save it
    if password_manager:
        sub_header(":lock: Creating a new password in BitWarden.")
        # if we're using bitwarden...
        bw = BwCLI()
        bw.unlock()
        argo_password = bw.generate()
        bw.create_login(name=argo_cd_domain,
                        item_url=argo_cd_domain,
                        user="admin",
                        password=argo_password)
        bw.lock()
        admin_pass = bcrypt.hashpw(argo_password.encode('utf-8'),
                                   bcrypt.gensalt()).decode()

        # this gets passed to the helm cli, but is bcrypted
        val['configs']['secret']['argocdServerAdminPassword'] = admin_pass

    # this creates a values.yaml from from the val dict above
    values_file_name = path.join(XDG_CACHE_DIR, 'argocd_values.yaml')
    with open(values_file_name, 'w') as values_file:
        dump(val, values_file)

    release = helm.chart(release_name='argo-cd',
                         chart_name='argo-cd/argo-cd',
                         chart_version='5.16.2',
                         namespace='argocd',
                         values_file=values_file_name)
    release.install(True)
    return
