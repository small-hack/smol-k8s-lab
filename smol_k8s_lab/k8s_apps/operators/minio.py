from json import load, dump
import logging as log
from os.path import exists, join
from os import makedirs

from smol_k8s_lab.constants import HOME_DIR
from smol_k8s_lab.bitwarden.bw_cli import BwCLI
from smol_k8s_lab.k8s_apps.identity_provider.zitadel_api import Zitadel
from smol_k8s_lab.k8s_tools.argocd_util import ArgoCD
from smol_k8s_lab.utils.passwords import create_password
from smol_k8s_lab.utils.minio_lib import BetterMinio


def configure_minio_tenant(argocd: ArgoCD,
                           minio_config: dict,
                           secure: bool = True,
                           zitadel_hostname: str = "",
                           zitadel: Zitadel = None,
                           bitwarden: BwCLI = None) -> BetterMinio | None:
    """
    minio tenant installation and configuration

    if secure is set to True, we write a config with https:// prefixing the
    hostname, else we use http://

    if zitadel obj and zitadel_hostname:
        We'll set up oidc for your tenant user console

    if bitwarden obj:
        We'll store all your secrets in bitwarden

    if init is enabled we:
      - write a minio config file with alias called minio-root for use with mc cli
      - return a BetterMinio object ready to create users, buckets, and policies
    """

    minio_init_enabled = minio_config['init']['enabled']
    argo_app_exists = argocd.check_if_app_exists('minio-tenant')

    secrets = minio_config['argo']['secret_keys']
    if secrets:
        minio_hostname = secrets.get('api_hostname', "")
        minio_user_console_hostname = secrets.get('user_console_hostname', "")

    # if the app already exists and bitwarden is enabled return the credentials
    if minio_init_enabled and argo_app_exists:
        if bitwarden:
            res = bitwarden.get_item(
                    f'minio-tenant-root-credentials-{minio_hostname}')
            access_key = minio_config['init']['values']['root_user']
            secret_key = res[0]['login']['password']
            return BetterMinio('minio-root', minio_hostname, access_key, secret_key)
        # if app already exists but bitwarden is not enabled, return None
        return

    # if the user has enabled smol_k8s_lab init, we create an initial user
    if minio_init_enabled and not argo_app_exists:
        # the namespace probably doesn't exist yet, so we try to create it
        argocd.k8s.create_namespace(minio_config['argo']['namespace'])
        access_key = minio_config['init']['values']['root_user']
        secret_key = create_password(characters=72)

        if zitadel:
            log.info("Creating a MinIO OIDC application via Zitadel...")
            redirect_uris = f"https://{minio_user_console_hostname}/oauth_callback"
            logout_uris = [f"https://{minio_user_console_hostname}/login"]
            minio_dict = zitadel.create_application("minio",
                                                    redirect_uris,
                                                    logout_uris)
            zitadel.create_role("minio_users", "MinIO Users", "minio_users")
            zitadel.create_role("minio_admins", "MinIO Administrators", "minio_admins")
            zitadel.update_user_grant(['minio_users', 'minio_admins'])

            # creates the initial root credentials secret for the minio tenant
            credentials_exports = {
                    'config.env': f"""MINIO_ROOT_USER={access_key}
            MINIO_ROOT_PASSWORD={secret_key}
            MINIO_IDENTITY_OPENID_CONFIG_URL=https://{zitadel_hostname}/.well-known/openid-configuration
            MINIO_IDENTITY_OPENID_CLIENT_ID={minio_dict['client_id']}
            MINIO_IDENTITY_OPENID_CLIENT_SECRET={minio_dict['client_secret']}
            MINIO_IDENTITY_OPENID_DISPLAY_NAME=zitadel
            MINIO_IDENTITY_OPENID_COMMENT="zitadelOIDC"
            MINIO_IDENTITY_OPENID_SCOPES="openid,email,groups"
            MINIO_IDENTITY_OPENID_CLAIM_NAME=groups
            MINIO_IDENTITY_OPENID_REDIRECT_URI={redirect_uris[0]}
                                   """}
        else:
            # creates the initial root credentials secret for the minio tenant
            credentials_exports = {
                    'config.env': f"""MINIO_ROOT_USER={access_key}
            MINIO_ROOT_PASSWORD={secret_key}"""}

        argocd.k8s.create_secret('default-tenant-env-config', 'minio',
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

    if not argo_app_exists:
        # actual installation of the minio tenant Argo CD Application
        argocd.install_app('minio-tenant', minio_config['argo'], True)


        # while we wait for the app to come up, update the config file
        if minio_init_enabled:
            create_minio_alias("minio-root",
                               minio_hostname,
                               access_key,
                               secret_key,
                               secure)

        if minio_init_enabled:
            # immediately create an admin and readonly policy
            minio_obj = BetterMinio('minio-root', minio_hostname,
                                    access_key, secret_key)
            # so that zitadel groups names match up with minio policy names
            minio_obj.create_admin_group_policy()
            minio_obj.create_read_user_group_policy()
    else:
        # if the minio tenant Argo CD app already exists, but init is enabed...
        if minio_init_enabled:
            if argo_app_exists and bitwarden:

                creds = bitwarden.get_item(
                        f'minio-tenant-root-credentials-{minio_hostname}'
                        )[0]['login']
                access_key = creds['username']
                secret_key = creds['password']

            return BetterMinio('minio-root',
                               minio_hostname,
                               access_key,
                               secret_key)


def create_minio_alias(minio_alias: str,
                       minio_hostname: str,
                       access_key: str,
                       secret_key: str,
                       secure: bool = True) -> None:
    """
    add minio alias for credentials to your local /home/.mc/config.json file
    """
    protocol = "https"
    if not secure:
        protocol = "http"

    # we create a config file so users can easily use minio from the cli
    new_minio_alias = {"url": f"{protocol}://{minio_hostname}",
                       "accessKey": access_key,
                       "secretKey": secret_key,
                       "api": "S3v4",
                       "path": "auto"}

    # if the user hasn't chosen a config location, we use XDG spec, maybe
    # xdg_minio_config_file = xdg_config_home() + "/minio/config.json"
    minio_config_dir = join(HOME_DIR, ".mc/")
    minio_config_file = join(minio_config_dir, "config.json")

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
                         "aliases": {minio_alias: new_minio_alias}}
    else:
        aliases = minio_cfg_obj.get("aliases", None)
        # if there is an aliases section with minio_alias, update it
        if aliases:
            minio_cfg_obj['aliases'][minio_alias] = new_minio_alias
        # if there is not an aliases section with minio_alias, create one
        else:
            minio_cfg_obj['aliases'] = {minio_alias: new_minio_alias}

    # write out the config file when we're done
    with open(minio_config_file, 'w') as minio_config_contents:
        dump(minio_cfg_obj, minio_config_contents)
