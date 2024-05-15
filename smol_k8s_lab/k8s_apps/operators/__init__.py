from smol_k8s_lab.bitwarden.bw_cli import BwCLI
from smol_k8s_lab.k8s_tools.argocd_util import ArgoCD
from smol_k8s_lab.utils.rich_cli.console_logging import header
from .postgres_operators import configure_postgres_operator
from .seaweedfs import configure_seaweedfs


def setup_operators(argocd: ArgoCD,
                    prometheus_config: dict = {},
                    longhorn_config: dict = {},
                    k8up_config: dict = {},
                    minio_config: dict = {},
                    seaweed_config: dict = {},
                    cnpg_config: dict = {},
                    pg_config: dict = {},
                    bitwarden: BwCLI = None) -> None:
    """
    deploy all k8s operators that can block other apps:
        - prometheus
        - longhorn
        - k8up
        - minio operator
        - seaweedfs
        - cnpg (cloud native postgres) operator
        - zalando postgres operator
    """
    header("Setting up Operators", "⚙️ ")

    # deploy the prometheus CRDs before everything else so that apps with metrics don't fail
    if prometheus_config and prometheus_config.get('enabled', False):
        argocd.install_app('prometheus-crds', prometheus_config['argo'])

    # longhorn operator is used to have expanding volumes that span multiple nodes
    if longhorn_config and longhorn_config.get('enabled', False):
        argocd.install_app('longhorn', longhorn_config['argo'])

    # k8up operator is a postgres operator for creating postgresql clusters
    if k8up_config and k8up_config.get('enabled', False):
        argocd.install_app('k8up', k8up_config['argo'])

    # minio operator is used to spin up minio tenants for isolated s3 endpoints
    if minio_config and minio_config.get('enabled', False):
        argocd.install_app('minio', minio_config['argo'], True)

    # seaweedfs
    if seaweed_config and seaweed_config.get('enabled', False):
        configure_seaweedfs(argocd, seaweed_config, bitwarden)

    # cnpg operator is a postgres operator for creating postgresql clusters
    if cnpg_config and cnpg_config.get('enabled', False):
        argocd.install_app('cnpng-operator', cnpg_config['argo'])

    # zalando postgres operator is a postgres operator for creating postgresql clusters
    if pg_config and pg_config.get('enabled', False):
        configure_postgres_operator(argocd, pg_config, bitwarden)
