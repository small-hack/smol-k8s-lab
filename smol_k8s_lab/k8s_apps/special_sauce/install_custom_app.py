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
        self.app_name = app_cfg["name"]
        self.oidc_creds = {}
        self.zitadel = zitadel
        # check if init is even enabled
        self.init_enabled = app_cfg['init']['enabled']
        # check if we need to setup oidc
        self.oidc_cfg = app_cfg['init'].get('oidc', {'enabled': False})
        # this can be setup, restore, or sync
        self.app_phase = "setup"

        # check immediately if this app is installed
        app_installed = argocd.check_if_app_exists(self.app_name)

        if self.init_enabled and not app_installed:
            # setup an oidc app via zitadel if required
            if self.oidc_cfg['enabled']:
                self.setup_oidc(self)

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
        setup minio alias
        """
        s3_access_key = create_password()
        # create a local alias to check and make sure nextcloud is functional
        create_minio_alias(minio_alias=self.app_name,
                           minio_hostname=s3_endpoint,
                           access_key=self.app_name,
                           secret_key=s3_access_key)
        return True

    def restore_app(self) -> True:
        """
        restore application
        """
        return True
