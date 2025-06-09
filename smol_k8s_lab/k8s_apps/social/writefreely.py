# internal libraries
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_apps.operators.minio import create_minio_alias
from smol_k8s_lab.k8s_apps.identity_provider.zitadel_api import Zitadel
from smol_k8s_lab.k8s_tools.argocd_util import ArgoCD
from smol_k8s_lab.k8s_tools.restores import (restore_seaweedfs,
                                             k8up_restore_pvc)
from smol_k8s_lab.utils.passwords import create_password
from smol_k8s_lab.utils.rich_cli.console_logging import sub_header, header
from smol_k8s_lab.utils.run.subproc import subproc
from smol_k8s_lab.utils.value_from import extract_secret, process_backup_vals

# external libraries
import logging as log


def configure_writefreely(argocd: ArgoCD,
                    cfg: dict,
                    pvc_storage_class: str,
                    zitadel: Zitadel = None,
                    bitwarden: BwCLI = None) -> bool:
    """
    creates a writefreely app and initializes it with secrets if you'd like :)

    required:
        argocd                 - ArgoCD() object for Argo CD operations
        cfg                    - dict, with at least argocd key and init key
        pvc_storage_class      - str, storage class of PVC

    optional:
        zitadel     - Zitadel() object with session token to create zitadel oidc app and roles
        bitwarden   - BwCLI() object with session token to create bitwarden items
    """
    # check immediately if the app is installed
    app_installed = argocd.check_if_app_exists('writefreely')

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

    header(f"{header_start} [green]writefreely[/], so you can self host your own blogging platform",
           '👻')

    # get any secrets for this app
    secrets = cfg['argo']['secret_keys']
    if secrets:
        writefreely_hostname = secrets['hostname']

    # we need namespace immediately
    writefreely_namespace = cfg['argo']['namespace']

    if init_enabled:
        # declare custom values for writefreely
        init_values = init.get('values', None)

        # backups are their own config.yaml section
        backup_vals = process_backup_vals(cfg.get('backups', {}), 'writefreely', argocd)

    if init_enabled and not app_installed:
        argocd.k8s.create_namespace(writefreely_namespace)

        if not restore_enabled:
            # configure the admin user credentials
            writefreely_admin_username = init_values.get('admin_user', 'tootadmin')
            writefreely_admin_email = init_values.get('admin_email', '')

            # configure the smtp credentials
            mail_user = init_values.get('smtp_user', '')
            mail_host = init_values.get('smtp_host', '')
            mail_port = init_values.get('smtp_port', '')
            mail_pass = extract_secret(init_values.get('smtp_password'))

            # configure s3 credentials
            s3_access_id = 'writefreely'
            s3_access_key = create_password()

        # configure OIDC
        if zitadel and not restore_enabled:
            log.debug("Creating a writefreely OIDC application in Zitadel...")
            redirect_uris = f"https://{writefreely_hostname}/auth/callback"
            logout_uris = [f"https://{writefreely_hostname}"]
            oidc_creds = zitadel.create_application(
                    "writefreely",
                    redirect_uris,
                    logout_uris
                    )
            zitadel.create_role("writefreely_users",
                                "writefreely Users",
                                "writefreely_users")
            zitadel.create_role("writefreely_admins",
                                "writefreely Admins",
                                "writefreely_admins")
            zitadel.update_user_grant(['writefreely_admins'])
            zitadel_hostname = zitadel.hostname
        else:
            zitadel_hostname = ""


        s3_endpoint = secrets.get('s3_endpoint', "")
        log.debug(f"writefreely s3_endpoint at the start is: {s3_endpoint}")

        if not restore_enabled:
            # create a local alias to check and make sure writefreely is functional
            create_minio_alias("writefreely", s3_endpoint, "writefreely", s3_access_key)

        if bitwarden and not restore_enabled:
            setup_bitwarden_items(argocd,
                                  writefreely_hostname,
                                  s3_endpoint,
                                  s3_access_id,
                                  s3_access_key,
                                  backup_vals['s3_user'],
                                  backup_vals['s3_password'],
                                  backup_vals['restic_repo_pass'],
                                  writefreely_admin_username,
                                  mail_host,
                                  mail_port,
                                  mail_user,
                                  mail_pass,
                                  oidc_creds,
                                  zitadel_hostname,
                                  bitwarden)

        # these are standard k8s secrets yaml
        elif not bitwarden and not restore_enabled:
            # admin creds k8s secret
            # k8s_obj.create_secret('writefreely-admin-credentials', 'writefreely',
            #               {"username": username,
            #                "email": email})

            # mysql creds k8s secret
            writefreely_mysql_password = create_password()
            argocd.k8s.create_secret(
                    'writefreely-mysql-credentials',
                    'writefreely',
                    {"password": writefreely_mysql_password,
                     'mysqlPassword': writefreely_mysql_password,
                     'username': "writefreely"})

    if not app_installed:
        if restore_enabled:
            restore_writefreely(argocd,
                               writefreely_hostname,
                               writefreely_namespace,
                               cfg['argo'],
                               secrets,
                               restore_dict,
                               backup_vals,
                               pvc_storage_class,
                               'writefreely-mysql',
                               bitwarden)

        if not init_enabled:
            argocd.install_app('writefreely', cfg['argo'])
        elif init_enabled and not restore_enabled:
            argocd.install_app('writefreely', cfg['argo'], True)
            # wait for all the writefreely apps to come up, give it extra time
            argocd.sync_app(app='writefreely-web-app', sleep_time=4)
            argocd.wait_for_app('writefreely-web-app')

            # create admin credentials
            password = create_user(writefreely_admin_username,
                                   writefreely_admin_email,
                                   cfg['argo']['namespace'])
            if bitwarden:
                sub_header("Creating secrets in Bitwarden")
                bitwarden.create_login(
                        name='writefreely-admin-credentials',
                        item_url=writefreely_hostname,
                        user=writefreely_admin_username,
                        password=password,
                        fields=[create_custom_field("email", writefreely_admin_email)]
                        )
    else:
        log.info("writefreely already installed 🎉")

        if bitwarden and init_enabled:
            refresh_bweso(argocd, writefreely_hostname, bitwarden)


def create_user(user: str, email: str, pod_namespace: str) -> str:
    """
    given a username, email, and namespace of the writefreely pod, we'll create a
    new writefreely user using a kubectl exec command and then we return
    their autogenerated password
    """
    sub_header(f"Creating a writefreely user for: {user}")
    # first, go get the exact name of the pod we need to exec a command on
    pod_cmd = (
            f"kubectl get pods -n {pod_namespace} "
            "-l app.kubernetes.io/instance=writefreely-web-app,app.kubernetes.io/component=web"
            " --no-headers "
            "-o custom-columns=NAME:.metadata.name"
            )
    pod = subproc([pod_cmd]).rstrip()
    log.info(f"writefreely web app pod is: {pod}")

    # generate a random password
    password = create_password()

    # then run the user creation command
    cmd = (f'kubectl exec -n {pod_namespace} {pod} -- /bin/sh -c "./writefreely '
           '--config-path ../config/config.yaml admin account create '
           f'--username {user} --email {email} --password \'{password}\'"')

    # then process the output from the command
    subproc([cmd], shell=True, universal_newlines=True)

    # then run the user promotion (to admin) command
    cmd = (f'kubectl exec -n {pod_namespace} {pod} -- /bin/sh -c '
           '"./writefreely --config-path ../config/config.yaml admin '
           f'account promote --username {user}"')

    # then process the output from the command
    subproc([cmd], shell=True, universal_newlines=True).split()[3]

    return password


def refresh_bweso(argocd: ArgoCD,
                  writefreely_hostname: str,
                  bitwarden: BwCLI) -> None:
    """
    if writefreely already installed, but bitwarden and init are enabled, still
    populate the bitwarden IDs in the appset secret plugin secret
    """
    log.debug("Making sure writefreely Bitwarden item IDs are in appset "
              "secret plugin secret")

    oidc_id = bitwarden.get_item(
            f"writefreely-oidc-credentials-{writefreely_hostname}"
            )[0]['id']

    admin_id = bitwarden.get_item(
            f"writefreely-admin-credentials-{writefreely_hostname}"
            )[0]['id']

    db_id = bitwarden.get_item(
            f"writefreely-mysql-credentials-{writefreely_hostname}"
            )[0]['id']

    smtp_id = bitwarden.get_item(
            f"writefreely-smtp-credentials-{writefreely_hostname}", False
            )[0]['id']

    s3_admin_id = bitwarden.get_item(
            f"writefreely-admin-s3-credentials-{writefreely_hostname}", False
            )[0]['id']

    s3_id = bitwarden.get_item(
            f"writefreely-user-s3-credentials-{writefreely_hostname}", False
            )[0]['id']

    s3_backups_id = bitwarden.get_item(
            f"writefreely-backups-s3-credentials-{writefreely_hostname}", False
            )[0]['id']

    # {'writefreely_admin_credentials_bitwarden_id': admin_id,
    argocd.update_appset_secret(
            {'writefreely_smtp_credentials_bitwarden_id': smtp_id,
             'writefreely_oidc_credentials_bitwarden_id': oidc_id,
             'writefreely_mysql_credentials_bitwarden_id': db_id,
             'writefreely_admin_credentials_bitwarden_id': admin_id,
             'writefreely_s3_admin_credentials_bitwarden_id': s3_admin_id,
             'writefreely_s3_writefreely_credentials_bitwarden_id': s3_id,
             'writefreely_s3_backups_credentials_bitwarden_id': s3_backups_id}
            )


def setup_bitwarden_items(argocd: ArgoCD,
                          writefreely_hostname: str,
                          s3_endpoint: str,
                          s3_access_id: str,
                          s3_access_key: str,
                          backups_s3_user: str,
                          backups_s3_password: str,
                          restic_repo_pass: str,
                          admin_user: str,
                          mail_host: str,
                          mail_port: str,
                          mail_user: str,
                          mail_pass: str,
                          oidc_creds: dict,
                          zitadel_hostname: str,
                          bitwarden: BwCLI) -> None:
    """
    setup secrets in bitwarden for writefreely.
    """

    # S3 credentials
    # endpoint that gets put into the secret should probably have http in it
    if "http" not in s3_endpoint:
        log.debug(f"writefreely s3_endpoint did not have http in it: {s3_endpoint}")
        s3_endpoint = "https://" + s3_endpoint
        log.debug(f"writefreely s3_endpoint - after prepending 'https://': {s3_endpoint}")

    writefreely_s3_endpoint_obj = create_custom_field("s3Endpoint", s3_endpoint)
    writefreely_s3_host_obj = create_custom_field("s3Hostname",
                                               s3_endpoint.replace("https://",
                                                                   ""))
    writefreely_s3_bucket_obj = create_custom_field("s3Bucket", "writefreely")
    s3_id = bitwarden.create_login(
            name='writefreely-user-s3-credentials',
            item_url=writefreely_hostname,
            user=s3_access_id,
            password=s3_access_key,
            fields=[
                writefreely_s3_endpoint_obj,
                writefreely_s3_host_obj,
                writefreely_s3_bucket_obj
                ]
            )

    admin_s3_key = create_password()
    s3_admin_id = bitwarden.create_login(
            name='writefreely-admin-s3-credentials',
            item_url=writefreely_hostname,
            user="writefreely-root",
            password=admin_s3_key
            )

    # credentials for remote backups of the s3 PVC
    restic_repo_pass_obj = create_custom_field("resticRepoPassword", restic_repo_pass)
    s3_backups_id = bitwarden.create_login(
            name='writefreely-backups-s3-credentials',
            item_url=writefreely_hostname,
            user=backups_s3_user,
            password=backups_s3_password,
            fields=[restic_repo_pass_obj]
            )

    # MySQL credentials
    writefreely_mysql_password = bitwarden.generate()
    mysql_pass_obj = create_custom_field("mysqlPassword",
                                         writefreely_mysql_password)
    db_id = bitwarden.create_login(
            name='writefreely-mysql-credentials',
            item_url=writefreely_hostname,
            user='writefreely',
            password=writefreely_mysql_password,
            fields=[mysql_pass_obj]
            )

    # SMTP credentials
    writefreely_smtp_host_obj = create_custom_field("smtpHostname", mail_host)
    writefreely_smtp_port_obj = create_custom_field("smtpPort", mail_port)
    smtp_id = bitwarden.create_login(
            name='writefreely-smtp-credentials',
            item_url=writefreely_hostname,
            user=mail_user,
            password=mail_pass,
            fields=[writefreely_smtp_host_obj, writefreely_smtp_port_obj]
            )

    # admin credentials for writefreely itself
    # admin_password = create_password()
    # email_obj = create_custom_field("email", writefreely_admin_email)
    # admin_id = bitwarden.create_login(
    #         name='writefreely-admin-credentials',
    #         item_url=writefreely_hostname,
    #         user=writefreely_admin_username,
    #         password=admin_password,
    #         fields=[email_obj]
    #         )

    # oidc credentials if they were given, else they're probably already there
    if oidc_creds:
        log.debug("Creating OIDC credentials for writefreely in Bitwarden...")
        issuer_obj = create_custom_field("issuer", f"https://{zitadel_hostname}")
        oidc_id = bitwarden.create_login(
                name='writefreely-oidc-credentials',
                item_url=writefreely_hostname,
                user=oidc_creds['client_id'],
                password=oidc_creds['client_secret'],
                fields=[issuer_obj]
                )
    else:
        oidc_id = bitwarden.get_item(
                f"writefreely-oidc-credentials-{writefreely_hostname}"
                )[0]['id']

    # update the writefreely values for the argocd appset
    # 'writefreely_admin_credentials_bitwarden_id': admin_id,
    argocd.update_appset_secret(
            {'writefreely_smtp_credentials_bitwarden_id': smtp_id,
             'writefreely_oidc_credentials_bitwarden_id': oidc_id,
             'writefreely_mysql_credentials_bitwarden_id': db_id,
             'writefreely_s3_admin_credentials_bitwarden_id': s3_admin_id,
             'writefreely_s3_writefreely_credentials_bitwarden_id': s3_id,
             'writefreely_s3_backups_credentials_bitwarden_id': s3_backups_id})

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


def restore_writefreely(argocd: ArgoCD,
                  writefreely_hostname: str,
                  writefreely_namespace: str,
                  argo_dict: dict,
                  secrets: dict,
                  restore_dict: dict,
                  backup_dict: dict,
                  global_pvc_storage_class: str,
                  bitwarden: BwCLI) -> None:
    """
    restore writefreely seaweedfs PVCs, writefreely files and/or config PVC(s)
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
        refresh_bweso(argocd, writefreely_hostname, bitwarden)

        # apply the external secrets so we can immediately use them for restores
        external_secrets_yaml = (
                f"https://raw.githubusercontent.com/small-hack/argocd-apps/{revision}/"
                f"{argo_path}external_secrets_argocd_appset.yaml"
                )
        argocd.k8s.apply_manifests(external_secrets_yaml, argocd.namespace)

    # these are the remote backups for seaweedfs
    s3_pvc_capacity = secrets['s3_pvc_capacity']

    # then we create all the seaweedfs pvcs we lost and restore them
    snapshot_ids = restore_dict['restic_snapshot_ids']
    s3_pvc_storage_class = secrets.get("s3_pvc_storage_class", global_pvc_storage_class)

    restore_seaweedfs(
            argocd,
            'writefreely',
            writefreely_namespace,
            revision,
            argo_path,
            s3_backup_endpoint,
            s3_backup_bucket,
            access_key_id,
            secret_access_key,
            restic_repo_password,
            s3_pvc_capacity,
            s3_pvc_storage_class,
            "ReadWriteOnce",
            snapshot_ids['seaweedfs_volume'],
            snapshot_ids['seaweedfs_filer'])

    podconfig_yaml = (
            f"https://raw.githubusercontent.com/small-hack/argocd-apps/{revision}/"
            f"{argo_path}pvc_argocd_appset.yaml"
            )
    argocd.k8s.apply_manifests(podconfig_yaml, argocd.namespace)

    # then we begin the restic restore of all the writefreely PVCs we lost
    for pvc in ['writefreely']:
        pvc_enabled = secrets.get('valkey_pvc_enabled', 'false')
        if pvc_enabled and pvc_enabled.lower() != 'false':
            # restores the writefreely pvc
            k8up_restore_pvc(
                    k8s_obj=argocd.k8s,
                    app='writefreely',
                    pvc=f'writefreely-{pvc.replace("_","-")}',
                    namespace='writefreely',
                    s3_endpoint=s3_backup_endpoint,
                    s3_bucket=s3_backup_bucket,
                    access_key_id=access_key_id,
                    secret_access_key=secret_access_key,
                    restic_repo_password=restic_repo_password,
                    snapshot_id=snapshot_ids[f'writefreely_{pvc}'],
                    pod_config="file-backups-podconfig"
                    )

    # todo: from here on out, this could be async to start on other tasks
    # install writefreely as usual, but wait on it this time
    argocd.install_app('writefreely', argo_dict, True)
