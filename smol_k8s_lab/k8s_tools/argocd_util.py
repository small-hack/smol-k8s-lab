# it was only a matter of time before I had to query argocd directly
import logging as log
from .k8s_lib import K8s
from ..utils.run.subproc import subproc
from json import loads


class ArgoCD():
    """
    class for common Argo CD functions
    """

    def __init__(self,
                 namespace: str,
                 argo_cd_domain: str,
                 k8s_obj: K8s|None = None) -> None:

        # setup Argo CD to talk directly to k8s
        log.debug(f"setting namespace to {namespace} and configuring argocd "
                  "to use k8s for auth")
        subproc([f'kubectl config set-context --current --namespace={namespace}',
                 f'argocd login {argo_cd_domain} --core'])
        self.namespace = namespace
        self.hostname = argo_cd_domain
        self.k8s = k8s_obj

    def check_if_app_exists(self, app: str) -> bool:
        """
        check if argocd application has already been installed
        """
        res = subproc([f"argocd app get {app}"], error_ok=True)
        if app in res:
            return True
        else:
            return False

    def sync_app(self,
                 app: str,
                 spinner: bool = True,
                 replace: bool = False,
                 force: bool = False) -> str:
        """
        syncs an argocd app and returns the result
        """
        # build sync command
        cmd = "argocd app sync --retry-limit 3 --loglevel warn "
        if replace:
            cmd += "--replace "
        if force:
            cmd += "--force "
        cmd += app

        counter = 0
        while True:
            if counter == 10:
                log.error("Something has gone wrong with syncs! we tried 10 times!")
                break
            # run sync command
            if spinner:
                res = subproc([cmd], error_ok=True)
            else:
                res = subproc([cmd], spinner=False, error_ok=True)

            if "permission denied" not in res:
                return res

            counter += 1

    def delete_app(self,
                   app: str,
                   spinner: bool = True,
                   force: bool = False) -> str:
        """
        delete an argocd app and returns the result
        """
        # build delete command
        cmd = "argocd app delete -y "
        if force:
            cmd += "--force "
        cmd += app

        # run sync command
        if spinner:
            return subproc([cmd])
        else:
            return subproc([cmd], spinner=False, error_ok=True)

    def install_app(self, app: str, argo_dict: dict, wait: bool = False) -> bool|None:
        """
        create and Argo CD app directly from the command line using passed in
        app and argo_dict which should have str keys for repo, path, and namespace
        """
        if self.check_if_app_exists(app):
            log.debug(f"An Argo CD app called [green]{app}[/] already [green]exists[/] :)")
            return True
        else:
            log.info(f"Installing an Argo CD app called {app} :)")
            repo = argo_dict['repo']
            path = argo_dict['path']
            revision = argo_dict['revision']
            app_namespace = argo_dict['namespace']
            app_cluster = argo_dict.get('cluster', 'https://kubernetes.default.svc')
            proj_namespaces = argo_dict['project']['destination']['namespaces']
            proj_namespaces.append(app_namespace)
            if 'argocd' not in proj_namespaces:
                proj_namespaces.append('argocd')

            # make sure the namespace already exists
            self.k8s.create_namespace(app_namespace)

            source_repos = [repo]
            extra_source_repos = argo_dict["project"].get('source_repos', [])
            if extra_source_repos:
                source_repos.extend(extra_source_repos)

            self.create_project(argo_dict['project'].get('name', app),
                                       app,
                                       set(proj_namespaces),
                                       app_cluster,
                                       set(source_repos))

            cmd = (f"argocd app create {app} --upsert "
                   f"--repo {repo} "
                   f"--path {path} "
                   f"--revision {revision} "
                   "--sync-policy automated "
                   "--sync-option ApplyOutOfSyncOnly=true "
                   "--self-heal "
                   f"--dest-namespace {app_namespace} "
                   f"--dest-server {app_cluster}")

            if argo_dict['directory_recursion']:
                cmd += " --directory-recurse"

            response = subproc([cmd])
            log.debug(response)

            # wait for the app to be healthy if requested by the user
            if wait:
                self.wait_for_app(app)

    def wait_for_app(self, app: str, retry: bool = False) -> None:
        """
        checks the status of an Argo CD app and waits till it is ready
        """
        if retry:
            # set error to true by default
            error = True
            # while error still equals True, keep retrying the command
            while error:
                try:
                    subproc([f"argocd app wait {app} --health --loglevel warn"])
                except Exception as e:
                    log.debug(e)
                    error = True
                    log.debug(f"Retrying wait for for {app}")
                else:
                    error = False
        else:
            subproc([f"argocd app wait {app} --health --loglevel warn"])

    def create_project(self,
                       project_name: str,
                       app: str,
                       namespaces: set,
                       clusters: str|list,
                       source_repos: set) -> True:
        """
        create an argocd project
        """
        argocd_proj = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "AppProject",
            "metadata": {
                "name": project_name,
                "namespace": 'argocd',
            },
            "spec": {
                "clusterResourceWhitelist": [
                    {
                        "group": "*",
                        "kind": "*"
                    }
                ],
                "description": f"project for {app}",
                "destinations": [],
                "namespaceResourceWhitelist": [
                    {
                        "group": "*",
                        "kind": "*"
                    }
                ],
                "orphanedResources": {},
                "sourceRepos": list(source_repos)
            },
            "status": {}
        }

        # if the user has passed in a single cluster... todo: handle multiple clusters
        if isinstance(clusters, str):
            if clusters == "https://kubernetes.default.svc":
                name = "in-cluster"
                server = "https://kubernetes.default.svc"
            elif clusters == "in-cluster":
                server = "https://kubernetes.default.svc"
                name = "in-cluster"
            else:
                cluster_json = loads(subproc(f"argocd cluster get {clusters} -o json"))
                name = cluster_json["name"]
                server = cluster_json["server"]

            for namespace in namespaces:
                extra_dest = {"name": name, "namespace": namespace, "server": server}
                argocd_proj['spec']['destinations'].append(extra_dest)

        try:
            self.k8s.apply_custom_resources([argocd_proj])
        except Exception as e:
            log.warn(e)

    def update_appset_secret(self, fields: dict, argo_managed: bool = True) -> None:
        """
        pass in k8s context and dict of fields to add to the argocd appset secret
        and reload the deployment
        """
        self.k8s.update_secret_key('appset-secret-vars',
                                   self.namespace,
                                   fields,
                                   'secret_vars.yaml')

        if argo_managed:
            # reload the argocd appset secret plugin
            self.sync_app('appset-secrets-plugin', spinner=True, replace=True, force=True)
            self.wait_for_app('appset-secrets-plugin')
        else:
            self.k8s.reload_deployment("appset-secrets-plugin", self.namespace)

        # reload the bitwarden ESO provider
        self.sync_app('bitwarden-eso-provider', spinner=True, replace=True, force=True)
        self.wait_for_app('bitwarden-eso-provider')
