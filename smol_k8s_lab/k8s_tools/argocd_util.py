# it was only a matter of time before I had to query argocd directly
import logging as log
from .k8s_lib import K8s
from ..utils.subproc import subproc


def check_if_argocd_app_exists(app: str) -> bool:
    """
    check if argocd application has already been installed
    """
    res = subproc([f"argocd app get {app}"], error_ok=True)
    if app in res:
        return True
    else:
        return False


def sync_argocd_app(app: str) -> None:
    """
    syncs an argocd app
    """
    subproc([f"argocd app sync {app}"])


def install_with_argocd(k8s_obj: K8s, app: str, argo_dict: dict) -> None:
    """
    create and Argo CD app directly from the command line using passed in
    app and argo_dict which should have str keys for repo, path, and namespace
    """
    repo = argo_dict['repo']
    path = argo_dict['path']
    revision = argo_dict['revision']
    app_namespace = argo_dict['namespace']
    proj_namespaces = argo_dict['project']['destination']['namespaces']
    proj_namespaces.append(app_namespace)

    # make sure the namespace already exists
    k8s_obj.create_namespace(app_namespace)

    source_repos = [repo]
    extra_source_repos = argo_dict["project"].get('source_repos', [])
    if extra_source_repos:
        source_repos.extend(extra_source_repos)
    create_argocd_project(k8s_obj, app, app, set(proj_namespaces), source_repos)

    cmd = (f"argocd app create {app} --upsert "
           f"--repo {repo} "
           f"--path {path} "
           f"--revision {revision} "
           "--sync-policy automated "
           "--sync-option ApplyOutOfSyncOnly=true "
           "--self-heal "
           f"--dest-namespace {app_namespace} "
           "--dest-server https://kubernetes.default.svc")

    if argo_dict['directory_recursion']:
        cmd += " --directory-recurse"

    response = subproc([cmd])
    log.debug(response)


def wait_for_argocd_app(app: str, retry: bool = False) -> None:
    """
    checks the status of an Argo CD app and waits till it is ready
    """
    if retry:
        # set error to true by default
        error = True
        # while error still equals True, keep retrying the command
        while error:
            try:
                subproc([f"argocd app wait {app} --health"])
            except Exception as e:
                log.debug(e)
                error = True
                log.debug(f"Retrying wait for for {app}")
            else:
                error = False
    else:
        subproc([f"argocd app wait {app}"])


def create_argocd_project(k8s_obj: K8s,
                          project_name: str,
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
                }
        argocd_proj['spec']['destinations'].append(extra_namespace)

    try:
        k8s_obj.apply_custom_resources([argocd_proj])
    except Exception as e:
        log.warn(e)


def update_argocd_appset_secret(k8s_obj: K8s, fields: dict) -> None:
    """ 
    pass in k8s context and dict of fields to add to the argocd appset secret
    and reload the deployment
    """
    k8s_obj.update_secret_key('appset-secret-vars',
                              'argocd',
                              fields,
                              'secret_vars.yaml')

    # reload the argocd appset secret plugin
    try:
        k8s_obj.reload_deployment('appset-secret-plugin', 'argocd')
    except Exception as e:
        log.error(
                "Couldn't scale down the "
                "[magenta]argocd-appset-secret-plugin[/] deployment "
                f"in [green]argocd[/] namespace. Recieved: {e}"
                )

    # reload the bitwarden ESO provider
    try:
        k8s_obj.reload_deployment('bitwarden-eso-provider', 'external-secrets')
    except Exception as e:
        log.error(
                "Couldn't scale down the [magenta]"
                "bitwarden-eso-provider[/] deployment in [green]"
                f"external-secrets[/] namespace. Recieved: {e}"
                )
