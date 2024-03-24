from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.bitwarden.bw_cli import BwCLI
from smol_k8s_lab.utils.rich_cli.console_logging import header
from .longhorn import configure_longhorn
from .k8up_operater import configure_k8up_operator
from .minio import configure_minio_operator
from .postgres_operators import configure_cnpg_operator, configure_postgres_operator
from .seaweedfs import configure_seaweedfs


def setup_operators(k8s_obj: K8s,
                    longhorn_config: dict = {},
                    k8up_config: dict = {},
                    minio_config: dict = {},
                    seaweed_config: dict = {},
                    cnpg_config: dict = {},
                    pg_config: dict = {},
                    bitwarden: BwCLI = None) -> None:
    """ 
    deploy all k8s operators that can block other apps:
        - minio operator
        - cnpg (cloud native postgres) operator
    """
    header("Setting up Operators", "⚙️ ")

    # longhorn operator is used to have expanding volumes that span multiple nodes
    if longhorn_config and longhorn_config.get('enabled', False):
        configure_longhorn(k8s_obj, longhorn_config)

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

    # zalando postgres operator is a postgres operator for creating postgresql clusters
    if pg_config and pg_config.get('enabled', False):
        configure_postgres_operator(k8s_obj, pg_config, bitwarden)
