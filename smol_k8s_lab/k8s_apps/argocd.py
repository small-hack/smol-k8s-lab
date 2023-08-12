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
from ..bw_cli import BwCLI
from ..console_logging import header, sub_header
from ..constants import XDG_CACHE_DIR
import k8s_tools
from ..k8s_tools.homelabHelm import helm
from ..k8s_tools.kubernetes_util import apply_manifests


def configure_argocd(argo_cd_domain="", bitwarden=None,
                     secret_creation=False, secret_dict={}):
    """
    Installs argocd with ingress enabled by default and puts admin pass in a
    password manager, currently only bitwarden is supported
    arg:
        argo_cd_domain:   str, defaults to "", required
        bitwarden: BwCLI() object, defaults to None

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
        argo_password = k8s_tools.create_password()

    admin_pass = bcrypt.hashpw(argo_password.encode('utf-8'),
                               bcrypt.gensalt()).decode()

    # this gets passed to the helm cli, but is bcrypted
    val['configs']['secret']['argocdServerAdminPassword'] = admin_pass

    # this creates a values.yaml from the val dict above
    values_file_name = path.join(XDG_CACHE_DIR, 'argocd_values.yaml')
    with open(values_file_name, 'w') as values_file:
        yaml.dump(val, values_file)

    release = helm.chart(release_name='argo-cd',
                         chart_name='argo-cd/argo-cd',
                         chart_version='5.43.2',
                         namespace='argocd',
                         values_file=values_file_name)
    release.install(True)

    if secret_creation:
        create_secrets(secret_dict)

        # this creates a values.yaml from this dict
        val = {'secretVars': {'existingSecret': 'appset-secret-vars'}}
        values_file_name = path.join(XDG_CACHE_DIR, 'appset_values.yaml')
        with open(values_file_name, 'w') as values_file:
            yaml.dump(val, values_file)

        # install the helm chart :)
        release = helm.chart(release_name='argocd-appset-secret-plugin',
                             chart_name='argocd-appset',
                             chart_version='0.2.0',
                             namespace='argocd',
                             values_file=values_file_name)
        release.install(True)

    return


# this lets us do multi line yaml values
yaml.SafeDumper.org_represent_str = yaml.SafeDumper.represent_str


# this too
def repr_str(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar(u'tag:yaml.org,2002:str', data,
                                       style='|')
    return dumper.org_represent_str(data)


def create_secrets(secret_dict: dict):
    """
    create a k8s secret accessible by Argo CD
    """
    # these are all app secrets we collected at the start of the script
    secret_keys = yaml.dump(secret_dict)

    # this is a standard k8s secrets yaml
    secret_yaml = {'apiVersion': 'v1',
                   'kind': 'Secret',
                   'metadata': {'name': 'appset-secret-vars',
                                'namespace': 'argocd'},
                   'stringData': {'secret_vars.yaml': secret_keys}}

    secrets_file_name = path.join(XDG_CACHE_DIR, 'secrets.yaml')

    # write out the file to be applied
    with open(secrets_file_name, 'w') as secret_file:
        yaml.safe_dump(secret_yaml, secret_file)

    apply_manifests(secrets_file_name)
    return
