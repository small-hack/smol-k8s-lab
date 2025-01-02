# internal libraries
from smol_k8s_lab.bitwarden.bw_cli import BwCLI
from smol_k8s_lab.k8s_tools.argocd_util import ArgoCD
from smol_k8s_lab.k8s_tools.restores import k8up_restore_pvc
from smol_k8s_lab.utils.passwords import create_password
from smol_k8s_lab.utils.rich_cli.console_logging import header
# from smol_k8s_lab.utils.value_from import process_backup_vals

# external libraries
import logging as log


def configure_valkey(argocd: ArgoCD,
                     cfg: dict,
                     bitwarden: BwCLI = None) -> bool:
    """
    creates a valkey app and initializes it with secrets if you'd like :)

    required:
        argocd                 - ArgoCD() object for Argo CD operations
        cfg                    - dict, with at least argocd key and init key

    optional:
        bitwarden   - BwCLI() object with session token to create bitwarden items

    coming soon:
        pvc_storage_class      - str, storage class of PVC
    """
    # check immediately if the app is installed
    app_installed = argocd.check_if_app_exists('valkey')

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

    header(f"{header_start} [green]valkey[/], so you can have a key/value store",
           '💿')

    # get any secrets for this app
    # secrets = cfg['argo']['secret_keys']

    # we need namespace immediately
    valkey_namespace = cfg['argo']['namespace']

    # if init_enabled:
    #    # backups are their own config.yaml section
    #     backup_vals = process_backup_vals(cfg.get('backups', {}), 'valkey', argocd)

    if init_enabled and not app_installed:
        argocd.k8s.create_namespace(valkey_namespace)

        if bitwarden and not restore_enabled:
            setup_bitwarden_items(argocd, bitwarden)

        # these are standard k8s secrets yaml
        elif not bitwarden and not restore_enabled:
            # valkey creds k8s secret
            valkey_password = create_password()
            argocd.k8s.create_secret('valkey-credentials', 'valkey',
                                     {"password": valkey_password})

    if not app_installed:
        # restore not supported yet
        # if restore_enabled:
        #     restore_valkey(argocd,
        #                    valkey_namespace,
        #                    cfg['argo'],
        #                    secrets,
        #                    restore_dict,
        #                    backup_vals,
        #                    pvc_storage_class,
        #                    bitwarden)

        if not init_enabled:
            argocd.install_app('valkey', cfg['argo'])
    else:
        log.info("valkey already installed 🎉")

        if bitwarden and init_enabled:
            refresh_bweso(argocd, bitwarden)


def refresh_bweso(argocd: ArgoCD, bitwarden: BwCLI) -> None:
    """
    if valkey already installed, but bitwarden and init are enabled, still
    populate the bitwarden IDs in the appset secret plugin secret
    """
    log.debug("Making sure valkey Bitwarden item IDs are in appset "
              "secret plugin secret")


    secrets_id = bitwarden.get_item("valkey-credentials-smol-k8s-lab", False)[0]['id']

    # {'valkey_admin_credentials_bitwarden_id': admin_id,
    argocd.update_appset_secret({'valkey_secret_bitwarden_id': secrets_id})


def setup_bitwarden_items(argocd: ArgoCD,
                          bitwarden: BwCLI) -> None:
    # valkey credentials
    valkey_password = bitwarden.generate()
    valkey_id = bitwarden.create_login(
            name='valkey-credentials-smol-k8s-lab',
            item_url="valkey.io",
            user='valkey',
            password=valkey_password
            )

    # update the valkey values for the argocd appset
    argocd.update_appset_secret({'valkey_valkey_bitwarden_id': valkey_id})

    # reload the bitwarden ESO provider
    try:
        argocd.k8s.reload_deployment('bitwarden-eso-provider', 'external-secrets')
    except Exception as e:
        log.error(
                "Couldn't scale down the [magenta]bitwarden-eso-provider"
                "[/] deployment in [green]external-secrets[/] namespace."
                f"Recieved: {e}"
                )


def restore_valkey(argocd: ArgoCD,
                   valkey_hostname: str,
                   valkey_namespace: str,
                   argo_dict: dict,
                   secrets: dict,
                   restore_dict: dict,
                   backup_dict: dict,
                   global_pvc_storage_class: str,
                   pgsql_cluster_name: str,
                   bitwarden: BwCLI) -> None:
    """
    restore valkey seaweedfs PVCs, valkey files and/or config PVC(s),
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
        refresh_bweso(argocd, bitwarden)

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

    # then we begin the restic restore of all the valkey PVCs we lost
    for pvc in ['valkey_primary', 'valkey_replica']:
        pvc_enabled = secrets.get('valkey_pvc_enabled', 'false')
        if pvc_enabled and pvc_enabled.lower() != 'false':
            # restores the valkey pvc
            k8up_restore_pvc(
                    k8s_obj=argocd.k8s,
                    app='valkey',
                    pvc=f'valkey-{pvc.replace("_","-")}',
                    namespace='valkey',
                    s3_endpoint=s3_backup_endpoint,
                    s3_bucket=s3_backup_bucket,
                    access_key_id=access_key_id,
                    secret_access_key=secret_access_key,
                    restic_repo_password=restic_repo_password,
                    snapshot_id=snapshot_ids[f'valkey_{pvc}'],
                    pod_config="file-backups-podconfig"
                    )

    # todo: from here on out, this could be async to start on other tasks
    # install valkey as usual, but wait on it this time
    argocd.install_app('valkey', argo_dict, True)
