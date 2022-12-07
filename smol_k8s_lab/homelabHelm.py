#!/usr/bin/env python3
"""
AUTHOR: @jessebot email: jessebot(AT)linux(d0t)com
USAGE: import homelabHelm as helm
"""
from .subproc import subproc


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
        def __init__(self, **kwargs):
            """
            installs/uninstalls a helm chart. Takes key word args:
            release_name="", chart_name="", namespace="", values_file="",
            set_options={}
            always does values file followed by --set options.
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
            installs helm chart to current k8s context, takes optional wait arg
            Defaults to False, if True, will wait till deployments are up
            keyword args:
                - release_name: str to call this installation
                - chart_name: str of helm chart to use (repo/chart)
                - namespace: str of namespace to deploy release to
                - values_file: a str of a file to use with --values
            """
            cmd = (f'helm upgrade {self.release_name} {self.chart_name}'
                   f' --install -n {self.namespace} --create-namespace')
            # f' --atomic')

            try:
                cmd += f' --values {self.values_file}'
            except AttributeError:
                pass

            try:
                if self.__dict__['set_options']:
                    for key, value in self.set_options.items():
                        cmd += f' --set {key}={value}'
            except KeyError:
                pass

            if wait:
                cmd += ' --wait --wait-for-jobs'

            subproc([cmd])

        def uninstall(self):
            """
            Uninstalls a helm chart from the current k8s context
            """
            cmd = f'helm uninstall {self.release_name} -n {self.namespace}'
            subproc([cmd])
