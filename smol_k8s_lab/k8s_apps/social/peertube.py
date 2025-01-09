# internal libraries
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_apps.operators.minio import create_minio_alias
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


def configure_peertube(argocd: ArgoCD,
                       cfg: dict,
                       pvc_storage_class: str,
                       bitwarden: BwCLI = None) -> bool:
    """
    creates a peertube app and initializes it with a secret if you'd like :)

    required:
        argocd                 - ArgoCD() object for Argo CD operations
        cfg                    - dict, with at least argocd key and init key
        pvc_storage_class      - str, storage class of PVC

    optional:
        bitwarden   - BwCLI() object with session token to create bitwarden items
    """
    # check immediately if the app is installed
    app_installed = argocd.check_if_app_exists('peertube')

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

    header(f"{header_start} [green]PeerTube[/], so you can self host your videos (like YouTube)",
           '🐙')

    # get any secrets for this app
    secrets = cfg['argo']['secret_keys']
    if secrets:
        peertube_hostname = secrets['hostname']

    # we need namespace immediately
    peertube_namespace = cfg['argo']['namespace']

    if init_enabled:
        # declare custom values for peertube
        init_values = init.get('values', None)

        # admin user's email
        peertube_admin_email = init_values.get('admin_email', '')

        # backups are their own config.yaml section
        backup_vals = process_backup_vals(cfg.get('backups', {}), 'peertube', argocd)

    if init_enabled and not app_installed:
        argocd.k8s.create_namespace(peertube_namespace)

        if not restore_enabled:
            # configure the admin user credentials
            # peertube_admin_username = init_values.get('admin_user', 'peeradmin')
            peertube_admin_email = init_values.get('admin_email', '')

            # configure the smtp credentials
            mail_user = init_values.get('smtp_user', '')
            mail_host = init_values.get('smtp_host', '')
            mail_port = init_values.get('smtp_port', '')
            mail_pass = extract_secret(init_values.get('smtp_password'))

            # configure s3 admin credentials
            s3_access_id = 'peertube'
            s3_access_key = create_password()

            # configure s3 video credentials
            video_s3_access_id = 'peertube-video'
            video_s3_access_key = create_password()

            # configure s3 video credentials
            user_s3_access_id = 'peertube-user'
            user_s3_access_key = create_password()

        # main s3 endpoint for postgres
        s3_endpoint = secrets.get('s3_endpoint', "")

        # s3 endpoints for video and user buckets
        streaming_bucket = secrets.get('s3_streaming_bucket', "")
        orig_video_bucket = secrets.get('s3_orig_video_bucket', "")
        web_video_bucket = secrets.get('s3_web_video_bucket', "")
        user_exports_bucket = secrets.get('s3_user_exports_bucket', "")

        log.debug(f"peertube s3_endpoint at the start is: {s3_endpoint}")

        if not restore_enabled:
            # create a local alias to check and make sure peertube is functional
            create_minio_alias(minio_alias=s3_access_id,
                               minio_hostname=s3_endpoint,
                               access_key=s3_access_id,
                               secret_key=s3_access_key)

        if bitwarden and not restore_enabled:
            setup_bitwarden_items(argocd,
                                  peertube_hostname,
                                  s3_endpoint,
                                  s3_access_id,
                                  s3_access_key,
                                  user_exports_bucket,
                                  orig_video_bucket,
                                  web_video_bucket,
                                  streaming_bucket,
                                  user_s3_access_id,
                                  user_s3_access_key,
                                  video_s3_access_id,
                                  video_s3_access_key,
                                  backup_vals['s3_user'],
                                  backup_vals['s3_password'],
                                  backup_vals['restic_repo_pass'],
                                  peertube_admin_email,
                                  mail_host,
                                  mail_user,
                                  mail_pass,
                                  mail_port,
                                  bitwarden)

        # these are standard k8s secrets yaml
        elif not bitwarden and not restore_enabled:
            # admin creds k8s secret
            peertube_admin_password = create_password()
            argocd.k8s.create_secret(
                    'peertube-admin-credentials',
                    'peertube',
                    {
                       "password": peertube_admin_password,
                       "email": peertube_admin_email
                    }
            )

            # postgres creds k8s secret
            peertube_pgsql_password = create_password()
            argocd.k8s.create_secret(
                    'peertube-pgsql-credentials',
                    'peertube',
                    {"password": peertube_pgsql_password,
                     'postrgesPassword': peertube_pgsql_password})

            # valkey creds k8s secret
            peertube_valkey_password = create_password()
            argocd.k8s.create_secret('peertube-valkey-credentials', 'peertube',
                                     {"password": peertube_valkey_password})

            # peertube secret
            argocd.k8s.create_secret('peertube-server-secret', 'peertube',
                                     {"secret": create_password()})

    if not app_installed:
        if restore_enabled:
            restore_peertube(argocd,
                             peertube_hostname,
                             peertube_namespace,
                             cfg['argo'],
                             secrets,
                             restore_dict,
                             backup_vals,
                             pvc_storage_class,
                             'peertube-postgres',
                             bitwarden)

        if not init_enabled:
            argocd.install_app('peertube', cfg['argo'])
        elif init_enabled and not restore_enabled:
            argocd.install_app('peertube', cfg['argo'], True)
            # wait for all the peertube apps to come up, give it extra time
            argocd.sync_app(app='peertube-web-app', sleep_time=4)
            argocd.wait_for_app('peertube-web-app')

            # create admin credentials, maybe not needed
            # password = create_user(peertube_admin_username,
            #                        peertube_admin_email,
            #                        cfg['argo']['namespace'])
    else:
        log.info("peertube already installed 🎉")

        if bitwarden and init_enabled:
            refresh_bweso(argocd, peertube_hostname, bitwarden)


def create_user(user: str, email: str, pod_namespace: str) -> str:
    """
    given a username, email, and namespace of the peertube pod, we'll create a
    new peertube user via tootctl using a kubectl exec command and then we return
    their autogenerated password
    """
    sub_header(f"Creating a peertube user for: {user}")
    # first, go get the exact name of the pod we need to exec a command on
    pod_cmd = (
            f"kubectl get pods -n {pod_namespace} "
            "-l app.kubernetes.io/instance=peertube-web-app,app.kubernetes.io/component=web"
            " --no-headers "
            "-o custom-columns=NAME:.metadata.name"
            )
    pod = subproc([pod_cmd]).rstrip()
    log.info(f"peertube web app pod is: {pod}")

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
                  peertube_hostname: str,
                  bitwarden: BwCLI) -> None:
    """
    if peertube already installed, but bitwarden and init are enabled, still
    populate the bitwarden IDs in the appset secret plugin secret
    """
    log.debug("Making sure peertube Bitwarden item IDs are in appset "
              "secret plugin secret")

    db_id = bitwarden.get_item(
            f"peertube-pgsql-credentials-{peertube_hostname}"
            )[0]['id']

    valkey_id = bitwarden.get_item(
            f"peertube-valkey-credentials-{peertube_hostname}", False
            )[0]['id']

    smtp_id = bitwarden.get_item(
            f"peertube-smtp-credentials-{peertube_hostname}", False
            )[0]['id']

    s3_admin_id = bitwarden.get_item(
            f"peertube-admin-s3-credentials-{peertube_hostname}", False
            )[0]['id']

    s3_db_id = bitwarden.get_item(
            f"peertube-postgres-s3-credentials-{peertube_hostname}", False
            )[0]['id']

    s3_id = bitwarden.get_item(
            f"peertube-user-s3-credentials-{peertube_hostname}", False
            )[0]['id']

    s3_backups_id = bitwarden.get_item(
            f"peertube-backups-s3-credentials-{peertube_hostname}", False
            )[0]['id']

    secrets_id = bitwarden.get_item(
            f"peertube-server-secret-{peertube_hostname}", False
            )[0]['id']

    admin_id = bitwarden.get_item(
            f"peertube-admin-credentials-{peertube_hostname}", False
            )[0]['id']

    argocd.update_appset_secret(
            {'peertube_smtp_credentials_bitwarden_id': smtp_id,
             'peertube_admin_credentials_bitwarden_id': admin_id,
             'peertube_postgres_credentials_bitwarden_id': db_id,
             'peertube_valkey_bitwarden_id': valkey_id,
             'peertube_s3_admin_credentials_bitwarden_id': s3_admin_id,
             'peertube_s3_postgres_credentials_bitwarden_id': s3_db_id,
             'peertube_s3_peertube_credentials_bitwarden_id': s3_id,
             'peertube_s3_backups_credentials_bitwarden_id': s3_backups_id,
             'peertube_secret_bitwarden_id': secrets_id}
            )


def setup_bitwarden_items(argocd: ArgoCD,
                          peertube_hostname: str,
                          s3_endpoint: str,
                          s3_access_id: str,
                          s3_access_key: str,
                          user_exports_bucket: str,
                          orig_video_bucket: str,
                          web_video_bucket: str,
                          streaming_bucket: str,
                          user_s3_access_id: str,
                          user_s3_access_key: str,
                          video_s3_access_id: str,
                          video_s3_access_key: str,
                          backups_s3_user: str,
                          backups_s3_password: str,
                          restic_repo_pass: str,
                          admin_email: str,
                          mail_host: str,
                          mail_user: str,
                          mail_pass: str,
                          mail_port: str,
                          bitwarden: BwCLI) -> None:
    """
    a function to setup all peertube related items in Bitwarden
    """
    # S3 credentials
    # endpoint that gets put into the secret should probably have http in it
    if "http" not in s3_endpoint:
        log.debug(f"peertube s3_endpoint did not have http in it: {s3_endpoint}")
        s3_endpoint = "https://" + s3_endpoint
        log.debug(f"peertube s3_endpoint - after prepending 'https://': {s3_endpoint}")

    peertube_s3_endpoint_obj = create_custom_field("s3Endpoint", s3_endpoint)
    peertube_s3_host_obj = create_custom_field("s3Hostname",
                                               s3_endpoint.replace("https://",
                                                                   ""))
    peertube_s3_bucket_obj = create_custom_field("s3Bucket", "peertube")
    user_s3_bucket_obj = create_custom_field("userExportBucket", user_exports_bucket)
    web_video_s3_bucket_obj = create_custom_field("webVideoBucket", web_video_bucket)
    orig_video_s3_bucket_obj = create_custom_field("origVideoBucket", orig_video_bucket)
    streaming_s3_bucket_obj = create_custom_field("streamingBucket", streaming_bucket)
    user_s3_access_id_obj = create_custom_field("s3PeertubeUserAccessID", user_s3_access_id)
    user_s3_access_key_obj = create_custom_field("s3PeertubeUserAccessKey", user_s3_access_key)
    video_s3_access_id_obj = create_custom_field("s3PeertubeVideoAccessID", video_s3_access_id)
    video_s3_access_key_obj = create_custom_field("s3PeertubeVideoAccessKey", video_s3_access_key)
    s3_id = bitwarden.create_login(
            name='peertube-user-s3-credentials',
            item_url=peertube_hostname,
            user=s3_access_id,
            password=s3_access_key,
            fields=[
                peertube_s3_endpoint_obj,
                peertube_s3_host_obj,
                peertube_s3_bucket_obj,
                user_s3_access_id_obj,
                user_s3_access_key_obj,
                video_s3_access_id_obj,
                video_s3_access_key_obj,
                user_s3_bucket_obj,
                web_video_s3_bucket_obj,
                orig_video_s3_bucket_obj,
                streaming_s3_bucket_obj
                ]
            )

    pgsql_s3_key = create_password()
    s3_db_id = bitwarden.create_login(
            name='peertube-postgres-s3-credentials',
            item_url=peertube_hostname,
            user="peertube-postgres",
            password=pgsql_s3_key
            )

    admin_s3_key = create_password()
    s3_admin_id = bitwarden.create_login(
            name='peertube-admin-s3-credentials',
            item_url=peertube_hostname,
            user="peertube-root",
            password=admin_s3_key
            )

    # credentials for remote backups of the s3 PVC
    restic_repo_pass_obj = create_custom_field("resticRepoPassword", restic_repo_pass)
    s3_backups_id = bitwarden.create_login(
            name='peertube-backups-s3-credentials',
            item_url=peertube_hostname,
            user=backups_s3_user,
            password=backups_s3_password,
            fields=[restic_repo_pass_obj]
            )

    # PostgreSQL credentials
    peertube_pgsql_password = bitwarden.generate()
    postrges_pass_obj = create_custom_field("postgresPassword",
                                            peertube_pgsql_password)
    db_id = bitwarden.create_login(
            name='peertube-pgsql-credentials',
            item_url=peertube_hostname,
            user='peertube',
            password=peertube_pgsql_password,
            fields=[postrges_pass_obj]
            )

    # valkey credentials
    peertube_valkey_password = bitwarden.generate()
    valkey_id = bitwarden.create_login(
            name='peertube-valkey-credentials',
            item_url=peertube_hostname,
            user='peertube',
            password=peertube_valkey_password
            )

    # SMTP credentials
    peertube_smtp_host_obj = create_custom_field("smtpHostname", mail_host)
    peertube_smtp_port_obj = create_custom_field("smtpPort", mail_port)
    smtp_id = bitwarden.create_login(
            name='peertube-smtp-credentials',
            item_url=peertube_hostname,
            user=mail_user,
            password=mail_pass,
            fields=[peertube_smtp_host_obj, peertube_smtp_port_obj]
            )

    # peertube random secret
    peertube_secret = create_password()
    secrets_id = bitwarden.create_login(
            name='peertube-server-secret',
            item_url=peertube_hostname,
            user="peertube",
            password=peertube_secret
            )

    # peertube admin credentials
    password = create_password()
    admin_id = bitwarden.create_login(
            name='peertube-admin-credentials',
            item_url=peertube_hostname,
            user=admin_email,
            password=password
            )

    # update the peertube values for the argocd appset
    argocd.update_appset_secret(
            {'peertube_smtp_credentials_bitwarden_id': smtp_id,
             'peertube_admin_credentials_bitwarden_id': admin_id,
             'peertube_postgres_credentials_bitwarden_id': db_id,
             'peertube_valkey_bitwarden_id': valkey_id,
             'peertube_s3_admin_credentials_bitwarden_id': s3_admin_id,
             'peertube_s3_postgres_credentials_bitwarden_id': s3_db_id,
             'peertube_s3_peertube_credentials_bitwarden_id': s3_id,
             'peertube_s3_backups_credentials_bitwarden_id': s3_backups_id,
             'peertube_secret_bitwarden_id': secrets_id})

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


def restore_peertube(argocd: ArgoCD,
                     peertube_hostname: str,
                     peertube_namespace: str,
                     argo_dict: dict,
                     secrets: dict,
                     restore_dict: dict,
                     backup_dict: dict,
                     global_pvc_storage_class: str,
                     pgsql_cluster_name: str,
                     bitwarden: BwCLI) -> None:
    """
    restore peertube seaweedfs PVCs, peertube files and/or config PVC(s),
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
        refresh_bweso(argocd, peertube_hostname, bitwarden)

        # apply the external secrets so we can immediately use them for restores
        external_secrets_yaml = (
                f"https://raw.githubusercontent.com/small-hack/argocd-apps/{revision}/"
                f"{argo_path}external_secrets_argocd_appset.yaml"
                )
        argocd.k8s.apply_manifests(external_secrets_yaml, argocd.namespace)

        # postgresql s3 ID
        s3_db_creds = bitwarden.get_item(
                f"peertube-postgres-s3-credentials-{peertube_hostname}", False
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
            'peertube',
            peertube_namespace,
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
                             'peertube',
                             peertube_namespace,
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

    # then we begin the restic restore of all the peertube PVCs we lost
    # for pvc in ['data', 'valkey_primary', 'valkey_replica']:
    for pvc in ['data']:
        if 'valkey' in pvc:
            pvc_enabled = secrets.get('valkey_pvc_enabled', 'false')
        else:
            pvc_enabled = secrets.get('data_pvc_enabled', 'false')
        if pvc_enabled and pvc_enabled.lower() != 'false':
            # restores the peertube pvc
            k8up_restore_pvc(
                    k8s_obj=argocd.k8s,
                    app='peertube',
                    pvc=f'peertube-{pvc.replace("_","-")}',
                    namespace='peertube',
                    s3_endpoint=s3_backup_endpoint,
                    s3_bucket=s3_backup_bucket,
                    access_key_id=access_key_id,
                    secret_access_key=secret_access_key,
                    restic_repo_password=restic_repo_password,
                    snapshot_id=snapshot_ids[f'peertube_{pvc}'],
                    pod_config="file-backups-podconfig"
                    )

    # todo: from here on out, this could be async to start on other tasks
    # install peertube as usual, but wait on it this time
    argocd.install_app('peertube', argo_dict, True)
