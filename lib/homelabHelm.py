#!/usr/bin/env python3
"""
AUTHOR: @jessebot email: jessebot(AT)linux(d0t)com
USAGE: import homelabHelm as helm
"""
from . import util


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
        def __init__(self, repo_name, repo_url):
            self.repo_name = repo_name
            self.repo_url = repo_url

        def add(self):
            """
            helm repo add
            """
            cmd = f'helm repo add {self.repo_name} {self.repo_url}'
            util.sub_proc(cmd)

        def update():
            """
            helm repo update
            """
            cmd = 'helm repo update'
            util.sub_proc(cmd)

        def remove(self):
            """
            helm repo remove
            """
            cmd = f'helm repo remove {self.repo_name}'
            util.sub_proc(cmd)

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
            """
            cmd = (f'helm upgrade {self.release_name} {self.chart_name}'
                   f' --install -n {self.namespace} --create-namespace')

            try:
                cmd += f' --values {self.values_file}'
            except AttributeError:
                pass

            try:
                if self.__dict__['set_options']:
                    for key, value in self.set_options.items:
                        cmd += f' --set {key}={value}'
            except KeyError:
                pass

            if wait:
                cmd += ' --wait'

            util.header(cmd)
            util.sub_proc(cmd)

        def uninstall(self):
            """
            Uninstalls a helm chart from the current k8s context
            """
            command = f'helm uninstall {self.release_name} -n {self.namespace}'
            util.sub_proc(command)
