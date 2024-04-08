from smol_k8s_lab.k8s_tools.argocd_util import (install_with_argocd,
                                                check_if_argocd_app_exists)
from smol_k8s_lab.k8s_tools.k8s_lib import K8s


def configure_prometheus_crds(k8s_obj: K8s, config: dict) -> None:
    """
    setup the prometheus CRDs as an Argo CD Application
    """
    if not check_if_argocd_app_exists('prometheus-crds'):
        # actual installation of the prometheus CRDs app
        install_with_argocd(k8s_obj, 'prometheus-crds', config['argo'])
