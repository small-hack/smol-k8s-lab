from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.utils.rich_cli.console_logging import header
from .minio import configure_minio_operator
from .cnpg_operator import configure_cnpg_operator


def setup_operators(k8s_obj: K8s,
                    minio_config: dict = {},
                    cnpg_config: dict = {}) -> None:
    """ 
    deploy all k8s operators that can block other apps:
        - minio operator
        - cnpg (cloud native postgres) operator
    """
    header("Setting up Operators", "⚙️ ")

    # minio operator is used to spin up minio tenants for isolated s3 endpoints
    if minio_config and minio_config.get('enabled', False):
        configure_minio_operator(k8s_obj, minio_config)

    # cnpg operator is a postgres operator for creating postgresql clusters
    if cnpg_config and cnpg_config.get('enabled', False):
        configure_cnpg_operator(k8s_obj, cnpg_config)
