# internal libraries
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_tools.argocd_util import ArgoCD
from smol_k8s_lab.k8s_tools.restores import k8up_restore_pvc
from smol_k8s_lab.utils.rich_cli.console_logging import sub_header, header
from smol_k8s_lab.utils.run.subproc import subproc
from smol_k8s_lab.utils.value_from import process_backup_vals

# external libraries
import asyncio
import logging as log


async def configure_jellyfin(
        argocd: ArgoCD,
        cfg: dict,
        pvc_storage_class: str,
        bitwarden: BwCLI = BwCLI("test","test","test")
        ) -> None:
    """
    creates a jellyfin app and initializes it with secrets if you'd like :)

    required:
        argocd            - ArgoCD() object for Argo CD operations
        cfg               - dict, with at least argocd key and init key
        pvc_storage_class - str, storage class of PVC

    optional:
        bitwarden   - BwCLI() object with session token to create bitwarden items
    """
    # check immediately if this app is installed
    app_installed = argocd.check_if_app_exists('jellyfin')

    # get any secret keys passed in
    secrets = cfg['argo']['secret_keys']
    if secrets:
        jellyfin_hostname = secrets['hostname']

        # make sure the pvc secrets are set correctly
        storage_class_secrets = {}

        # verify each configurable PVC has an associated secret
        for pvc in ['media', 'config']:
            storage_class = secrets.get(f"{pvc}_storage_class", None)
            if not storage_class:
                storage_class_secrets[f"jellyfin_{pvc}_storage_class"] = pvc_storage_class

        if storage_class_secrets:
            argocd.update_appset_secret(storage_class_secrets)

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

    header(f"{header_start} [green]Jellyfin[/], your home media server", '🪼')

    if init_enabled:
        # backups are their own config.yaml section
        backup_vals = process_backup_vals(cfg.get('backups', {}), 'jellyfin', argocd)

    # if the user has chosen to use smol-k8s-lab initialization
    if not app_installed and init_enabled:
        jellyfin_namespace = cfg['argo']['namespace']
        argocd.k8s.create_namespace(jellyfin_namespace)

        # if bitwarden is enabled, we create login items for each set of credentials
        if bitwarden and not restore_enabled:
            setup_bitwarden_items(argocd,
                                  jellyfin_hostname,
                                  backup_vals['s3_user'],
                                  backup_vals['s3_password'],
                                  backup_vals['restic_repo_pass'],
                                  bitwarden)

    if not app_installed:
        # if the user is restoring, the process is a little different
        if init_enabled and restore_enabled:
            restore_jellyfin(argocd,
                             jellyfin_hostname,
                             jellyfin_namespace,
                             cfg['argo'],
                             secrets,
                             restore_dict,
                             backup_vals,
                             pvc_storage_class,
                             'jellyfin-postgres',
                             bitwarden)
        else:
            argocd.install_app('jellyfin', cfg['argo'])
    else:
        log.info("jellyfin already installed 🎉")
        if bitwarden and init_enabled:
            refresh_bweso(argocd, jellyfin_hostname, bitwarden)


def restore_jellyfin(argocd: ArgoCD,
                     jellyfin_hostname: str,
                     jellyfin_namespace: str,
                     argo_dict: dict,
                     secrets: dict,
                     restore_dict: dict,
                     backup_dict: dict,
                     global_pvc_storage_class: str,
                     bitwarden: BwCLI) -> None:
    """
    restore jellyfin seaweedfs PVCs, jellyfin files and/or config PVC(s),
    and CNPG postgresql cluster
    """
    # this is the info for the REMOTE backups
    s3_backup_endpoint = backup_dict['endpoint']
    s3_backup_bucket = backup_dict['bucket']
    access_key_id = backup_dict["s3_user"]
    secret_access_key = backup_dict["s3_password"]
    restic_repo_password = backup_dict['restic_repo_pass']

    # get argo git repo info
    revision = argo_dict['revision']
    argo_path = argo_dict['path']

    # first we grab existing bitwarden items if they exist
    if bitwarden:
        refresh_bweso(argocd, jellyfin_hostname, bitwarden)

        # apply the external secrets so we can immediately use them for restores
        external_secrets_yaml = (
                f"https://raw.githubusercontent.com/small-hack/argocd-apps/{revision}/"
                f"{argo_path}external_secrets_argocd_appset.yaml"
                )
        argocd.k8s.apply_manifests(external_secrets_yaml, argocd.namespace)

    # then we create all the seaweedfs pvcs we lost and restore them
    snapshot_ids = restore_dict['restic_snapshot_ids']

    podconfig_yaml = (
            f"https://raw.githubusercontent.com/small-hack/argocd-apps/{revision}/"
            f"{argo_path}pvc_argocd_appset.yaml"
            )
    argocd.k8s.apply_manifests(podconfig_yaml, argocd.namespace)

    # then we begin the restic restore of all the jellyfin PVCs we lost
    for pvc in ['media', 'config']:
        pvc_enabled = secrets.get(f'{pvc}_pvc_enabled', 'false')
        if pvc_enabled and pvc_enabled.lower() != 'false':
            # restores the jellyfin pvc
            k8up_restore_pvc(argocd.k8s,
                             'jellyfin',
                             f'jellyfin-{pvc}',
                             'jellyfin',
                             s3_backup_endpoint,
                             s3_backup_bucket,
                             access_key_id,
                             secret_access_key,
                             restic_repo_password,
                             snapshot_ids[f'jellyfin_{pvc}'],
                             "file-backups-podconfig"
                             )

    # todo: from here on out, this could be async to start on other tasks
    # install jellyfin as usual, but wait on it this time
    argocd.install_app('jellyfin', argo_dict, True)

    # verify jellyfin rolled out completely, just in case
    rollout = (f"kubectl rollout status -n {jellyfin_namespace} "
               "deployment/jellyfin-web-app --watch --timeout 10m")
    while True:
        rolled_out = subproc([rollout], error_ok=True)
        if "NotFound" not in rolled_out:
            break

    # try to update the maintenance mode of jellyfin to off
    jellyfin_obj = jellyfin(argocd.k8s, jellyfin_namespace)
    jellyfin_obj.set_maintenance_mode("off")


def setup_bitwarden_items(argocd: ArgoCD,
                          jellyfin_hostname: str,
                          backups_s3_user: str,
                          backups_s3_password: str,
                          restic_repo_pass: str,
                          bitwarden: BwCLI) -> None:
    """
    setup all the bitwarden items for jellyfin external secrets to be populated
    """
    sub_header("Creating jellyfin items in Bitwarden")

    # credentials for remote backups of the s3 PVC
    restic_repo_pass_obj = create_custom_field("resticRepoPassword", restic_repo_pass)
    s3_backups_id = bitwarden.create_login(
            name='jellyfin-backups-s3-credentials',
            item_url=jellyfin_hostname,
            user=backups_s3_user,
            password=backups_s3_password,
            fields=[restic_repo_pass_obj]
            )

    # update the jellyfin values for the argocd appset
    argocd.update_appset_secret(
            {'jellyfin_s3_backups_credentials_bitwarden_id': s3_backups_id})


def refresh_bweso(argocd: ArgoCD,
                  jellyfin_hostname: str,
                  bitwarden: BwCLI) -> None:
    """
    if bitwarden and init are enabled, but app is already installed, make sure
    we populate appset secret plugin secret with jellyfin bitwarden item IDs
    """
    log.debug("Making sure jellyfin Bitwarden item IDs are in appset "
              "secret plugin secret")

    s3_backups_id = bitwarden.get_item(
            f"jellyfin-backups-s3-credentials-{jellyfin_hostname}", False
            )[0]['id']

    argocd.update_appset_secret(
            {'jellyfin_s3_backups_credentials_bitwarden_id': s3_backups_id})
