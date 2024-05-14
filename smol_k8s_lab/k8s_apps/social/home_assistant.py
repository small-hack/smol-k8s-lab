# function for creating the initial home assistant user

# internal libraries
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_tools.argocd_util import ArgoCD
from smol_k8s_lab.k8s_tools.restores import create_restic_restore_job
from smol_k8s_lab.utils.passwords import create_password
from smol_k8s_lab.utils.rich_cli.console_logging import sub_header, header
from smol_k8s_lab.utils.value_from import extract_secret, process_backup_vals

# external libraries
import logging as log


def configure_home_assistant(argocd: ArgoCD,
                             cfg: dict,
                             pvc_storage_class: str,
                             api_tls_verify: bool = False,
                             bitwarden: BwCLI = None) -> None:
    """
    creates a home-assistant app and initializes it with secrets if you'd like :)

    required:
        argocd      - ArgoCD() object for argo operations
        cfg - dictionary with at least argocd key and init key

    optional:
        bitwarden   - BwCLI() object with session token to create bitwarden items
    """
    # check immediately if this app is installed
    app_installed = argocd.check_if_app_exists('home-assistant')

    # get any secret keys passed in
    secrets = cfg['argo']['secret_keys']
    if secrets:
        home_assistant_hostname = secrets['hostname']

    # verify if initialization is enabled
    init_enabled = cfg['init']['enabled']

    # process restore dict
    restore_dict = cfg['init'].get('restore', {"enabled": False})
    restore_enabled = restore_dict['enabled']
    if restore_enabled:
        header_start = "Restoring"
    else:
        if app_installed:
            header_start = "Syncing"
        else:
            header_start = "Setting up"

    header(f"{header_start} [green]home-assistant[/], to self host your home automation",
           '🏡')

    # backups are their own config.yaml section
    backup_vals = process_backup_vals(cfg.get('backups', {}),
                                      'home_assistant',
                                      argocd)

    # we need namespace no matter the install type
    home_assistant_namespace = cfg['argo']['namespace']

    # if the user has chosen to use smol-k8s-lab initialization
    if not app_installed and init_enabled:
        # immediately create namespace
        argocd.k8s.create_namespace(home_assistant_namespace)

        # grab all possile init values
        init_values = cfg['init'].get('values', None)
        if init_values:
            admin_name = init_values.get('admin_name', 'admin')
            admin_user = init_values.get('admin_user', 'admin')
            admin_language = init_values.get('language', 'en')
            admin_password = extract_secret(init_values.get('password', ''))
            if not restore_enabled:
                if not admin_password:
                    admin_password = create_password()

        # if bitwarden is enabled, we create login items for each set of credentials
        if bitwarden and not restore_enabled:
            setup_bitwarden_items(argocd,
                                  home_assistant_hostname,
                                  admin_user,
                                  admin_name,
                                  admin_language,
                                  backup_vals['s3_user'],
                                  backup_vals['s3_password'],
                                  backup_vals['restic_repo_pass'],
                                  api_tls_verify,
                                  bitwarden)
        # these are standard k8s secrets
        else:
            # home-assistant admin credentials and smtp credentials
            argocd.k8s.create_secret('home-assistant-credentials',
                                     'home-assistant',
                                     {"ADMIN_USERNAME": admin_user,
                                      "ADMIN_NAME": admin_name,
                                      "ADMIN_PASSWORD": admin_password,
                                      "ADMIN_LANGUAGE": admin_language,
                                      "EXTERNAL_URL": home_assistant_hostname
                                      })

    if init_enabled and restore_enabled:
        restore_home_assistant(argocd,
                               secrets,
                               home_assistant_hostname,
                               home_assistant_namespace,
                               restore_dict,
                               backup_vals['endpoint'],
                               backup_vals['bucket'],
                               backup_vals['s3_user'],
                               backup_vals['s3_password'],
                               backup_vals['restic_repo_pass'],
                               pvc_storage_class,
                               app_installed,
                               bitwarden)

    if not app_installed:
        # then install the app as normal
        argocd.install_app('home-assistant', cfg['argo'])
    else:
        log.info("home-assistant already installed 🎉")

        # if bitwarden and init are enabled, make sure we populate appset secret
        # plugin secret with bitwarden item IDs
        if bitwarden and init_enabled:
            refresh_bitwarden(argocd, home_assistant_hostname, bitwarden)


def restore_home_assistant(argocd: ArgoCD,
                           secrets: dict,
                           home_assistant_hostname: str,
                           home_assistant_namespace: str,
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

    only works if using home_assistant app with init.enabled=True
    """
    if bitwarden:
        refresh_bitwarden(argocd, home_assistant_hostname, bitwarden)
        # apply the external secrets so we can immediately use them for restores
        external_secrets_yaml = (
                "https://raw.githubusercontent.com/small-hack/argocd-apps/"
                "main/home-assistant/toleration_and_affinity_app_of_apps/"
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
                             'home-assistant',
                             'home-assistant',
                             home_assistant_namespace,
                             secrets['pvc_capacity'],
                             'home-assistant-pvc',
                             s3_backup_endpoint,
                             s3_backup_bucket,
                             access_key_id,
                             secret_access_key,
                             restic_repo_password,
                             pvc_storage_class,
                             secrets.get('pvc_access_mode', 'ReadWriteOnce'),
                             restore_dict['restic_snapshot_ids']['home_assistant'],
                             '/config',
                             affinity,
                             tolerations)

    argocd.k8s.reload_deployment('home-assistant', home_assistant_namespace)


def setup_bitwarden_items(argocd: ArgoCD,
                          home_assistant_hostname: str,
                          admin_user: str,
                          admin_name: str,
                          admin_language: str,
                          backups_s3_user: str,
                          backups_s3_password: str,
                          restic_repo_pass: str,
                          api_tls_verify: bool,
                          bitwarden: BwCLI) -> None:
    """
    setup initial bitwarden items for home assistant
    """
    sub_header("Creating home-assistant items in Bitwarden")
    # determine if using https or http for home assistant api calls
    if api_tls_verify:
        external_url = 'https://' + home_assistant_hostname + '/'
    else:
        external_url = 'http://' + home_assistant_hostname + '/'
    external_url_field = create_custom_field('externalurl', external_url)

    # admin credentials for initial owner user
    admin_name_field = create_custom_field('name', admin_name)
    admin_lang_field = create_custom_field('language', admin_language)
    admin_password = bitwarden.generate()
    admin_id = bitwarden.create_login(
            name=f'home-assistant-admin-credentials-{home_assistant_hostname}',
            item_url=home_assistant_hostname,
            user=admin_user,
            password=admin_password,
            fields=[admin_name_field, admin_lang_field, external_url_field]
            )

    # credentials for remote backups of the s3 PVC
    restic_repo_pass_obj = create_custom_field("resticRepoPassword", restic_repo_pass)
    s3_backups_id = bitwarden.create_login(
            name='home-assistant-backups-s3-credentials',
            item_url=home_assistant_hostname,
            user=backups_s3_user,
            password=backups_s3_password,
            fields=[restic_repo_pass_obj]
            )

    # update the home-assistant values for the argocd appset
    argocd.update_appset_secret(
            {'home_assistant_admin_credentials_bitwarden_id': admin_id,
             'home_assistant_s3_backups_credentials_bitwarden_id': s3_backups_id}
            )


def refresh_bitwarden(argocd: ArgoCD,
                      home_assistant_hostname: str,
                      bitwarden: BwCLI) -> None:
    """
    refresh bitwardens item in the appset secret plugin
    """
    log.debug("Making sure home-assistant Bitwarden item IDs are in appset "
              "secret plugin secret")

    admin_id = bitwarden.get_item(
            f"home-assistant-admin-credentials-{home_assistant_hostname}"
            )[0]['id']

    s3_backups_id = bitwarden.get_item(
            f"home-assistant-backups-s3-credentials-{home_assistant_hostname}", False
            )[0]['id']

    argocd.update_appset_secret(
            {'home_assistant_admin_credentials_bitwarden_id': admin_id,
             'home_assistant_s3_backups_credentials_bitwarden_id': s3_backups_id}
            )
