# internal libraries
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_apps.operators.minio import create_minio_alias
from smol_k8s_lab.k8s_apps.social.mastodon_secrets import generate_mastodon_secrets
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


def configure_mastodon(argocd: ArgoCD,
                       cfg: dict,
                       pvc_storage_class: str,
                       libretranslate_api_key: str = "",
                       bitwarden: BwCLI = None) -> bool:
    """
    creates a mastodon app and initializes it with secrets if you'd like :)

    required:
        argocd                 - ArgoCD() object for Argo CD operations
        cfg                    - dict, with at least argocd key and init key
        pvc_storage_class      - str, storage class of PVC
        libretranslate_api_key - str, api key to enable automatic translations

    optional:
        bitwarden   - BwCLI() object with session token to create bitwarden items
    """
    # check immediately if the app is installed
    app_installed = argocd.check_if_app_exists('mastodon')

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

    header(f"{header_start} [green]Mastodon[/], so you can self host your social media",
           '🐘')

    # get any secrets for this app
    secrets = cfg['argo']['secret_keys']
    if secrets:
        mastodon_hostname = secrets['hostname']
        mastodon_libretranslate_hostname = secrets['libretranslate_hostname']

    # we need namespace immediately
    mastodon_namespace = cfg['argo']['namespace']

    if init_enabled:
        # declare custom values for mastodon
        init_values = init.get('values', None)

        # backups are their own config.yaml section
        backup_vals = process_backup_vals(cfg.get('backups', {}), 'mastodon', argocd)

        # get the api key for LibreTranslate, so we can translate posts
        libre_api_key = extract_secret(init_values.get('libretranslate_api_key'))
        if not libre_api_key:
            libre_api_key = libretranslate_api_key

    if init_enabled and not app_installed:
        argocd.k8s.create_namespace(mastodon_namespace)

        if not restore_enabled:
            # configure the admin user credentials
            mastodon_admin_username = init_values.get('admin_user', 'tootadmin')
            mastodon_admin_email = init_values.get('admin_email', '')

            # configure the smtp credentials
            mail_user = init_values.get('smtp_user', '')
            mail_host = init_values.get('smtp_host', '')
            mail_pass = extract_secret(init_values.get('smtp_password'))

            # main mastodon rake secrets
            rake_secrets = generate_mastodon_secrets()

            # configure s3 credentials
            s3_access_id = 'mastodon'
            s3_access_key = create_password()

        s3_endpoint = secrets.get('s3_endpoint', "")
        log.debug(f"Mastodon s3_endpoint at the start is: {s3_endpoint}")

        if not restore_enabled:
            # create a local alias to check and make sure mastodon is functional
            create_minio_alias("mastodon", s3_endpoint, "mastodon", s3_access_key)

        if bitwarden and not restore_enabled:
            setup_bitwarden_items(argocd,
                                  mastodon_hostname,
                                  s3_endpoint,
                                  s3_access_id,
                                  s3_access_key,
                                  backup_vals['s3_user'],
                                  backup_vals['s3_password'],
                                  backup_vals['restic_repo_pass'],
                                  mastodon_admin_username,
                                  mail_host,
                                  mail_user,
                                  mail_pass,
                                  rake_secrets,
                                  mastodon_libretranslate_hostname,
                                  libre_api_key,
                                  bitwarden)

        # these are standard k8s secrets yaml
        elif not bitwarden and not restore_enabled:
            # admin creds k8s secret
            # k8s_obj.create_secret('mastodon-admin-credentials', 'mastodon',
            #               {"username": username,
            #                "email": email})

            # postgres creds k8s secret
            mastodon_pgsql_password = create_password()
            argocd.k8s.create_secret(
                    'mastodon-pgsql-credentials',
                    'mastodon',
                    {"password": mastodon_pgsql_password,
                     'postrgesPassword': mastodon_pgsql_password})

            # valkey creds k8s secret
            mastodon_valkey_password = create_password()
            argocd.k8s.create_secret('mastodon-valkey-credentials', 'mastodon',
                                     {"password": mastodon_valkey_password})

            # mastodon rake secrets
            argocd.k8s.create_secret('mastodon-server-secrets', 'mastodon',
                                     rake_secrets)

    if not app_installed:
        if restore_enabled:
            restore_mastodon(argocd,
                             mastodon_hostname,
                             mastodon_namespace,
                             cfg['argo'],
                             secrets,
                             restore_dict,
                             backup_vals,
                             pvc_storage_class,
                             'mastodon-postgres',
                             mastodon_libretranslate_hostname,
                             libre_api_key,
                             bitwarden)

        if not init_enabled:
            argocd.install_app('mastodon', cfg['argo'])
        elif init_enabled and not restore_enabled:
            argocd.install_app('mastodon', cfg['argo'], True)
            # wait for all the mastodon apps to come up, give it extra time
            argocd.sync_app(app='mastodon-web-app', sleep_time=4)
            argocd.wait_for_app('mastodon-web-app')

            # create admin credentials
            password = create_user(mastodon_admin_username,
                                   mastodon_admin_email,
                                   cfg['argo']['namespace'])
            if bitwarden:
                sub_header("Creating secrets in Bitwarden")
                bitwarden.create_login(
                        name='mastodon-admin-credentials',
                        item_url=mastodon_hostname,
                        user=mastodon_admin_username,
                        password=password,
                        fields=[create_custom_field("email", mastodon_admin_email)]
                        )
    else:
        log.info("mastodon already installed 🎉")

        if bitwarden and init_enabled:
            refresh_bweso(argocd, mastodon_hostname, mastodon_libretranslate_hostname, libre_api_key, bitwarden)


def create_user(user: str, email: str, pod_namespace: str) -> str:
    """
    given a username, email, and namespace of the mastodon pod, we'll create a
    new mastodon user via tootctl using a kubectl exec command and then we return
    their autogenerated password
    """
    sub_header(f"Creating a mastodon user for: {user}")
    # first, go get the exact name of the pod we need to exec a command on
    pod_cmd = (
            f"kubectl get pods -n {pod_namespace} "
            "-l app.kubernetes.io/instance=mastodon-web-app,app.kubernetes.io/component=web"
            " --no-headers "
            "-o custom-columns=NAME:.metadata.name"
            )
    pod = subproc([pod_cmd]).rstrip()
    log.info(f"Mastodon web app pod is: {pod}")

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
                  mastodon_hostname: str,
                  mastodon_libretranslate_hostname: str,
                  libre_api_key: str,
                  bitwarden: BwCLI) -> None:
    """
    if mastodon already installed, but bitwarden and init are enabled, still
    populate the bitwarden IDs in the appset secret plugin secret
    """
    log.debug("Making sure mastodon Bitwarden item IDs are in appset "
              "secret plugin secret")

    # admin_id = bitwarden.get_item(
    #         f"mastodon-admin-credentials-{mastodon_hostname}"
    #         )[0]['id']

    db_id = bitwarden.get_item(
            f"mastodon-pgsql-credentials-{mastodon_hostname}"
            )[0]['id']

    elastic_id = bitwarden.get_item(
            f"mastodon-elasticsearch-credentials-{mastodon_hostname}", False
            )[0]['id']

    valkey_id = bitwarden.get_item(
            f"mastodon-valkey-credentials-{mastodon_hostname}", False
            )[0]['id']

    smtp_id = bitwarden.get_item(
            f"mastodon-smtp-credentials-{mastodon_hostname}", False
            )[0]['id']

    s3_admin_id = bitwarden.get_item(
            f"mastodon-admin-s3-credentials-{mastodon_hostname}", False
            )[0]['id']

    s3_db_id = bitwarden.get_item(
            f"mastodon-postgres-s3-credentials-{mastodon_hostname}", False
            )[0]['id']

    s3_id = bitwarden.get_item(
            f"mastodon-user-s3-credentials-{mastodon_hostname}", False
            )[0]['id']

    s3_backups_id = bitwarden.get_item(
            f"mastodon-backups-s3-credentials-{mastodon_hostname}", False
            )[0]['id']

    secrets_id = bitwarden.get_item(
            f"mastodon-server-secrets-{mastodon_hostname}", False
            )[0]['id']

    # do some checking here since this isn't required and so it may not be available
    libretranslate_api_key_item = bitwarden.get_item(
            f"mastodon-libretranslate-credentials-{mastodon_hostname}", False
            )[0]
    if libretranslate_api_key_item:
        libretranslate_api_key_id = libretranslate_api_key_item.get('id', "")
    else:
        endpoint = create_custom_field('endpoint',
                                       mastodon_libretranslate_hostname)
        libretranslate_api_key_id = bitwarden.create_login(
                name=f'mastodon-libretranslate-credentials-{mastodon_hostname}',
                item_url=mastodon_libretranslate_hostname,
                user="n/a",
                password=libre_api_key,
                fields=[endpoint]
                )

    # {'mastodon_admin_credentials_bitwarden_id': admin_id,
    argocd.update_appset_secret(
            {'mastodon_smtp_credentials_bitwarden_id': smtp_id,
             'mastodon_postgres_credentials_bitwarden_id': db_id,
             'mastodon_valkey_bitwarden_id': valkey_id,
             'mastodon_s3_admin_credentials_bitwarden_id': s3_admin_id,
             'mastodon_s3_postgres_credentials_bitwarden_id': s3_db_id,
             'mastodon_s3_mastodon_credentials_bitwarden_id': s3_id,
             'mastodon_s3_backups_credentials_bitwarden_id': s3_backups_id,
             'mastodon_elasticsearch_credentials_bitwarden_id': elastic_id,
             'mastodon_libretranslate_bitwarden_id': libretranslate_api_key_id,
             'mastodon_server_secrets_bitwarden_id': secrets_id}
            )


def setup_bitwarden_items(argocd: ArgoCD,
                          mastodon_hostname: str,
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
                          rake_secrets: dict,
                          mastodon_libretranslate_hostname: str,
                          libre_api_key: str,
                          bitwarden: BwCLI) -> None:
    # S3 credentials
    # endpoint that gets put into the secret should probably have http in it
    if "http" not in s3_endpoint:
        log.debug(f"Mastodon s3_endpoint did not have http in it: {s3_endpoint}")
        s3_endpoint = "https://" + s3_endpoint
        log.debug(f"Mastodon s3_endpoint - after prepending 'https://': {s3_endpoint}")

    mastodon_s3_endpoint_obj = create_custom_field("s3Endpoint", s3_endpoint)
    mastodon_s3_host_obj = create_custom_field("s3Hostname",
                                               s3_endpoint.replace("https://",
                                                                   ""))
    mastodon_s3_bucket_obj = create_custom_field("s3Bucket", "mastodon")
    s3_id = bitwarden.create_login(
            name='mastodon-user-s3-credentials',
            item_url=mastodon_hostname,
            user=s3_access_id,
            password=s3_access_key,
            fields=[
                mastodon_s3_endpoint_obj,
                mastodon_s3_host_obj,
                mastodon_s3_bucket_obj
                ]
            )

    pgsql_s3_key = create_password()
    s3_db_id = bitwarden.create_login(
            name='mastodon-postgres-s3-credentials',
            item_url=mastodon_hostname,
            user="mastodon-postgres",
            password=pgsql_s3_key
            )

    admin_s3_key = create_password()
    s3_admin_id = bitwarden.create_login(
            name='mastodon-admin-s3-credentials',
            item_url=mastodon_hostname,
            user="mastodon-root",
            password=admin_s3_key
            )

    # credentials for remote backups of the s3 PVC
    restic_repo_pass_obj = create_custom_field("resticRepoPassword", restic_repo_pass)
    s3_backups_id = bitwarden.create_login(
            name='mastodon-backups-s3-credentials',
            item_url=mastodon_hostname,
            user=backups_s3_user,
            password=backups_s3_password,
            fields=[restic_repo_pass_obj]
            )

    # elastic search password
    mastodon_elasticsearch_password = bitwarden.generate()
    elastic_id = bitwarden.create_login(
            name='mastodon-elasticsearch-credentials',
            item_url=mastodon_hostname,
            user='mastodon',
            password=mastodon_elasticsearch_password
            )

    # PostgreSQL credentials
    mastodon_pgsql_password = bitwarden.generate()
    postrges_pass_obj = create_custom_field("postgresPassword",
                                            mastodon_pgsql_password)
    db_id = bitwarden.create_login(
            name='mastodon-pgsql-credentials',
            item_url=mastodon_hostname,
            user='mastodon',
            password=mastodon_pgsql_password,
            fields=[postrges_pass_obj]
            )

    # valkey credentials
    mastodon_valkey_password = bitwarden.generate()
    valkey_id = bitwarden.create_login(
            name='mastodon-valkey-credentials',
            item_url=mastodon_hostname,
            user='mastodon',
            password=mastodon_valkey_password
            )

    # SMTP credentials
    mastodon_smtp_host_obj = create_custom_field("smtpHostname", mail_host)
    smtp_id = bitwarden.create_login(
            name='mastodon-smtp-credentials',
            item_url=mastodon_hostname,
            user=mail_user,
            password=mail_pass,
            fields=[mastodon_smtp_host_obj]
            )

    # admin credentials for mastodon itself
    # toot_password = create_password()
    # email_obj = create_custom_field("email", mastodon_admin_email)
    # admin_id = bitwarden.create_login(
    #         name='mastodon-admin-credentials',
    #         item_url=mastodon_hostname,
    #         user=mastodon_admin_username,
    #         password=toot_password,
    #         fields=[email_obj]
    #         )

    # mastodon secrets
    secret_key_base_obj = create_custom_field(
            "SECRET_KEY_BASE",
            rake_secrets['SECRET_KEY_BASE']
            )
    otp_secret_obj = create_custom_field(
            "OTP_SECRET",
            rake_secrets['OTP_SECRET']
            )
    vapid_pub_key_obj = create_custom_field(
            "VAPID_PUBLIC_KEY",
            rake_secrets['VAPID_PUBLIC_KEY']
            )
    vapid_priv_key_obj = create_custom_field(
            "VAPID_PRIVATE_KEY",
            rake_secrets['VAPID_PRIVATE_KEY']
            )
    active_record_encryption_deterministic_obj = create_custom_field(
            "ACTIVE_RECORD_ENCRYPTION_DETERMINISTIC_KEY",
            rake_secrets['ACTIVE_RECORD_ENCRYPTION_DETERMINISTIC_KEY']
            )
    active_record_encryption_derivation_obj = create_custom_field(
            "ACTIVE_RECORD_ENCRYPTION_KEY_DERIVATION_SALT",
            rake_secrets['ACTIVE_RECORD_ENCRYPTION_KEY_DERIVATION_SALT']
            )
    active_record_encryption_primary_obj = create_custom_field(
            "ACTIVE_RECORD_ENCRYPTION_PRIMARY_KEY",
            rake_secrets['ACTIVE_RECORD_ENCRYPTION_PRIMARY_KEY']
            )

    secrets_id = bitwarden.create_login(
            name='mastodon-server-secrets',
            item_url=mastodon_hostname,
            user="mastodon",
            password="none",
            fields=[
                secret_key_base_obj,
                otp_secret_obj,
                vapid_priv_key_obj,
                vapid_pub_key_obj,
                active_record_encryption_primary_obj,
                active_record_encryption_derivation_obj,
                active_record_encryption_deterministic_obj
                ]
            )

    endpoint = create_custom_field('endpoint', mastodon_libretranslate_hostname)
    libretranslate_api_key_id = bitwarden.create_login(
            name=f'mastodon-libretranslate-credentials-{mastodon_hostname}',
            item_url=mastodon_libretranslate_hostname,
            user="n/a",
            password=libre_api_key,
            fields=[endpoint]
            )

    # update the mastodon values for the argocd appset
    # 'mastodon_admin_credentials_bitwarden_id': admin_id,
    argocd.update_appset_secret(
            {'mastodon_smtp_credentials_bitwarden_id': smtp_id,
             'mastodon_postgres_credentials_bitwarden_id': db_id,
             'mastodon_valkey_bitwarden_id': valkey_id,
             'mastodon_s3_admin_credentials_bitwarden_id': s3_admin_id,
             'mastodon_s3_postgres_credentials_bitwarden_id': s3_db_id,
             'mastodon_s3_mastodon_credentials_bitwarden_id': s3_id,
             'mastodon_s3_backups_credentials_bitwarden_id': s3_backups_id,
             'mastodon_elasticsearch_credentials_bitwarden_id': elastic_id,
             'mastodon_server_secrets_bitwarden_id': secrets_id,
             'mastodon_libretranslate_bitwarden_id': libretranslate_api_key_id})

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


def restore_mastodon(argocd: ArgoCD,
                     mastodon_hostname: str,
                     mastodon_namespace: str,
                     argo_dict: dict,
                     secrets: dict,
                     restore_dict: dict,
                     backup_dict: dict,
                     global_pvc_storage_class: str,
                     pgsql_cluster_name: str,
                     mastodon_libretranslate_hostname: str,
                     libre_api_key: str,
                     bitwarden: BwCLI) -> None:
    """
    restore mastodon seaweedfs PVCs, mastodon files and/or config PVC(s),
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
        refresh_bweso(argocd, mastodon_hostname, mastodon_libretranslate_hostname, libre_api_key, bitwarden)

        # apply the external secrets so we can immediately use them for restores
        external_secrets_yaml = (
                f"https://raw.githubusercontent.com/small-hack/argocd-apps/{revision}/"
                f"{argo_path}external_secrets_argocd_appset.yaml"
                )
        argocd.k8s.apply_manifests(external_secrets_yaml, argocd.namespace)

        # postgresql s3 ID
        s3_db_creds = bitwarden.get_item(
                f"mastodon-postgres-s3-credentials-{mastodon_hostname}", False
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
            'mastodon',
            mastodon_namespace,
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
                             'mastodon',
                             mastodon_namespace,
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

    # then we begin the restic restore of all the mastodon PVCs we lost
    for pvc in ['valkey_primary', 'valkey_replica']:
        pvc_enabled = secrets.get('valkey_pvc_enabled', 'false')
        if pvc_enabled and pvc_enabled.lower() != 'false':
            # restores the mastodon pvc
            k8up_restore_pvc(
                    k8s_obj=argocd.k8s,
                    app='mastodon',
                    pvc=f'mastodon-{pvc.replace("_","-")}',
                    namespace='mastodon',
                    s3_endpoint=s3_backup_endpoint,
                    s3_bucket=s3_backup_bucket,
                    access_key_id=access_key_id,
                    secret_access_key=secret_access_key,
                    restic_repo_password=restic_repo_password,
                    snapshot_id=snapshot_ids[f'mastodon_{pvc}'],
                    pod_config="file-backups-podconfig"
                    )

    # todo: from here on out, this could be async to start on other tasks
    # install mastodon as usual, but wait on it this time
    argocd.install_app('mastodon', argo_dict, True)
