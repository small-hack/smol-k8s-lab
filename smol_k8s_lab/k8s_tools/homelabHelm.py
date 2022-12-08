#!/usr/bin/env python3
"""
AUTHOR: @jessebot email: jessebot(AT)linux(d0t)com
USAGE: import homelabHelm as helm
"""


from collections import OrderedDict
from shutil import which
from ..subproc import subproc
from ..console_logging import header, sub_header


class helm:
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
        def __init__(self, repo_dict):
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

        def install(self, wait=False):
            """
            Installs helm chart to current k8s context, takes optional wait arg
            Defaults to False, if True, will wait till deployments are up
            keyword args:
                - release_name: str to call this installation
                - chart_name: str of helm chart to use (repo/chart)
                - chart_version: version of the chart to install
                - namespace: str of namespace to deploy release to
                - values_file: a str of a file to use with --values
            """
            cmd = (f'helm upgrade {self.release_name} {self.chart_name}'
                   f' --install -n {self.namespace} --create-namespace')
            # f' --atomic')

            if self.__dict__.get('chart_version', False):
                cmd += f' --version {self.chart_version}'

            if self.__dict__.get('values_file', False):
                cmd += f' --values {self.values_file}'

            if self.__dict__.get('set_options', False):
                for key, value in self.set_options.items():
                    cmd += f' --set {key}={value}'

            if wait:
                cmd += ' --wait --wait-for-jobs'

            subproc([cmd])

        def uninstall(self):
            """
            Uninstalls a helm chart from the current k8s context
            """
            cmd = f'helm uninstall {self.release_name} -n {self.namespace}'
            subproc([cmd])
            return True


def add_default_repos(k8s_distro, argo=False, external_secrets=False,
                      kyverno=False):
    """
    Add all the default helm chart repos:
    - metallb is for loadbalancing and assigning ips, on metal...
    - ingress-nginx allows us to do ingress, so access outside the cluster
    - jetstack is for cert-manager for TLS certs
    - argo is argoCD to manage k8s resources in the future through a gui
    - kyverno is a k8s native policy manager
    """
    repos = OrderedDict()

    repos['metallb'] = 'https://metallb.github.io/metallb'
    repos['ingress-nginx'] = 'https://kubernetes.github.io/ingress-nginx'
    repos['jetstack'] = 'https://charts.jetstack.io'

    if external_secrets:
        repos['external-secrets'] = 'https://charts.external-secrets.io'

    if argo:
        repos['argo-cd'] = 'https://argoproj.github.io/argo-helm'

    if kyverno:
        repos['kyverno'] = 'https://kyverno.github.io/kyverno/'

    # kind has a special install path
    if k8s_distro == 'kind':
        repos.pop('ingress-nginx')

    # install and update any repos needed
    helm.repo(repos).add()
    return


def prepare_helm(k8s_distro="", argo=False, external_secrets=False,
                 kyverno=False):
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
    add_default_repos(k8s_distro, argo, external_secrets, kyverno)
    return
