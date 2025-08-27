# internal libraries
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_tools.argocd_util import ArgoCD
from smol_k8s_lab.k8s_tools.restores import (restore_seaweedfs,
                                             k8up_restore_pvc,
                                             restore_cnpg_cluster)
from smol_k8s_lab.utils.passwords import create_password
from smol_k8s_lab.utils.rich_cli.console_logging import header
from smol_k8s_lab.utils.value_from import extract_secret, process_backup_vals

# external libraries
import logging as log


async def configure_juicefs(argocd: ArgoCD,
                            cfg: dict,
                            pvc_storage_class: str,
                            zitadel: Zitadel,
                            bitwarden: BwCLI = BwCLI("test","test","test")
                            ) -> bool:
    """
    creates a juicefs app and initializes it with secrets from enva vars

    required:
        argocd                 - ArgoCD() object for Argo CD operations
        cfg                    - dict, with at least argocd key and init key
        pvc_storage_class      - str, storage class of PVC

    optional:
        zitadel     - Zitadel() object with session token to create zitadel oidc app and roles
        bitwarden   - BwCLI() object with session token to create bitwarden items
    """

    # check immediately if the app is installed
    app_installed = argocd.check_if_app_exists('juicefs')

    # verify if initialization is enabled
    init = cfg.get('init', {'enabled': True, 'restore': {'enabled': False}})
    init_enabled = init.get('enabled', True)

    # check if we're restoring and get values for that
    restore_dict = init.get('restore', {"enabled": False})
    restore_enabled = restore_dict['enabled']

    # figure out what header to print
    if restore_enabled:
        header_start = "Restoring"
    else:
        if app_installed:
            header_start = "Syncing"
        else:
            header_start = "Setting up"

    header(f"{header_start} [green]juicefs[/], high-prformance network-backed storage!",
           '🧃📂')

    # get any secrets for this app
    secrets = cfg['argo']['secret_keys']
    if secrets:
        forgejo_hostname = secrets['hostname']


