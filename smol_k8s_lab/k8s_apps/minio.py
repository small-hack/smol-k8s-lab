import logging as log
from minio import Minio, MinioAdmin
from shutil import which

from smol_k8s_lab.bitwarden.bw_cli import BwCLI
from smol_k8s_lab.k8s_tools.argocd_util import install_with_argocd, wait_for_argocd_app
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.utils.passwords import create_password
from smol_k8s_lab.utils.subproc import subproc


def configure_minio(k8s_obj: K8s,
                    minio_config: dict,
                    bitwarden: BwCLI = None) -> None | list:
    """
    minio installation and configuration

    if minio init is enabled, we also return the hostname and root credentials
    """
    minio_init_enabled = minio_config['init']['enabled']

    # if the user has enabled smol_k8s_lab init, we create an initial user
    if minio_init_enabled:
        access_key = minio_config['init']['values']['root_user']
        secret_key = create_password()
        minio_hostname = minio_config['argo']['secret_keys']['minio_api_hostname']

        credentials_exports = (
        f'export MINIO_ROOT_USER="{access_key}"\n'
        f'export MINIO_ROOT_PASSWORD="{secret_key}"'
        )

        # the namespace probably doesn't exist yet, so we try to create it
        k8s_obj.create_namespace('minio')

        # creates the initial root credentials secret for the minio tenant
        k8s_obj.create_secret('default-tenant-env-config', 'minio',
                              credentials_exports,
                              'config.env')

        if bitwarden:
            log.info("Creating MinIO root credentials in Bitwarden")

            # admin credentials + metrics server info token
            bitwarden.create_login(
                    name='minio-tenant-root-credentials',
                    item_url=minio_hostname,
                    user=access_key,
                    password=secret_key
                    )

    # actual installation of the minio app
    install_with_argocd(k8s_obj, 'minio', minio_config['argo'])
    wait_for_argocd_app('minio')

    if minio_init_enabled:
        return [minio_hostname, access_key, secret_key]


def create_access_credentials(hostname: str, access_key: str) -> str:
    """
    given a hostname, create minio access credentials using the mc admin client
    return secret_key
    """
    if which("brew") and not which("mc"):
        # try to install minio-mc with brew
        subproc("brew install minio-mc")

    # Create a client with the MinIO hostname, its access key and secret key.
    admin_client = MinioAdmin(hostname)

    # similar to mc admin user add
    secret_key = create_password()
    admin_client.user_add(access_key, secret_key)

    # make the credentials
    return secret_key


def create_bucket(hostname: str, access_key: str, secret_key: str,
                  bucket_name: str) -> None:
    """
    Takes credentials and a bucket_name and creates a bucket via the minio sdk
    """
    # Create a client with the MinIO hostname, its access key and secret key.
    client = Minio(hostname, access_key=access_key, secret_key=secret_key)
    
    # Make bucket if it does not exist already
    found = client.bucket_exists(bucket_name)
    if not found:
        client.make_bucket(bucket_name)
    else:
        log.info(f'Bucket "{bucket_name}" already exists')
