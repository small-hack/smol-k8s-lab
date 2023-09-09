#!/usr/bin/env python3.11
"""
       Name: argocd
DESCRIPTION: configure argocd
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
import bcrypt
from os import path
import yaml
from ..constants import XDG_CACHE_DIR
from ..k8s_tools.helm import Helm
from ..k8s_tools.k8s_lib import K8s
from ..utils.bw_cli import BwCLI
from ..utils.subproc import subproc
from ..utils.passwords import create_password
from ..utils.pretty_printing.console_logging import header, sub_header


def configure_argocd(k8s_obj: K8s,
                     argo_cd_domain: str = "",
                     bitwarden: BwCLI = None,
                     plugin_secret_creation: bool = False,
                     secret_dict: dict = {}) -> True:
    """
    Installs argocd with ingress enabled by default and puts admin pass in a
    password manager, currently only bitwarden is supported
    arg:
      argo_cd_domain:          fqdn for argocd
      bitwarden:               BwCLI() object, defaults to None
      plugin_secret_creation:  boolean for creating the plugin secret generator
      secret_dict:             set of secrets to create for secret plugin
    """
    header("Installing [green]Argo CD[/green] for managing your Kubernetes apps",
           "🦑")
    release_dict = {'release_name': 'argo-cd', 'namespace': 'argocd'}

    release = Helm.chart(**release_dict)
    already_installed = release.check_existing()
    if not already_installed:
        # this is the base python dict for the values.yaml that is created below
        val = {'fullnameOverride': 'argo-cd',
               'dex': {'enabled': False},
               'configs': {
                   'secret': {'argocdServerAdminPassword': ""}
                   },
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

        # if we're using bitwarden, generate a password & save it
        if bitwarden:
            sub_header(":lock: Creating a new password in BitWarden.")
            # if we're using bitwarden...
            argo_password = bitwarden.generate()
            bitwarden.create_login(name=argo_cd_domain,
                                   item_url=argo_cd_domain,
                                   user="admin",
                                   password=argo_password)
        # if we're not using bitwarden, just create a password the normal way
        else:
            argo_password = create_password()

        admin_pass = bcrypt.hashpw(argo_password.encode('utf-8'),
                                   bcrypt.gensalt()).decode()

        # this gets passed to the helm cli, but is bcrypted
        val['configs']['secret']['argocdServerAdminPassword'] = admin_pass

        # this creates a values.yaml from the val dict above
        values_file_name = path.join(XDG_CACHE_DIR, 'argocd_values.yaml')
        with open(values_file_name, 'w') as values_file:
            yaml.dump(val, values_file)

        release_dict['values_file'] = values_file_name
        release_dict['chart_name'] = 'argo-cd/argo-cd'
        release_dict['chart_version'] = '5.46.0'

        release = Helm.chart(**release_dict)
        release.install(True)

    if plugin_secret_creation:
        configure_secret_plugin_generator(k8s_obj, secret_dict)

    # setup Argo CD to talk directly to k8s
    subproc(['kubectl config set-context --current --namespace=argocd',
             f'argocd login {argo_cd_domain} --core'])

    return True


def configure_secret_plugin_generator(k8s_obj: K8s, secret_dict: dict):
    """
    configures the applicationset secret plugin generator
    """
    msg = "🔌 Installing the ApplicationSet Secret Plugin Generator for Argo CD..."
    sub_header(msg)

    # creates the secret vars secret with all the key/values for each appset
    k8s_obj.create_secret('appset-secret-vars', 'argocd', secret_dict,
                          'secret_vars.yaml')

    token = create_password()

    # creates only the token for authentication
    k8s_obj.create_secret('appset-secret-token', 'argocd', {'token': token})

    # this creates a values.yaml from this dict
    set_opts = {'secretVars.existingSecret': 'appset-secret-vars',
                'token.existingSecret': 'appset-secret-token'}

    # install the helm chart :)
    chart_name = 'appset-secret-plugin/argocd-appset-secret-plugin'
    release = Helm.chart(release_name='argocd-appset-secret-plugin',
                         chart_name=chart_name,
                         chart_version='0.4.0',
                         namespace='argocd',
                         set_options=set_opts)
    release.install(True)
