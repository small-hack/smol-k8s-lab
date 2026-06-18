# internal libraries
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_apps.operators.minio import create_minio_alias
from smol_k8s_lab.k8s_apps.identity_provider.zitadel_api import Zitadel
from smol_k8s_lab.k8s_tools.argocd_util import ArgoCD
from smol_k8s_lab.k8s_tools.restores import (restore_seaweedfs,
                                             k8up_restore_pvc,
                                             restore_cnpg_cluster)
from smol_k8s_lab.utils.passwords import create_password
from smol_k8s_lab.utils.rich_cli.console_logging import sub_header, header
from smol_k8s_lab.utils.run.subproc import subproc
from smol_k8s_lab.utils.value_from import extract_secret, process_backup_vals

# external libraries
import asyncio
import logging as log
from rich.prompt import Prompt


class install_custom_app():
    """
    install a custom smol-k8s-lab application

    This allows you to automatically setup the following:
        - an Argo CD Application

    Optionally we also setup:
        - OIDC using Zitadel
        - S3 credentials
        - PostgreSQL credentials
        - SMTP credentials
        - valkey credentials
        - an initial admin user/password
        - run custom script/function
    """
    def __init__(
            self,
            argocd: ArgoCD,
            app_cfg: dict,
            zitadel: Zitadel,
            bitwarden: BwCLI = BwCLI("test","test","test")
                 ) -> None:
        self.argocd = argocd
        self.zitadel = zitadel
        self.bitwarden = bitwarden
        # name of the app to install, used basically everywhere
        self.app_name = app_cfg["name"]
        self.app_hostname = app_cfg["hostname"]
        # check if init is even enabled
        self.init_enabled = app_cfg['init']['enabled']
        # check if we need to setup oidc
        self.oidc_cfg = app_cfg['init'].get('oidc', {'enabled': False})
        # placeholder for oidc credentials
        self.oidc_creds = {}
        # check if we need to setup a self-hosted S3
        self.s3_cfg = app_cfg['init'].get('s3', {'enabled': False})
        # check if we need to setup a postgresql database
        self.pgsql_cfg = app_cfg['init'].get('postgresql', {'enabled': False})
        # check if we need to setup a valkey cache
        self.valkey_cfg = app_cfg['init'].get('valkey', {'enabled': False})
        # this can be setup, restore, or sync
        self.app_phase = "setup"

        # check immediately if this app is installed
        app_installed = argocd.check_if_app_exists(self.app_name)

        if self.init_enabled and not app_installed:
            # setup an oidc app via zitadel if required
            if self.oidc_cfg['enabled']:
                self.setup_oidc(self)

            if bitwarden:
                self.setup_bitwarden_secrets()

    def setup_oidc(self) -> True:
        """
        setup OIDC application and groups known as roles in Zitadel
        (only Zitadel supported)

        TODO: this should take an OIDC struct of some sort that includes:
            - redirect_uris
            - logout_uris
            - hostname
            - if this supports an admin group or not
        """
        log.debug(f"Creating a {self.app_name} OIDC application in Zitadel...")

        # create an Application in Zitadel for this app
        self.oidc_creds = self.zitadel.create_application(
                self.app_name,
                self.oidc_cfg['redirect_uris'],
                self.oidc_cfg['logout_uris']
                )

        # create role (group) for regular app users
        self.zitadel.create_role(f"{self.app_name}_users",
                                 f"{self.app_name} Users",
                                 f"{self.app_name}_users")

        # create role (group) for admin app users
        self.zitadel.create_role(f"{self.app_name}_admins",
                                 f"{self.app_name} Admins",
                                 f"{self.app_name}_admins")

        # make sure the user running smol-k8s-lab in in the admins group
        self.zitadel.update_user_grant([f'{self.app_name}_admins'])

        return True

    def setup_s3(self) -> True:
        """
        setup S3 credentails and minio alias locally
        """
        s3_endpoint = self.s3_cfg['endpoint']

        # choose a random password for the S3 access key secret
        s3_access_key = create_password()

        # create a local alias to check and make sure nextcloud is functional
        create_minio_alias(minio_alias=self.app_name,
                           minio_hostname=s3_endpoint,
                           access_key=self.app_name,
                           secret_key=s3_access_key)
        return True


    def setup_bitwarden_secrets(self) -> True:
        """
        setup bitwarden and/or openbao secrets
        """
        hostname = self.app_hostname
        bw_id_dict = {}

        if self.s3_cfg['enabled']:
            s3_endpoint = self.s3_cfg['endpoint']

            # s3 credentials creation
            bucket_obj = create_custom_field('bucket', f'{self.app_name}-data')
            s3_access_key = create_password()
            endpoint_obj = create_custom_field('endpoint', s3_endpoint)
            s3_id = self.bitwarden.create_login(
                    name=f'{self.app_name}-user-s3-credentials',
                    item_url=hostname,
                    user=self.app_name,
                    password=s3_access_key,
                    fields=[bucket_obj, endpoint_obj]
                    )
            bw_id_dict[f'{self.app_name}_credentials_bitwarden_id'] = s3_id

            # TODO: Do we actually need this?
            admin_s3_key = create_password()
            s3_admin_id = self.bitwarden.create_login(
                    name=f'{self.app_name}-admin-s3-credentials',
                    item_url=hostname,
                    user=f"{self.app_name}-root",
                    password=admin_s3_key
                    )
            bw_id_dict[f'{self.app_name}_s3_admin_credentials_bitwarden_id'] = s3_admin_id

            # if we're also setting up postgresql, make sure it can backup to s3
            if self.pgsql_cfg['enabled']:
                pgsql_s3_key = create_password()
                s3_db_id = self.bitwarden.create_login(
                        name=f'{self.app_name}-postgres-s3-credentials',
                        item_url=hostname,
                        user=f"{self.app_name}-postgres",
                        password=pgsql_s3_key
                        )
                bw_id_dict[f'{self.app_name}_s3_postgres_credentials_bitwarden_id'] = s3_db_id


    def restore_app(self) -> True:
        """
        restore application
        """
        return True
