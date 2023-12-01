from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.bitwarden.bw_cli import BwCLI
from smol_k8s_lab.utils.rich_cli.console_logging import header
from .minio import configure_minio_operator
from .seaweedfs import configure_seaweedfs
from .cnpg_operator import configure_cnpg_operator
from .k8up_operater import configure_k8up_operator


def setup_operators(k8s_obj: K8s,
                    k8up_config: dict = {},
                    minio_config: dict = {},
                    seaweed_config: dict = {},
                    cnpg_config: dict = {},
                    bitwarden: BwCLI = None) -> None:
    """ 
    deploy all k8s operators that can block other apps:
        - minio operator
        - cnpg (cloud native postgres) operator
    """
    header("Setting up Operators", "⚙️ ")

    # k8up operator is a postgres operator for creating postgresql clusters
    if k8up_config and k8up_config.get('enabled', False):
        configure_k8up_operator(k8s_obj, k8up_config)

    # minio operator is used to spin up minio tenants for isolated s3 endpoints
    if minio_config and minio_config.get('enabled', False):
        configure_minio_operator(k8s_obj, minio_config)

    # seaweedfs
    if seaweed_config and seaweed_config.get('enabled', False):
        configure_seaweedfs(k8s_obj, seaweed_config, bitwarden)

    # cnpg operator is a postgres operator for creating postgresql clusters
    if cnpg_config and cnpg_config.get('enabled', False):
        configure_cnpg_operator(k8s_obj, cnpg_config)
