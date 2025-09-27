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
                            bitwarden: BwCLI = BwCLI("test","test","test")) -> None:
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
    init_enabled = cfg['init']['enabled']

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
        juicefs_hostname = secrets.get('hostname', "")
        juicefs_valkey_pvc_storage_class = secrets.get('valkey_pvc_storage_class', "")
        juicefs_valkey_pvc_size = secrets.get('valkey_pvc_size', "")

    if init_enabled:
        # declare custom values for juicefs
        init_values = init.get('values', None)

        # backups are their own config.yaml section
        backup_vals = process_backup_vals(cfg.get('backups', {}), 'juicefs', argocd)

    # initial secrets to deploy this app from scratch
    if init_enabled and not app_installed:
         # declare custom values
         init_values = init.get('values', None)
         backup_vals = process_backup_vals(cfg.get('backups', {}), 'juicefs', argocd)

         # configure the s3 credentials
         s3_access_key_id = extract_secret(init_values.get('access_key_id', ""))
         s3_secret_access_key = extract_secret(init_values.get('secret_access_key', ""))
         bucket_name = extract_secret(init_values.get('bucket_name', ""))
         s3_url = extract_secret(init_values.get('s3_url', ""))

         # create s3 secret in bitwarden
         if bitwarden and not restore_enabled:
            setup_bitwarden_items(argocd,
                                  juicefs_hostname,
                                  s3_url,
                                  s3_access_key_id,
                                  s3_secret_access_key,
                                  bucket_name,
                                  backup_vals['s3_user'],
                                  backup_vals['s3_password'],
                                  backup_vals['restic_repo_pass'],
                                  juicefs_valkey_pvc_size,
                                  juicefs_valkey_pvc_storage_class,
                                  bitwarden)

def setup_bitwarden_items(argocd: ArgoCD,
                          juicefs_hostname: str,
                          s3_url: str,
                          s3_access_key_id: str,
                          s3_secret_access_key: str,
                          bucket_name: str,
                          backups_s3_user: str,
                          backups_s3_password: str,
                          restic_repo_pass: str,
                          juicefs_valkey_pvc_size: str,
                          juicefs_valkey_pvc_storage_class: str,
                          bitwarden: BwCLI) -> None:
    """
    setup secrets in bitwarden for juicefs.
    """

    # S3 credentials
    # endpoint that gets put into the secret should probably have http in it
    if "http" not in s3_url:
        log.debug(f"juicefs s3_url did not have http in it: {s3_url}")
        s3_url = "https://" + s3_url
        log.debug(f"juicefs s3_url - after prepending 'https://': {s3_url}")

    juicefs_s3_endpoint_obj = create_custom_field("s3Endpoint", s3_url)

    juicefs_s3_host_obj = create_custom_field("s3Hostname",
                                               s3_url.replace("https://",
                                                                   ""))

    juicefs_s3_bucket_obj = create_custom_field("s3Bucket", bucket_name)

    s3_id = bitwarden.create_login(
            name='juicefs-s3-credentials',
            item_url=juicefs_hostname,
            user=s3_access_key_id,
            password=s3_secret_access_key,
            fields=[
                juicefs_s3_endpoint_obj,
                juicefs_s3_host_obj,
                juicefs_s3_bucket_obj
                ]
            )

    # credentials for remote backups of the s3 PVC
    restic_repo_pass_obj = create_custom_field("resticRepoPassword", restic_repo_pass)
    s3_backups_id = bitwarden.create_login(
            name='juicefs-backups-s3-credentials',
            item_url=juicefs_hostname,
            user=backups_s3_user,
            password=backups_s3_password,
            fields=[restic_repo_pass_obj]
            )

    # set a password for valkey
    juicefs_valkey_password = bitwarden.generate()

    # create the valkey secret in bitwarden
    valkey_id = bitwarden.create_login(
       name='juicefs-valkey-credentials',
       item_url=juicefs_hostname,
       user='valkey',
       password=juicefs_valkey_password
       )

    # update the juicefs values for the argocd appset
    argocd.update_appset_secret(
            {'juicefs_s3_credentials_bitwarden_id': s3_id,
             'juicefs_s3_backups_credentials_bitwarden_id': s3_backups_id,
             'juicefs_valkey_credentials_bitwarden_id': valkey_id,
             'juicefs_valkey_pvc_storage_class': juicefs_valkey_pvc_storage_class,
             'juicefs_valkey_pvc_size': juicefs_valkey_pvc_size
             }
            )

    # reload the bitwarden ESO provider
    try:
        argocd.k8s.reload_deployment('bitwarden-eso-provider',
                                     'external-secrets')
    except Exception as e:
        log.error(
                "Couldn't scale down the [magenta]bitwarden-eso-provider"
                "[/] deployment in [green]external-secrets[/] namespace."
                f"Recieved: {e}"
                )
