# internal libraries
from smol_k8s_lab.bitwarden.bw_cli import BwCLI
from smol_k8s_lab.k8s_tools.argocd_util import ArgoCD

def configure_openbao(argocd: ArgoCD, config: dict, bw: BwCLI = None) -> None:
    """
    setup the openbao as an Argo CD Application
    """
    if not argocd.check_if_app_exists('openbao'):
        argocd.install_app('openbao', config['argo'])
    else:
        argocd.sync_app('openbao')
