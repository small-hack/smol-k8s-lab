from json import load, dump, dumps
import logging as log
from os.path import exists, join
from os import makedirs
from minio import Minio, MinioAdmin
from minio.credentials.providers import MinioClientConfigProvider
from shutil import which

from smol_k8s_lab.constants import HOME_DIR, XDG_CACHE_DIR
from smol_k8s_lab.bitwarden.bw_cli import BwCLI
from smol_k8s_lab.k8s_apps.identity_provider.zitadel_api import Zitadel
from smol_k8s_lab.k8s_tools.argocd_util import ArgoCD
from smol_k8s_lab.utils.passwords import create_password
from smol_k8s_lab.utils.run.subproc import subproc


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
        minio_config_dir = join(HOME_DIR, ".mc/")
        minio_config_file = join(minio_config_dir, "config.json")
        log.debug(f"Checking for config file in {minio_config_file}")
        minio_provider = MinioClientConfigProvider(minio_config_file, minio_alias)
        self.admin_client = MinioAdmin(api_hostname, minio_provider)
        self.client = Minio(api_hostname, access_key, secret_key)

    def get_object(self, bucket: str, s3_object: str, save_file: str = ""):
        """
        get an s3_object from an s3 endpoint
        """
        if not save_file:
            file_name = s3_object.split("/")[-1]
            save_file = join(XDG_CACHE_DIR, f"smol-k8s-lab/{file_name}")

        return self.client.fget_object(bucket, s3_object, save_file)

    def list_object(self,
                    bucket: str,
                    s3_object_path: str = "",
                    recursive: bool = False):
        """
        list an s3_object dir from an s3 endpoint
        """
        obj_args = {"bucket_name": bucket,
                    "prefix": s3_object_path,
                    "recursive": recursive}

        return self.client.list_objects(**obj_args)

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
            policy_name = self.create_bucket_policy(bucket_name)
            self.admin_client.policy_set(policy_name, access_key)
        else:
            log.info(f'Bucket "{bucket_name}" already exists')

    def create_bucket_policy(self, bucket: str) -> str:
        """
        creates a readwrite policy for a given bucket and returns the policy name
        """
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetBucketLocation",
                        "s3:GetObject",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{bucket}",
                        f"arn:aws:s3:::{bucket}/*"
                    ]
                }
            ]
        }

        # we write out the policy, because minio admin client requires it
        policy_file_name = XDG_CACHE_DIR + f'minio_{bucket}_policy.json'
        with open(policy_file_name, 'w') as policy_file:
            dump(policy, policy_file)

        # actually create the policy
        policy_name = f'{bucket}BucketReadWrite'
        self.admin_client.policy_add(policy_name, policy_file_name)

        return policy_name

    def create_admin_group_policy(self) -> None:
        """
        creates an admin policy for OIDC called minio_admins
        """
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "admin:*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "kms:*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:*"
                    ],
                    "Resource": [
                        "arn:aws:s3:::*"
                    ]
                }
            ]
        }

        # we write out the policy, because minio admin client requires it
        policy_file_name = XDG_CACHE_DIR + 'minio_oidc_admin_policy.json'
        with open(policy_file_name, 'w') as policy_file:
            dump(policy, policy_file)

        # actually create the policy
        self.admin_client.policy_add('minio_admins', policy_file_name)
        log.info("Created minio_admin policy for use with OIDC")

    def create_read_user_group_policy(self) -> None:
        """
        creates a readonly policy for OIDC called minio_read_users
        """
        policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "s3:GetBucketLocation",
                            "s3:GetObject"
                            ],
                        "Resource": [
                            "arn:aws:s3:::*"
                            ]
                        }
                    ]
                }

        # we write out the policy, because minio admin client requires it
        policy_file_name = XDG_CACHE_DIR + 'minio_oidc_user_readonly_policy.json'
        with open(policy_file_name, 'w') as policy_file:
            dump(policy, policy_file)

        # actually create the policy
        self.admin_client.policy_add('minio_read_users', policy_file_name)
        log.info("Created minio_read only user policy for use with OIDC")

    def set_anonymous_download(self, bucket: str, prefix: str) -> None:
        """
        sets anonymous download on a particular bucket and folder
        """
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:GetBucketLocation"],
                    "Resource": f"arn:aws:s3:::{bucket}",
                },
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:ListBucket"],
                    "Condition": {
                        "StringEquals": {"s3:prefix": [prefix]}
                    },
                    "Resource": f"arn:aws:s3:::{bucket}",
                },
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket}/{prefix}*",
                },
            ],
        }

        self.client.set_bucket_policy(bucket, dumps(policy))


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
