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

        def update(self):
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
        def __init__(self, release_name, **kwargs):
            """
            installs/uninstalls a helm chart. Takes optional key word args:
                chart="", namespace="", values_file="", set_options={}
            always does values file followed by --set options.
            """
            # only required arg
            self.release_name = release_name

            # for each keyword arg's key, create self.key for other methods
            # to reference e.g. pass in namespace='kube-system' and we create
            # self.namespace='kube-system'
            for key, value in kwargs:
                locals()[f'self.{key}'] = value

            # always install into default namespace unless stated otherwise
            if not kwargs['namespace']:
                self.namespace = 'default'

            self.upgrade = self.install(self)

        def install(self, wait=False):
            """
            installs helm chart to current k8s context, takes optional wait arg
            arg Defaults to False, if True, will wait till deployments are up
            """
            util.header("helm ")
            cmd = (f'helm upgrade {self.release_name} {self.chart} --install'
                   f' -n {self.namespace} --create-namespace')

            if self.values_file:
                cmd += f' --values {self.values_file}'

            if self.set_options:
                for key, value in self.set_options.items:
                    cmd += f' --set {key}={value}'

            if wait:
                cmd += ' --wait'
                util.sub_proc(cmd)
            else:
                util.sub_proc(cmd)

        def uninstall(self):
            """
            Uninstalls a helm chart from the current k8s context
            """
            command = f'helm uninstall {self.release_name} -n {self.namespace}'
            util.sub_proc(command)
