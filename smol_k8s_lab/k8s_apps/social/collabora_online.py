# function for creating the initial home assistant user

# internal libraries
from smol_k8s_lab.bitwarden.bw_cli import BwCLI
from smol_k8s_lab.k8s_tools.argocd_util import ArgoCD
from smol_k8s_lab.k8s_tools.restores import create_restic_restore_job
from smol_k8s_lab.utils.passwords import create_password
from smol_k8s_lab.utils.rich_cli.console_logging import sub_header, header
from smol_k8s_lab.utils.value_from import extract_secret

# external libraries
import logging as log


def configure_collabora_online(argocd: ArgoCD,
                               cfg: dict,
                               pvc_storage_class: str,
                               bitwarden: BwCLI = None) -> None:
    """
    creates a collabora app and initializes it with secrets if you'd like :)

    required:
        argocd  - ArgoCD() object for argo operations
        cfg     - dictionary with at least argocd key and init key

    optional:
        bitwarden   - BwCLI() object with session token to create bitwarden items
    """
    # check immediately if this app is installed
    app_installed = argocd.check_if_app_exists('collabora-online')

    # get any secret keys passed in
    secrets = cfg['argo']['secret_keys']
    if secrets:
        collabora_hostname = secrets['hostname']

    # verify if initialization is enabled
    init_enabled = cfg['init']['enabled']

    # process restore dict
    # restore_dict = cfg['init'].get('restore', {"enabled": False})
    # restore_enabled = restore_dict['enabled']
    # if restore_enabled:
    #     header_start = "Restoring"
    # else:
    if app_installed:
        header_start = "Syncing"
    else:
        header_start = "Setting up"

    header(f"{header_start} [green]collabora-online[/], to self host your document service",
           '📄')

    # backups are their own config.yaml section
    # backup_vals = process_backup_vals(cfg.get('backups', {}),
    #                                   'collabora_online',
    #                                   argocd)

    # we need namespace no matter the install type
    collabora_namespace = cfg['argo']['namespace']

    # if the user has chosen to use smol-k8s-lab initialization
    if not app_installed and init_enabled:
        # immediately create namespace
        argocd.k8s.create_namespace(collabora_namespace)

        # grab all possile init values
        init_values = cfg['init'].get('values', None)
        if init_values:
            admin_user = init_values.get('admin_user', 'admin')
            admin_password = extract_secret(init_values.get('password',
                                                            create_password()))

        # if bitwarden is enabled, we create login items for each set of credentials
        # if bitwarden and not restore_enabled:
        if bitwarden:
            #                     backup_vals['s3_user'],
            #                     backup_vals['s3_password'],
            #                     backup_vals['restic_repo_pass'],
            setup_collabora_bitwarden_items(argocd,
                                            collabora_hostname,
                                            admin_user,
                                            admin_password,
                                            bitwarden)
        # these are standard k8s secrets
        else:
            # collabora admin credentials and smtp credentials
            argocd.k8s.create_secret('collabora-credentials',
                                     collabora_namespace,
                                     {"ADMIN_USERNAME": admin_user,
                                      "ADMIN_PASSWORD": admin_password})

    # if init_enabled and restore_enabled:
    #     restore_collabora(argocd,
    #                       secrets,
    #                       collabora_hostname,
    #                       collabora_namespace,
    #                       restore_dict,
    #                       backup_vals['endpoint'],
    #                       backup_vals['bucket'],
    #                       backup_vals['s3_user'],
    #                       backup_vals['s3_password'],
    #                       backup_vals['restic_repo_pass'],
    #                       pvc_storage_class,
    #                       app_installed,
    #                       bitwarden)

    if not app_installed:
        # then install the app as normal
        argocd.install_app('collabora-online', cfg['argo'])
    else:
        log.info("collabora-online already installed 🎉")

        # if bitwarden and init are enabled, make sure we populate appset secret
        # plugin secret with bitwarden item IDs
        if bitwarden and init_enabled:
            refresh_collabora_bitwarden(argocd, collabora_hostname, bitwarden)


def restore_collabora(argocd: ArgoCD,
                      secrets: dict,
                      collabora_hostname: str,
                      collabora_namespace: str,
                      restore_dict: dict,
                      s3_backup_endpoint: str,
                      s3_backup_bucket: str,
                      access_key_id: str,
                      secret_access_key: str,
                      restic_repo_password: str,
                      pvc_storage_class: str,
                      app_installed: bool,
                      bitwarden: BwCLI) -> None:
    """
    restore home assistant's external secrets and PVC, then if app_installed=True,
    reload the deployment and if not just end the function

    only works if using collabora app with init.enabled=True
    """
    if bitwarden:
        refresh_collabora_bitwarden(argocd, collabora_hostname, bitwarden)
        # apply the external secrets so we can immediately use them for restores
        external_secrets_yaml = (
                "https://raw.githubusercontent.com/small-hack/argocd-apps/"
                "main/collabora/toleration_and_affinity_app_of_apps/"
                "external_secrets_argocd_appset.yaml"
                )
        argocd.k8s.apply_manifests(external_secrets_yaml, argocd.namespace)

    if secrets['affinity_key']:
        affinity = {"nodeAffinity": {
                      "requiredDuringSchedulingIgnoredDuringExecution": {
                        "nodeSelectorTerms": [
                          {"matchExpressions": [{"key": secrets['affinity_key'],
                                                 "operator": "In",
                                                 "values": [secrets['affinity_value']]}]}
                        ]
                      }
                    }
                  }
    else:
        affinity = {}

    if secrets['toleration_key']:
        tolerations = [{"effect": secrets['toleration_effect'],
                        "key": secrets['toleration_key'],
                        "operator": secrets['toleration_operator'],
                        "value": secrets['toleration_value']}]
    else:
        tolerations = {}

    # recreates the PVC and runs a k8s restic restore job to populate it
    create_restic_restore_job(argocd.k8s,
                             'collabora',
                             'collabora',
                             collabora_namespace,
                             secrets['pvc_capacity'],
                             'collabora-pvc',
                             s3_backup_endpoint,
                             s3_backup_bucket,
                             access_key_id,
                             secret_access_key,
                             restic_repo_password,
                             pvc_storage_class,
                             secrets.get('pvc_access_mode', 'ReadWriteOnce'),
                             restore_dict['restic_snapshot_ids']['collabora'],
                             '/config',
                             affinity,
                             tolerations)

    argocd.k8s.reload_deployment('collabora', collabora_namespace)


def setup_collabora_bitwarden_items(argocd: ArgoCD,
                                    collabora_hostname: str,
                                    admin_user: str,
                                    admin_pass: str,
                                    bitwarden: BwCLI) -> None:
    """
    setup initial bitwarden items for home assistant

    possible future args:
                          backups_s3_user: str,
                          backups_s3_password: str,
                          restic_repo_pass: str,
    """
    sub_header("Creating collabora items in Bitwarden")

    # admin credentials for initial owner user
    admin_id = bitwarden.create_login(
            name=f'collabora-admin-credentials-{collabora_hostname}',
            item_url=collabora_hostname,
            user=admin_user,
            password=admin_pass
            )

    # credentials for remote backups of the s3 PVC
    # restic_repo_pass_obj = create_custom_field("resticRepoPassword", restic_repo_pass)
    # s3_backups_id = bitwarden.create_login(
    #         name='collabora-backups-s3-credentials',
    #         item_url=collabora_hostname,
    #         user=backups_s3_user,
    #         password=backups_s3_password,
    #         fields=[restic_repo_pass_obj]
    #         )

    # update the collabora values for the argocd appset
    # 'collabora_s3_backups_credentials_bitwarden_id': s3_backups_id}
    argocd.update_appset_secret({'collabora_admin_credentials_bitwarden_id': admin_id})


def refresh_collabora_bitwarden(argocd: ArgoCD,
                      collabora_hostname: str,
                      bitwarden: BwCLI) -> None:
    """
    refresh bitwardens item in the appset secret plugin
    """
    log.debug("Making sure collabora Bitwarden item IDs are in appset "
              "secret plugin secret")

    admin_id = bitwarden.get_item(
            f"collabora-admin-credentials-{collabora_hostname}"
            )[0]['id']

    # s3_backups_id = bitwarden.get_item(
    #         f"collabora-backups-s3-credentials-{collabora_hostname}", False
    #         )[0]['id']

    # 'collabora_s3_backups_credentials_bitwarden_id': s3_backups_id}
    argocd.update_appset_secret(
            {'collabora_admin_credentials_bitwarden_id': admin_id}
            )
