# it was only a matter of time before I had to query argocd directly
import logging as log
from .k8s_lib import K8s
from .kubernetes_util import apply_custom_resources
from ..utils.subproc import subproc


def install_with_argocd(k8s_obj: K8s, app: str, argo_dict: dict) -> True:
    """
    create and Argo CD app directly from the command line using passed in
    app and argo_dict which should have str keys for repo, path, and namespace
    """
    repo = argo_dict['repo']
    path = argo_dict['path']
    app_namespace = argo_dict['namespace']
    proj_namespaces = argo_dict['project']['destination']['namespaces']
    proj_namespaces.append(app_namespace)

    if argo_dict.get('part_of_app_of_apps', None):
        log.debug("Looks like this app is actually part of an app of apps "
                  "that will be deployed")
        return True

    # make sure the namespace already exists
    k8s_obj.create_namespace(app_namespace)

    source_repos = [repo]
    extra_source_repos = argo_dict["project"].get('source_repos', [])
    if extra_source_repos:
        source_repos.extend(extra_source_repos)
    create_argocd_project(app, app, set(proj_namespaces), source_repos)

    cmd = (f"argocd app create {app} --upsert "
           f"--repo {repo} "
           f"--path {path} "
           "--sync-policy automated "
           "--sync-option ApplyOutOfSyncOnly=true "
           "--self-heal "
           f"--dest-namespace {app_namespace} "
           "--dest-server https://kubernetes.default.svc")

    response = subproc([cmd])
    log.debug(response)

    return True


def wait_for_argocd_app(app: str):
    """
    checks the status of an Argo CD app and waits till it is ready
    """
    subproc([f"argocd app wait {app}"])
    return True


def create_argocd_project(project_name: str,
                          app: str,
                          namespaces: str,
                          source_repos: list) -> True:
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
            "destinations": [
                {
                    "name": "in-cluster",
                    "namespace": 'argocd',
                    "server": "https://kubernetes.default.svc"
                }
            ],
            "namespaceResourceWhitelist": [
                {
                    "group": "*",
                    "kind": "*"
                }
            ],
            "orphanedResources": {},
            "sourceRepos": source_repos
        },
        "status": {}
    }

    for namespace in namespaces:
        extra_namespace = {
                    "name": "in-cluster",
                    "namespace": namespace,
                    "server": "https://kubernetes.default.svc"
                },
        argocd_proj['spec']['destinations'].append(extra_namespace)

    apply_custom_resources([argocd_proj])
