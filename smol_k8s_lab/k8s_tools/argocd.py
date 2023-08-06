# it was only a matter of time before I had to query argocd directly
from ..subproc import subproc


def install_with_argocd(app: str, argo_dict: dict):
    """
    create and Argo CD app directly from the command line using passed in
    app and argo_dict which should have str keys for repo, path, and namespace
    """
    repo = argo_dict['repo']
    path = argo_dict['path']
    namespace = argo_dict['namespace']

    cmd = (f"argocd app create {app} "
           f"--repo {repo} "
           f"--path {path} "
           f"--dest-namespace {namespace} "
           "--dest-server https://kubernetes.default.svc")

    subproc([cmd])
