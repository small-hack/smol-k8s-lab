# it was only a matter of time before I had to query argocd directly
from ..subproc import subproc


def install_with_argocd(app: str, repo: str, path: str, namespace: str):
    """
    create and Argo CD app directly from the command line using passed in
    app, repo, path, and namespace
    """
    cmd = (f"argocd app create guestbook --repo {repo} --path {path}"
           f"--dest-namespace {namespace} --dest-server "
           "https://kubernetes.default.svc")

    subproc([cmd])
