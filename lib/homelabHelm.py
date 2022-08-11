#!/usr/bin/env python3
"""
AUTHOR: @jessebot email: jessebot(AT)linux(d0t)com
USAGE: import homelabHelm as helm
"""
import subprocess


def sub_proc(command="", error_ok=False, suppress_output=False):
    """
    Takes a str commmand to run in BASH, as well as optionals bools to pass on
    errors in stderr/stdout and suppress_output
    """
    print('-'.center(78, '-'))
    print(f'\033[92m Running cmd:\033[00m {command}')
    cmd = command.split()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return_code = p.returncode
    res = p.communicate()
    res_stdout = '  ' + res[0].decode('UTF-8').replace('\n', '\n  ')
    res_stderr = '  ' + res[1].decode('UTF-8').replace('\n', '\n  ')

    if not error_ok:
        # check return code, raise error if failure
        if not return_code or return_code != 0:
            # also scan both stdout and stdin for weird errors
            for output in [res_stdout.lower(), res_stderr.lower()]:
                if 'error' in output:
                    err = f'Return code not zero! Return code: {return_code}'
                    # this just prints the error in red
                    raise Exception(f'\033[0;33m {err} \n {output} \033[00m')

    for output in [res_stdout, res_stderr]:
        if output:
            if not suppress_output:
                print(output.rstrip())
            return output


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
            self.update = self.update()

        def add(self):
            """
            helm repo add
            """
            cmd = f'helm repo add {self.repo_name} {self.repo_url}'
            sub_proc(cmd)
            self.update()

        def remove(self):
            """
            helm repo remove
            """
            cmd = f'helm repo remove {self.repo_name}'
            sub_proc(cmd)

        def update(self):
            """
            helm repo update
            """
            cmd = 'helm repo update'
            sub_proc(cmd)

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

        def install(self):
            """
            installs a helm chart to the current k8s context
            """
            cmd = (f'helm upgrade {self.release_name} {self.chart} --install'
                   f' --namespace {self.namespace} --create-namespace')

            if self.values_file:
                cmd += f' --values {self.values_file}'

            if self.set_options:
                for key, value in self.set_options.items:
                    cmd += f' --set {key}={value}'

            sub_proc(cmd)


        def uninstall(self):
            """
            Uninstalls a helm chart from the current k8s context
            """
            command = (f'helm uninstall {self.release_name}'
                       f' --namespace {self.namespace}')
            sub_proc(command)
