# it was only a matter of time before I had to query argocd directly
import logging as log
from .k8s_lib import K8s
from ..subproc import subproc


def install_with_argocd(k8s_obj: K8s,
                        app: str = "",
                        argo_dict: dict = {}) -> True:
    """
    create and Argo CD app directly from the command line using passed in
    app and argo_dict which should have str keys for repo, path, and namespace
    """
    repo = argo_dict['repo']
    path = argo_dict['path']
    namespace = argo_dict['namespace']

    # make sure the namespace already exists
    k8s_obj.create_namespace(namespace)

    cmd = (f"argocd app create {app} "
           f"--repo {repo} "
           f"--path {path} "
           f"--dest-namespace {namespace} "
           "--dest-server https://kubernetes.default.svc")

    response = subproc([cmd])
    log.debug(response)

    return True
