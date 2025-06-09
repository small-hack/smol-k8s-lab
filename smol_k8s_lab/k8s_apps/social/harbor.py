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
import logging as log


def configure_harbor(argocd: ArgoCD,
                     cfg: dict,
                     pvc_storage_class: str,
                     zitadel: Zitadel = None,
                     bitwarden: BwCLI = None) -> bool:
    """
    creates a harbor app and initializes it with secrets if you'd like :)

    required:
        argocd                 - ArgoCD() object for Argo CD operations
        cfg                    - dict, with at least argocd key and init key
        pvc_storage_class      - str, storage class of PVC

    optional:
        zitadel     - Zitadel() object with session token to create zitadel oidc app and roles
        bitwarden   - BwCLI() object with session token to create bitwarden items
    """
    # check immediately if the app is installed
    app_installed = argocd.check_if_app_exists('harbor')

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

    header(f"{header_start} [green]harbor[/], so you can self host your social media",
           '🐘')

    # get any secrets for this app
    secrets = cfg['argo']['secret_keys']
    if secrets:
        harbor_hostname = secrets['hostname']

    # we need namespace immediately
    harbor_namespace = cfg['argo']['namespace']

    if init_enabled:
        # declare custom values for harbor
        init_values = init.get('values', None)

        # backups are their own config.yaml section
        backup_vals = process_backup_vals(cfg.get('backups', {}), 'harbor', argocd)

    if init_enabled and not app_installed:
        argocd.k8s.create_namespace(harbor_namespace)

        if not restore_enabled:
            # configure the admin user credentials
            harbor_admin_username = init_values.get('admin_user', 'tootadmin')
            # harbor_admin_email = init_values.get('admin_email', '')

            # configure the smtp credentials
            mail_user = init_values.get('smtp_user', '')
            mail_host = init_values.get('smtp_host', '')
            mail_pass = extract_secret(init_values.get('smtp_password'))

            # configure s3 credentials
            s3_access_id = 'harbor'
            s3_access_key = create_password()

        # configure OIDC
        if zitadel and not restore_enabled:
            log.debug("Creating a harbor OIDC application in Zitadel...")
            redirect_uris = f"https://{harbor_hostname}/auth/callback"
            logout_uris = [f"https://{harbor_hostname}"]
            oidc_creds = zitadel.create_application(
                    "harbor",
                    redirect_uris,
                    logout_uris
                    )
            zitadel.create_role("harbor_users",
                                "harbor Users",
                                "harbor_users")
            zitadel.create_role("harbor_admins",
                                "harbor Admins",
                                "harbor_admins")
            zitadel.update_user_grant(['harbor_admins'])
            zitadel_hostname = zitadel.hostname
        else:
            zitadel_hostname = ""

        s3_endpoint = secrets.get('s3_endpoint', "")
        log.debug(f"harbor s3_endpoint at the start is: {s3_endpoint}")

        if not restore_enabled:
            # create a local alias to check and make sure harbor is functional
            create_minio_alias("harbor", s3_endpoint, "harbor", s3_access_key)

        if bitwarden and not restore_enabled:
            setup_bitwarden_items(argocd,
                                  harbor_hostname,
                                  s3_endpoint,
                                  s3_access_id,
                                  s3_access_key,
                                  backup_vals['s3_user'],
                                  backup_vals['s3_password'],
                                  backup_vals['restic_repo_pass'],
                                  harbor_admin_username,
                                  mail_host,
                                  mail_user,
                                  mail_pass,
                                  oidc_creds,
                                  zitadel_hostname,
                                  bitwarden)

        # these are standard k8s secrets yaml
        elif not bitwarden and not restore_enabled:
            # admin creds k8s secret
            argocd.k8s.create_secret('harbor-admin-credentials', 'harbor',
                          {"username": harbor_admin_username,
                           "password": create_password(),
                           "secretKey": create_password(False, 16)})

            # harbor registry credentials
            argocd.k8s.create_secret('harbor-registry-credentials', 'harbor',
                          {"username": harbor_admin_username,
                           "password": create_password()})

            # postgres creds k8s secret
            harbor_pgsql_password = create_password()
            argocd.k8s.create_secret(
                    'harbor-pgsql-credentials',
                    'harbor',
                    {"password": harbor_pgsql_password,
                     'postrgesPassword': harbor_pgsql_password})

            # valkey creds k8s secret
            harbor_valkey_password = create_password()
            argocd.k8s.create_secret('harbor-valkey-credentials', 'harbor',
                                     {"password": harbor_valkey_password})

    if not app_installed:
        if restore_enabled:
            restore_harbor(argocd,
                           harbor_hostname,
                           harbor_namespace,
                           cfg['argo'],
                           secrets,
                           restore_dict,
                           backup_vals,
                           pvc_storage_class,
                           'harbor-postgres',
                           bitwarden)

        argocd.install_app('harbor', cfg['argo'], True)
        # wait for all the harbor apps to come up, give it extra time
        argocd.sync_app(app='harbor-web-app', sleep_time=4)
        argocd.wait_for_app('harbor-web-app')
    else:
        log.info("harbor already installed 🎉")

        if bitwarden and init_enabled:
            refresh_bweso(argocd, harbor_hostname, bitwarden)


def create_user(user: str, email: str, pod_namespace: str) -> str:
    """
    given a username, email, and namespace of the harbor pod, we'll create a
    new harbor user via tootctl using a kubectl exec command and then we return
    their autogenerated password
    """
    sub_header(f"Creating a harbor user for: {user}")
    # first, go get the exact name of the pod we need to exec a command on
    pod_cmd = (
            f"kubectl get pods -n {pod_namespace} "
            "-l app.kubernetes.io/instance=harbor-web-app,app.kubernetes.io/component=web"
            " --no-headers "
            "-o custom-columns=NAME:.metadata.name"
            )
    pod = subproc([pod_cmd]).rstrip()
    log.info(f"harbor web app pod is: {pod}")

    # then run the user creation command
    cmd = (f'kubectl exec -n {pod_namespace} {pod} -- /bin/bash -c "bin/tootctl '
           f'accounts create {user} --email {email} --confirmed --role Owner"')

    # then process the output from the command and return it
    res = subproc([cmd],
                  shell=True,
                  universal_newlines=True).split()[3]
    print(f"password returned is: {res}")
    return res


def refresh_bweso(argocd: ArgoCD,
                  harbor_hostname: str,
                  bitwarden: BwCLI) -> None:
    """
    if harbor already installed, but bitwarden and init are enabled, still
    populate the bitwarden IDs in the appset secret plugin secret
    """
    log.debug("Making sure harbor Bitwarden item IDs are in appset "
              "secret plugin secret")

    oidc_id = bitwarden.get_item(
            f"harbor-oidc-credentials-{harbor_hostname}"
            )[0]['id']

    admin_id = bitwarden.get_item(
            f"harbor-admin-credentials-{harbor_hostname}"
            )[0]['id']

    registry_id = bitwarden.get_item(
            f"harbor-registry-credentials-{harbor_hostname}"
            )[0]['id']

    db_id = bitwarden.get_item(
            f"harbor-pgsql-credentials-{harbor_hostname}"
            )[0]['id']

    valkey_id = bitwarden.get_item(
            f"harbor-valkey-credentials-{harbor_hostname}", False
            )[0]['id']

    smtp_id = bitwarden.get_item(
            f"harbor-smtp-credentials-{harbor_hostname}", False
            )[0]['id']

    s3_admin_id = bitwarden.get_item(
            f"harbor-admin-s3-credentials-{harbor_hostname}", False
            )[0]['id']

    s3_db_id = bitwarden.get_item(
            f"harbor-postgres-s3-credentials-{harbor_hostname}", False
            )[0]['id']

    s3_id = bitwarden.get_item(
            f"harbor-user-s3-credentials-{harbor_hostname}", False
            )[0]['id']

    s3_backups_id = bitwarden.get_item(
            f"harbor-backups-s3-credentials-{harbor_hostname}", False
            )[0]['id']

    argocd.update_appset_secret(
            {'harbor_smtp_credentials_bitwarden_id': smtp_id,
             'harbor_oidc_credentials_bitwarden_id': oidc_id,
             'harbor_postgres_credentials_bitwarden_id': db_id,
             'harbor_valkey_bitwarden_id': valkey_id,
             'harbor_registry_credentials_bitwarden_id': registry_id,
             'harbor_admin_credentials_bitwarden_id': admin_id,
             'harbor_s3_admin_credentials_bitwarden_id': s3_admin_id,
             'harbor_s3_postgres_credentials_bitwarden_id': s3_db_id,
             'harbor_s3_harbor_credentials_bitwarden_id': s3_id,
             'harbor_s3_backups_credentials_bitwarden_id': s3_backups_id}
            )


def setup_bitwarden_items(argocd: ArgoCD,
                          harbor_hostname: str,
                          s3_endpoint: str,
                          s3_access_id: str,
                          s3_access_key: str,
                          backups_s3_user: str,
                          backups_s3_password: str,
                          restic_repo_pass: str,
                          admin_user: str,
                          mail_host: str,
                          mail_user: str,
                          mail_pass: str,
                          oidc_creds: dict,
                          zitadel_hostname: str,
                          bitwarden: BwCLI) -> None:
    # S3 credentials
    # endpoint that gets put into the secret should probably have http in it
    if "http" not in s3_endpoint:
        log.debug(f"harbor s3_endpoint did not have http in it: {s3_endpoint}")
        s3_endpoint = "https://" + s3_endpoint
        log.debug(f"harbor s3_endpoint - after prepending 'https://': {s3_endpoint}")

    harbor_s3_endpoint_obj = create_custom_field("s3Endpoint", s3_endpoint)
    harbor_s3_host_obj = create_custom_field("s3Hostname",
                                               s3_endpoint.replace("https://",
                                                                   ""))
    harbor_s3_bucket_obj = create_custom_field("s3Bucket", "harbor")
    s3_id = bitwarden.create_login(
            name='harbor-user-s3-credentials',
            item_url=harbor_hostname,
            user=s3_access_id,
            password=s3_access_key,
            fields=[
                harbor_s3_endpoint_obj,
                harbor_s3_host_obj,
                harbor_s3_bucket_obj
                ]
            )

    # postgresql S3 creds
    pgsql_s3_key = create_password()
    s3_db_id = bitwarden.create_login(
            name='harbor-postgres-s3-credentials',
            item_url=harbor_hostname,
            user="harbor-postgres",
            password=pgsql_s3_key
            )

    # harbor admin S3 creds
    admin_s3_key = create_password()
    s3_admin_id = bitwarden.create_login(
            name='harbor-admin-s3-credentials',
            item_url=harbor_hostname,
            user="harbor-root",
            password=admin_s3_key
            )

    # credentials for remote backups of the s3 PVC
    restic_repo_pass_obj = create_custom_field("resticRepoPassword", restic_repo_pass)
    s3_backups_id = bitwarden.create_login(
            name='harbor-backups-s3-credentials',
            item_url=harbor_hostname,
            user=backups_s3_user,
            password=backups_s3_password,
            fields=[restic_repo_pass_obj]
            )

    # PostgreSQL credentials
    harbor_pgsql_password = bitwarden.generate()
    postrges_pass_obj = create_custom_field("postgresPassword",
                                            harbor_pgsql_password)
    db_id = bitwarden.create_login(
            name='harbor-pgsql-credentials',
            item_url=harbor_hostname,
            user='harbor',
            password=harbor_pgsql_password,
            fields=[postrges_pass_obj]
            )

    # valkey credentials
    harbor_valkey_password = bitwarden.generate()
    valkey_id = bitwarden.create_login(
            name='harbor-valkey-credentials',
            item_url=harbor_hostname,
            user='harbor',
            password=harbor_valkey_password
            )

    # SMTP credentials
    harbor_smtp_host_obj = create_custom_field("smtpHostname", mail_host)
    smtp_id = bitwarden.create_login(
            name='harbor-smtp-credentials',
            item_url=harbor_hostname,
            user=mail_user,
            password=mail_pass,
            fields=[harbor_smtp_host_obj]
            )

    # admin credentials for harbor itself
    admin_password = create_password()
    # for harbor encryption key, must be 16 characters
    secret_key_obj = create_custom_field("secretKey", create_password(False, 16))
    admin_id = bitwarden.create_login(
            name='harbor-admin-credentials',
            item_url=harbor_hostname,
            user=admin_user,
            password=admin_password,
            fields=[secret_key_obj]
            )

    # initial registry credentials for harbor
    registry_username = create_password(False, 12)
    registry_password = create_password()
    registry_id = bitwarden.create_login(
            name='harbor-registry-credentials',
            item_url=harbor_hostname,
            user=registry_username,
            password=registry_password
            )

    # oidc credentials if they were given, else they're probably already there
    if oidc_creds:
        log.debug("Creating OIDC credentials for harbor in Bitwarden...")
        issuer_obj = create_custom_field("issuer", f"https://{zitadel_hostname}")
        oidc_id = bitwarden.create_login(
                name='harbor-oidc-credentials',
                item_url=harbor_hostname,
                user=oidc_creds['client_id'],
                password=oidc_creds['client_secret'],
                fields=[issuer_obj]
                )
    else:
        oidc_id = bitwarden.get_item(
                f"harbor-oidc-credentials-{harbor_hostname}"
                )[0]['id']

    # update the harbor values for the argocd appset
    argocd.update_appset_secret(
            {'harbor_smtp_credentials_bitwarden_id': smtp_id,
             'harbor_oidc_credentials_bitwarden_id': oidc_id,
             'harbor_postgres_credentials_bitwarden_id': db_id,
             'harbor_valkey_bitwarden_id': valkey_id,
             'harbor_registry_credentials_bitwarden_id': registry_id,
             'harbor_admin_credentials_bitwarden_id': admin_id,
             'harbor_s3_admin_credentials_bitwarden_id': s3_admin_id,
             'harbor_s3_postgres_credentials_bitwarden_id': s3_db_id,
             'harbor_s3_harbor_credentials_bitwarden_id': s3_id,
             'harbor_s3_backups_credentials_bitwarden_id': s3_backups_id})

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


def restore_harbor(argocd: ArgoCD,
                     harbor_hostname: str,
                     harbor_namespace: str,
                     argo_dict: dict,
                     secrets: dict,
                     restore_dict: dict,
                     backup_dict: dict,
                     global_pvc_storage_class: str,
                     pgsql_cluster_name: str,
                     bitwarden: BwCLI) -> None:
    """
    restore harbor seaweedfs PVCs, harbor files and/or config PVC(s),
    and CNPG postgresql cluster
    """
    # this is the info for the REMOTE backups
    s3_backup_endpoint = backup_dict['endpoint']
    s3_backup_bucket = backup_dict['bucket']
    access_key_id = backup_dict["s3_user"]
    secret_access_key = backup_dict["s3_password"]
    restic_repo_password = backup_dict['restic_repo_pass']
    cnpg_backup_schedule = backup_dict['postgres_schedule']

    # get argo git repo info
    revision = argo_dict['revision']
    argo_path = argo_dict['path']

    # first we grab existing bitwarden items if they exist
    if bitwarden:
        refresh_bweso(argocd, harbor_hostname, bitwarden)

        # apply the external secrets so we can immediately use them for restores
        external_secrets_yaml = (
                f"https://raw.githubusercontent.com/small-hack/argocd-apps/{revision}/"
                f"{argo_path}external_secrets_argocd_appset.yaml"
                )
        argocd.k8s.apply_manifests(external_secrets_yaml, argocd.namespace)

        # postgresql s3 ID
        s3_db_creds = bitwarden.get_item(
                f"harbor-postgres-s3-credentials-{harbor_hostname}", False
                )[0]['login']

        pg_access_key_id = s3_db_creds["username"]
        pg_secret_access_key = s3_db_creds["password"]

    # these are the remote backups for seaweedfs
    s3_pvc_capacity = secrets['s3_pvc_capacity']

    # then we create all the seaweedfs pvcs we lost and restore them
    snapshot_ids = restore_dict['restic_snapshot_ids']
    s3_pvc_storage_class = secrets.get("s3_pvc_storage_class", global_pvc_storage_class)

    restore_seaweedfs(
            argocd,
            'harbor',
            harbor_namespace,
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

    # then we finally can restore the postgres database :D
    if restore_dict.get("cnpg_restore", False):
        psql_version = restore_dict.get("postgresql_version", 16)
        s3_endpoint = secrets.get('s3_endpoint', "")
        restore_cnpg_cluster(argocd.k8s,
                             'harbor',
                             harbor_namespace,
                             pgsql_cluster_name,
                             psql_version,
                             s3_endpoint,
                             pg_access_key_id,
                             pg_secret_access_key,
                             pgsql_cluster_name,
                             cnpg_backup_schedule)

    podconfig_yaml = (
            f"https://raw.githubusercontent.com/small-hack/argocd-apps/{revision}/"
            f"{argo_path}pvc_argocd_appset.yaml"
            )
    argocd.k8s.apply_manifests(podconfig_yaml, argocd.namespace)

    # then we begin the restic restore of all the harbor PVCs we lost
    for pvc in ['valkey_primary', 'valkey_replica', 'trivy', 'jobs', 'registry']:
        pvc_enabled = secrets.get('valkey_pvc_enabled', 'false')
        if pvc_enabled and pvc_enabled.lower() != 'false':
            # restores the harbor pvc
            k8up_restore_pvc(
                    k8s_obj=argocd.k8s,
                    app='harbor',
                    pvc=f'{pvc.replace("_","-")}',
                    namespace='harbor',
                    s3_endpoint=s3_backup_endpoint,
                    s3_bucket=s3_backup_bucket,
                    access_key_id=access_key_id,
                    secret_access_key=secret_access_key,
                    restic_repo_password=restic_repo_password,
                    snapshot_id=snapshot_ids[f'harbor_{pvc}'],
                    pod_config="file-backups-podconfig"
                    )

    # todo: from here on out, this could be async to start on other tasks
    # install harbor as usual, but wait on it this time
    argocd.install_app('harbor', argo_dict, True)
