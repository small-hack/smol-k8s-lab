#!/usr/bin/env python3.11
"""
       Name: argocd
DESCRIPTION: configure argocd
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
import bcrypt
import logging as log
from os import path
import yaml
from ..constants import XDG_CACHE_DIR
from ..k8s_tools.argocd_util import ArgoCD
from ..k8s_tools.helm import Helm
from ..k8s_tools.k8s_lib import K8s
from ..bitwarden.bw_cli import BwCLI
from ..utils.passwords import create_password
from ..utils.rich_cli.console_logging import header, sub_header


def configure_argocd(k8s_obj: K8s,
                     argocd_config_dict: dict = {},
                     secret_dict: dict = {},
                     bitwarden: BwCLI = None) -> ArgoCD:
    """
    Installs argocd with ingress enabled by default and puts admin pass in a
    password manager, currently only bitwarden is supported
    arg:
      k8s_obj:                K8s() object with the kubernetes context
      bitwarden:              BwCLI() object, defaults to None
      plugin_secret_creation: boolean for creating the plugin secret generator
      secret_dict:            set of secrets to create for secret plugin
    """
    header("Installing [green]Argo CD[/green] for managing your Kubernetes apps",
           "🦑")

    namespace = argocd_config_dict['argo']['namespace']
    # this is needed for helm but also setting argo to use the current k8s context
    argo_cd_domain = secret_dict['argo_cd_hostname']

    # immediately start building helm object to check if helm release exists
    release_dict = {"release_name": "argo-cd", "namespace": namespace}
    release = Helm.chart(**release_dict)

    if not release.check_existing():
        # this is the base python dict for the values.yaml that is created below
        val = {"fullnameOverride": "argo-cd",
               "dex": {"enabled": False},
               "configs": {
                   "secret": {"argocdServerAdminPassword": ""}
                   },
               "server": {
                   "ingress": {
                       "enabled": True,
                       "hostname": argo_cd_domain,
                       "annotations": {
                           "nginx.ingress.kubernetes.io/backend-protocol": "HTTPS",
                           "kubernetes.io/tls-acme": True,
                           "nginx.ingress.kubernetes.io/ssl-passthrough": True,
                       },
                       "ingressClassName": "nginx",
                       "https": True,
                       "tls":  [{"secretName": "argocd-secret",
                                 "hosts": [argo_cd_domain]}]}}}

        # TODO: add this to dict if debug logging is enabled for smol-k8s-lab:
        # "global": {"logging": {"level": "debug"}}

        if secret_dict.get('global_cluster_issuer', None):
            val['server']['ingress']['annotations']['cert-manager.io/cluster-issuer'] = secret_dict['global_cluster_issuer']

        # if we're using bitwarden, generate a password & save it
        if bitwarden:
            sub_header(":lock: Creating a new password in BitWarden.")
            # if we're using bitwarden...
            argo_password = bitwarden.generate()
            bitwarden.create_login(name="argo-cd-admin-credentials",
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

        release = Helm.chart(**release_dict)
        release.install(wait=True)

    argocd = ArgoCD(namespace, argo_cd_domain, k8s_obj)

    # install the appset secret plugin generator if we're using that
    if "github.com/small-hack/argocd-apps" in argocd_config_dict['argo']['repo']:
        if argocd_config_dict['argo']['directory_recursion']:
            configure_secret_plugin_generator(argocd,
                                              argocd_config_dict,
                                              secret_dict)
    return argocd


def configure_secret_plugin_generator(argocd: ArgoCD,
                                      argocd_config: dict,
                                      secret_dict: dict) -> None:
    """
    configures the applicationset secret plugin generator

    (._. ) <-- who are they?
    """
    if not argocd.check_if_app_exists('appset-secrets-plugin'):
        # creates the secret vars secret with all the key/values for each appset
        argocd.k8s.create_secret('appset-secret-vars', 'argocd', secret_dict,
                                 'secret_vars.yaml')

        msg = "🔌 Installing the ApplicationSet Secret Plugin Generator for Argo CD..."
        sub_header(msg)

        # creates only the token for authentication
        token = create_password()
        argocd.k8s.create_secret('appset-secret-token', 'argocd', {'token': token})

        # this creates a values.yaml from this dict
        set_opts = {'secretVars.existingSecret': 'appset-secret-vars',
                    'token.existingSecret': 'appset-secret-token'}

        # install the helm chart :)
        release = Helm.chart(
                release_name='appset-secret-plugin',
                chart_name='appset-secret-plugin/appset-secret-plugin',
                namespace='argocd',
                set_options=set_opts
                )
        release.install(wait=True)

        # gotta make sure the project already exists
        log.info("Creating argocd project if it does not exist...")

        # get project namespaces
        proj_ns = argocd_config['argo']['project']['destination']['namespaces']
        if argocd.namespace not in proj_ns:
            proj_ns.append(argocd.namespace)

        # create argocd project
        argocd.create_project(argocd_config['argo']['project']['name'],
                              "Argo CD",
                              proj_ns,
                              argocd_config['argo']['cluster'],
                              set(argocd_config['argo']['project']['source_repos']))

        # immediately install the argocd appset plugin
        log.info("Immediately installing the appset secret plugin via Argo CD")
        repo_url = argocd_config['argo']['repo'].replace("https://","").replace("http://","")
        url_sections = repo_url.replace("github.com/", "").split('/')
        owner = url_sections[0]
        repo_name = url_sections[1].replace(".git", "")
        ref = argocd_config['argo']['revision']
        path = argocd_config['argo']['path']
        if not path.endswith("/"):
            path += "/"

        appset_secrets_yaml = (
                f"https://raw.githubusercontent.com/{owner}/{repo_name}/"
                f"{ref}/{path}appset_secret_plugin/"
                "appset_secret_plugin_generator_argocd_app.yaml"
                )

        log.info(f"applying {appset_secrets_yaml}")
        argocd.k8s.apply_manifests(appset_secrets_yaml, argocd.namespace)
    else:
        log.info("Reloading deployment for Argo CD Appset Secret Plugin")
        argocd.update_appset_secret(secret_dict)
