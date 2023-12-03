#!/usr/bin/env python3
"""
AUTHOR: @jessebot
LICENSE: AGPLv4
"""

# internal libraries
from ..utils.subproc import subproc
from ..utils.rich_cli.console_logging import header, sub_header

# external libraries
from collections import OrderedDict
import logging as log
import requests
from ruamel.yaml import YAML
from shutil import which

# these are the URLs of each manually installed helm chart, so that the appset matches
APPSET_URLS = {
        "argo-cd": "https://raw.githubusercontent.com/small-hack/argocd-apps/main/argocd/app_of_apps/argocd_appset.yaml",
        "appset-secret-plugin": "https://raw.githubusercontent.com/small-hack/argocd-apps/main/argocd/app_of_apps/appset_secret_plugin/appset_secret_plugin_generator_argocd_app.yaml",
        "cert-manager": "https://raw.githubusercontent.com/small-hack/argocd-apps/main/cert-manager/cert-manager_argocd_app.yaml",
        "ingress-nginx": "https://raw.githubusercontent.com/small-hack/argocd-apps/main/ingress-nginx/ingress-nginx_argocd_app.yaml",
        "cilium": "https://raw.githubusercontent.com/small-hack/argocd-apps/main/alpha/cilium/cilium_argocd_appset.yaml"
        }


class Helm:
    """
    Local helm management of repos:
    use helm to add/remove/update repos and upgrade/(un)install charts
    """
    def __init__(self):
        """
        not sure what to put here
        """
        return

    class repo:
        """
        perform add, update, and removal of helm chart repos
        """
        def __init__(self, repo_dict: dict):
            """
            must pass in a repo_dict of {'repo_name': 'repo url'}
            """
            self.repo_dict = repo_dict

        def add(self):
            """
            helm repo add a dict of repos
            """
            cmds = []
            for repo_name, repo_url in self.repo_dict.items():
                cmds.append(f'helm repo add {repo_name} {repo_url}')

            # update any repos that are out of date
            cmds.append("helm repo update")

            # fire all of these off at once
            subproc(cmds)

        def remove(self):
            """
            helm repo remove
            """
            subproc([f'helm repo remove {self.repo_name}'])

    class chart:
        """
        installs/uninstalls a helm chart.
        """
        def __init__(self, **kwargs):
            """
            Takes key word args:
            release_name="", chart_name="", chart_version="", namespace="",
            values_file="", set_options={}
            order of operations: values file followed by --set options.
            """
            # for each keyword arg's key, create self.key for other methods
            # to reference e.g. pass in namespace='kube-system' and we create
            # self.namespace='kube-system'
            self.__dict__.update(kwargs)

            # always install into default namespace unless stated otherwise
            if not kwargs['namespace']:
                self.namespace = 'default'

        def check_existing(self,):
            """
            check if we already have an existing install
            """
            cmd = (f'helm list --short --filter {self.release_name} '
                   f' -n {self.namespace}')
            return subproc([cmd], quiet=True)


        def install(self, wait: bool = False) -> True:
            """
            Installs helm chart to current k8s context, takes optional wait arg
            Defaults to False, if True, will wait till deployments are up
            keyword args:
                - release_name:  str to call this installation
                - chart_name:    str of helm chart to use (repo/chart)
                - chart_version: version of the chart to install
                - namespace:     str of namespace to deploy release to
                - values_file:   str of a file to use with --values
                - set_options:   dict of key/values to be passed with --set
            """
            if self.check_existing():
                log.info(f"{self.release_name} is already installed :)")
                return True

            cmd = (f'helm upgrade {self.release_name} {self.chart_name}'
                   f' --install -n {self.namespace} --create-namespace')
            # f' --atomic')

            if self.__dict__.get('chart_version', False):
                cmd += f' --version {self.chart_version}'
            else:
                version = self.get_appset_version()
                cmd += f' --version {version}'

            if self.__dict__.get('values_file', False):
                cmd += f' --values {self.values_file}'

            if self.__dict__.get('set_options', False):
                for key, value in self.set_options.items():
                    cmd += f' --set {key}={value}'

            if wait:
                cmd += ' --wait --wait-for-jobs'

            subproc([cmd])
            return True

        def get_appset_version(self) -> str:
            """
            go get the version of the helm chart installed by the live appset
            """
            # get the contents of the remote url
            res = requests.get(APPSET_URLS[self.release_name]).text

            # use the ruamel.yaml library to load the yaml
            yaml = YAML()
            obj = yaml.load(res)

            # this is an app
            if obj['kind'] == "Application":
                return obj['spec']['source']['targetRevision']
            # this is an appset
            else:
                # return the current version of the app
                return obj['spec']['template']['spec']['source']['targetRevision']

        def uninstall(self):
            """
            Uninstalls a helm chart from the current k8s context
            """
            cmd = f'helm uninstall {self.release_name} -n {self.namespace}'
            subproc([cmd])
            return True


def add_default_repos(k8s_distro: str,
                      metallb: bool = False,
                      cilium: bool = False,
                      argo: bool = False,
                      argo_secrets: bool = False) -> None:
    """
    Add all the default helm chart repos:
    - metallb is for loadbalancing and assigning ips, on metal...
    - cilium is for networking policy management
    - ingress-nginx allows us to do ingress, so access outside the cluster
    - jetstack is for cert-manager for TLS certs
    - argo is argoCD to manage k8s resources in the future through a gui
    """
    repos = OrderedDict()

    # metallb comes first, but may be skipped
    if metallb:
        repos['metallb'] = 'https://metallb.github.io/metallb'

    # cilium comes first, but may be skipped
    if cilium:
        repos['cilium'] = 'https://helm.cilium.io/'

    repos['ingress-nginx'] = 'https://kubernetes.github.io/ingress-nginx'
    repos['jetstack'] = 'https://charts.jetstack.io'

    if argo:
        repos['argo-cd'] = 'https://argoproj.github.io/argo-helm'

    if argo_secrets:
        repos['appset-secret-plugin'] = ('https://small-hack.github.io/'
                                         'appset-secret-plugin')

    # kind has a special install path
    if k8s_distro == 'kind':
        repos.pop('ingress-nginx')

    # install and update any repos needed
    Helm.repo(repos).add()


def prepare_helm(k8s_distro: str,
                 argo: bool = False,
                 metallb: bool = True,
                 cilium: bool = False,
                 argo_app_set: bool = False) -> bool:
    """
    get helm installed if needed, and then install/update all the helm repos
    """
    header("Adding/Updating helm repos...")
    if not which("helm"):
        msg = ("ʕ•́ᴥ•̀ʔ [b]Helm[/b] is [warn]not installed[/warn]. "
               "[i]We'll install it for you.[/i] ʕᵔᴥᵔʔ")
        sub_header(msg)
        subproc(['brew install helm'])

    # this is where we add all the helm repos we're going to use
    add_default_repos(k8s_distro, metallb, cilium, argo, argo_app_set)
    return True
