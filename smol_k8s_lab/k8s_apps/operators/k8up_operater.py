from smol_k8s_lab.k8s_tools.argocd_util import (install_with_argocd,
                                                check_if_argocd_app_exists)
from smol_k8s_lab.k8s_tools.k8s_lib import K8s


def configure_k8up_operator(k8s_obj: K8s, config: dict) -> None:
    """
    setup the MinIO operator as an Argo CD Application
    """
    # check if minio is using smol_k8s_lab init and if already present in Argo CD
    if not check_if_argocd_app_exists('k8up'):
        # actual installation of the minio app
        install_with_argocd(k8s_obj, 'k8up', config['argo'])
