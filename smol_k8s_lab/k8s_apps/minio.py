from json import load, dump
import logging as log
from os.path import exists
from os import makedirs
from minio import Minio, MinioAdmin
from shutil import which
# from xdg_base_dirs import xdg_config_home

from smol_k8s_lab.constants import HOME_DIR
from smol_k8s_lab.bitwarden.bw_cli import BwCLI
from smol_k8s_lab.k8s_tools.argocd_util import (
        install_with_argocd, wait_for_argocd_app, check_if_argocd_app_exists)
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.utils.passwords import create_password
from smol_k8s_lab.utils.subproc import subproc


def configure_minio(k8s_obj: K8s,
                    minio_config: dict,
                    secure: bool = True,
                    bitwarden: BwCLI = None):
    """
    minio installation and configuration

    if minio init is enabled, we also return the hostname and root credentials

    if secure is set to True, we write a config with https:// prefixing the
    hostname, else we use http://
    """
    minio_init_enabled = minio_config['init']['enabled']
    argo_app_exists = check_if_argocd_app_exists('minio')

    # if the user has enabled smol_k8s_lab init, we create an initial user
    if minio_init_enabled:
        access_key = minio_config['init']['values']['root_user']
        minio_hostname = minio_config['argo']['secret_keys']['api_hostname']

        # if the app already exists and bitwarden is enabled return the credentials
        if argo_app_exists:
            if bitwarden:
                res = bitwarden.get_item(
                        f'minio-tenant-root-credentials-{minio_hostname}')
                secret_key = res[0]['login']['password']
                return BetterMinio('minio-root', minio_hostname, access_key, secret_key)
            # if app already exists but bitwarden is not enabled, return None
            return

        secret_key = create_password()
        # the namespace probably doesn't exist yet, so we try to create it
        k8s_obj.create_namespace('minio')

        # creates the initial root credentials secret for the minio tenant
        credentials_exports = {'config.env': f"""MINIO_ROOT_USER={access_key}
        MINIO_ROOT_PASSWORD={secret_key}"""}
        k8s_obj.create_secret('default-tenant-env-config', 'minio',
                              credentials_exports)

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

    # while we wait for the app to come up, update the config file
    if minio_init_enabled:
        protocal = "http"
        if secure:
            protocal = "https"
        # we create a config file so users can easily use minio from the cli
        new_minio_alias = {"url": f"{protocal}://{minio_hostname}",
                           "accessKey": access_key,
                           "secretKey": secret_key,
                           "api": "S3v4",
                           "path": "auto"}

        # if the user hasn't chosen a config location, we use XDG spec, maybe
        # xdg_minio_config_file = xdg_config_home() + "/minio/config.json"
        minio_config_dir = HOME_DIR + ".mc/"
        minio_config_file = minio_config_dir + "config.json"

        # create the dir if it doesn't exist
        if not exists(minio_config_file):
            makedirs(minio_config_dir, exist_ok=True)
            minio_cfg_obj = {}
        else:
            # open the default minio cli config to take a peek
            with open(minio_config_file, 'r') as minio_config_contents:
                minio_cfg_obj = load(minio_config_contents)

        # reconfigure the file for our new alias
        if not minio_cfg_obj:
            # if there's not a config object, make one
            minio_cfg_obj = {"version": "10",
                             "aliases": {"minio-root": new_minio_alias}}
        else:
            aliases = minio_cfg_obj.get("aliases", None)
            # if there is an aliases section with minio-root, update it
            if aliases:
                minio_cfg_obj['aliases']['minio-root'] = new_minio_alias
            # if there is not an aliases section with minio-root, create one
            else:
                minio_cfg_obj['aliases'] = {"minio-root": new_minio_alias}

        # write out the config file when we're done
        with open(minio_config_file, 'w') as minio_config_contents:
            dump(minio_cfg_obj, minio_config_contents)

    # make sure the app is up before returning
    wait_for_argocd_app('minio')

    if minio_init_enabled:
        return BetterMinio('minio-root', minio_hostname, access_key, secret_key)


class BetterMinio:
    """ 
    a wrapper around the two seperate Minio and MinioAdmin clients to create
    users and buckets with basic policies
    """

    def __init__(self,
                 minio_alias: str,
                 api_hostname: str,
                 access_key: str,
                 secret_key: str) -> None:
        self.root_user = access_key
        self.root_password = secret_key
        self.admin_client = MinioAdmin(minio_alias)
        self.client = Minio(api_hostname, access_key, secret_key)

    def create_access_credentials(self, access_key: str) -> str:
        """
        given an access key name, we create minio access credentials
        using the mc admin client
        return secret_key
        """
        if which("brew") and not which("mc"):
            # try to install minio-mc with brew
            subproc("brew install minio-mc")

        # Create a client with the MinIO hostname, its access key and secret key.
        log.info(f"About to create the minio credentials for user {access_key}")

        # similar to mc admin user add
        secret_key = create_password()
        self.admin_client.user_add(access_key, secret_key)

        log.info(f"Creation of minio credentials for user {access_key} completed.")
        return secret_key

    def create_bucket(self, bucket_name: str, access_key: str) -> None:
        """
        Takes bucket_name and access_key of user to assign bucket to
        creates a bucket via the minio sdk
        """
        # Make bucket if it does not exist already
        log.info(f'Check for bucket "{bucket_name}"...')
        found = self.client.bucket_exists(bucket_name)

        if not found:
            log.info(f'Creating bucket "{bucket_name}"...')
            self.client.make_bucket(bucket_name)

            # policy for bucket
            log.info(f"Adding a readwrite policy for bucket, {bucket_name}")
            self.admin_client.policy_set('readwrite', access_key)
        else:
            log.info(f'Bucket "{bucket_name}" already exists')
