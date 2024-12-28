# internal libraries
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_apps.operators.minio import create_minio_alias
# from smol_k8s_lab.k8s_apps.social.gotosocial_secrets import generate_gotosocial_secrets
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


def configure_gotosocial(argocd: ArgoCD,
                         cfg: dict,
                         pvc_storage_class: str,
                         bitwarden: BwCLI = None) -> bool:
    """
    creates a gotosocial app and initializes it with secrets if you'd like :)

    required:
        argocd                 - ArgoCD() object for Argo CD operations
        cfg                    - dict, with at least argocd key and init key
        pvc_storage_class      - str, storage class of PVC

    optional:
        bitwarden   - BwCLI() object with session token to create bitwarden items

    not available yet:
        libretranslate_api_key - str, api key to enable automatic translations
    """
    # check immediately if the app is installed
    app_installed = argocd.check_if_app_exists('gotosocial')

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

    header(f"{header_start} [green]gotosocial[/], so you can self host your social media",
           '🦥')

    # get any secrets for this app
    secrets = cfg['argo']['secret_keys']
    if secrets:
        gotosocial_hostname = secrets['hostname']
        # gotosocial_libretranslate_hostname = secrets['libretranslate_hostname']

    # we need namespace immediately
    gotosocial_namespace = cfg['argo']['namespace']

    if init_enabled:
        # declare custom values for gotosocial
        init_values = init.get('values', None)

        # backups are their own config.yaml section
        backup_vals = process_backup_vals(cfg.get('backups', {}), 'gotosocial', argocd)

        # get the api key for LibreTranslate, so we can translate posts
        # libre_api_key = extract_secret(init_values.get('libretranslate_api_key'))
        # if not libre_api_key:
        #     libre_api_key = libretranslate_api_key

    if init_enabled and not app_installed:
        argocd.k8s.create_namespace(gotosocial_namespace)

        if not restore_enabled:
            # configure the admin user credentials
            gotosocial_admin_username = init_values.get('admin_user', 'tootadmin')
            gotosocial_admin_email = init_values.get('admin_email', '')

            # configure the smtp credentials
            mail_user = init_values.get('smtp_user', '')
            mail_host = init_values.get('smtp_host', '')
            mail_pass = extract_secret(init_values.get('smtp_password'))

            # main gotosocial rake secrets
            # rake_secrets = generate_gotosocial_secrets()

            # configure s3 credentials
            s3_access_id = 'gotosocial'
            s3_access_key = create_password()

        s3_endpoint = secrets.get('s3_endpoint', "")
        log.debug(f"gotosocial s3_endpoint at the start is: {s3_endpoint}")

        if not restore_enabled:
            # create a local alias to check and make sure gotosocial is functional
            create_minio_alias("gotosocial", s3_endpoint, "gotosocial", s3_access_key)

        if bitwarden and not restore_enabled:
            # rake_secrets,
            # gotosocial_libretranslate_hostname,
            # libre_api_key,
            setup_bitwarden_items(argocd,
                                  gotosocial_hostname,
                                  s3_endpoint,
                                  s3_access_id,
                                  s3_access_key,
                                  backup_vals['s3_user'],
                                  backup_vals['s3_password'],
                                  backup_vals['restic_repo_pass'],
                                  gotosocial_admin_username,
                                  mail_host,
                                  mail_user,
                                  mail_pass,
                                  bitwarden)

        # these are standard k8s secrets yaml
        elif not bitwarden and not restore_enabled:
            # admin creds k8s secret
            # k8s_obj.create_secret('gotosocial-admin-credentials', 'gotosocial',
            #               {"username": username,
            #                "email": email})

            # postgres creds k8s secret
            gotosocial_pgsql_password = create_password()
            argocd.k8s.create_secret(
                    'gotosocial-pgsql-credentials',
                    'gotosocial',
                    {"password": gotosocial_pgsql_password,
                     'postrgesPassword': gotosocial_pgsql_password})

            # valkey creds k8s secret
            gotosocial_valkey_password = create_password()
            argocd.k8s.create_secret('gotosocial-valkey-credentials', 'gotosocial',
                                     {"password": gotosocial_valkey_password})

            # gotosocial rake secrets
            # argocd.k8s.create_secret('gotosocial-server-secrets', 'gotosocial',
            # rake_secrets)

    if not app_installed:
        if restore_enabled:
            # gotosocial_libretranslate_hostname,
            # libre_api_key,
            restore_gotosocial(argocd,
                             gotosocial_hostname,
                             gotosocial_namespace,
                             cfg['argo'],
                             secrets,
                             restore_dict,
                             backup_vals,
                             pvc_storage_class,
                             'gotosocial-postgres',
                             bitwarden)

        if not init_enabled:
            argocd.install_app('gotosocial', cfg['argo'])
        elif init_enabled and not restore_enabled:
            argocd.install_app('gotosocial', cfg['argo'], True)
            # wait for all the gotosocial apps to come up, give it extra time
            argocd.sync_app(app='gotosocial-web-app', sleep_time=4)
            argocd.wait_for_app('gotosocial-web-app')

            # create admin credentials
            password = create_user(gotosocial_admin_username,
                                   gotosocial_admin_email,
                                   cfg['argo']['namespace'])
            if bitwarden:
                sub_header("Creating secrets in Bitwarden")
                bitwarden.create_login(
                        name='gotosocial-admin-credentials',
                        item_url=gotosocial_hostname,
                        user=gotosocial_admin_username,
                        password=password,
                        fields=[create_custom_field("email", gotosocial_admin_email)]
                        )
    else:
        log.info("gotosocial already installed 🎉")

        if bitwarden and init_enabled:
            # gotosocial_libretranslate_hostname, libre_api_key,
            refresh_bweso(argocd, gotosocial_hostname, bitwarden)


def create_user(user: str, email: str, pod_namespace: str) -> str:
    """
    given a username, email, and namespace of the gotosocial pod, we'll create a
    new gotosocial user using a kubectl exec command and then we return
    their autogenerated password
    """
    sub_header(f"Creating a gotosocial user for: {user}")
    # first, go get the exact name of the pod we need to exec a command on
    pod_cmd = (
            f"kubectl get pods -n {pod_namespace} "
            "-l app.kubernetes.io/instance=gotosocial-web-app,app.kubernetes.io/component=web"
            " --no-headers "
            "-o custom-columns=NAME:.metadata.name"
            )
    pod = subproc([pod_cmd]).rstrip()
    log.info(f"gotosocial web app pod is: {pod}")

    # generate a random password
    password = create_password()

    # then run the user creation command
    cmd = (f'kubectl exec -n {pod_namespace} {pod} -- /bin/bash -c "gotosocial '
           '--config-path /path/to/config.yaml admin account create '
           f'--username {user} --email {email} --password \'{password}\'')

    # then process the output from the command
    subproc([cmd], shell=True, universal_newlines=True)


    # then run the user promotion (to admin) command
    cmd = (f'kubectl exec -n {pod_namespace} {pod} -- /bin/bash -c "gotosocial '
           '--config-path /path/to/config.yaml admin account promote '
           f'--username {user}')

    # then process the output from the command
    subproc([cmd], shell=True, universal_newlines=True).split()[3]

    return password


def refresh_bweso(argocd: ArgoCD,
                  gotosocial_hostname: str,
                  gotosocial_libretranslate_hostname: str,
                  libre_api_key: str,
                  bitwarden: BwCLI) -> None:
    """
    if gotosocial already installed, but bitwarden and init are enabled, still
    populate the bitwarden IDs in the appset secret plugin secret
    """
    log.debug("Making sure gotosocial Bitwarden item IDs are in appset "
              "secret plugin secret")

    # admin_id = bitwarden.get_item(
    #         f"gotosocial-admin-credentials-{gotosocial_hostname}"
    #         )[0]['id']

    db_id = bitwarden.get_item(
            f"gotosocial-pgsql-credentials-{gotosocial_hostname}"
            )[0]['id']

    elastic_id = bitwarden.get_item(
            f"gotosocial-elasticsearch-credentials-{gotosocial_hostname}", False
            )[0]['id']

    valkey_id = bitwarden.get_item(
            f"gotosocial-valkey-credentials-{gotosocial_hostname}", False
            )[0]['id']

    smtp_id = bitwarden.get_item(
            f"gotosocial-smtp-credentials-{gotosocial_hostname}", False
            )[0]['id']

    s3_admin_id = bitwarden.get_item(
            f"gotosocial-admin-s3-credentials-{gotosocial_hostname}", False
            )[0]['id']

    s3_db_id = bitwarden.get_item(
            f"gotosocial-postgres-s3-credentials-{gotosocial_hostname}", False
            )[0]['id']

    s3_id = bitwarden.get_item(
            f"gotosocial-user-s3-credentials-{gotosocial_hostname}", False
            )[0]['id']

    s3_backups_id = bitwarden.get_item(
            f"gotosocial-backups-s3-credentials-{gotosocial_hostname}", False
            )[0]['id']

    secrets_id = bitwarden.get_item(
            f"gotosocial-server-secrets-{gotosocial_hostname}", False
            )[0]['id']

    # do some checking here since this isn't required and so it may not be available
    # libretranslate_api_key_item = bitwarden.get_item(
    #         f"gotosocial-libretranslate-credentials-{gotosocial_hostname}", False
    #         )[0]
    # if libretranslate_api_key_item:
    #     libretranslate_api_key_id = libretranslate_api_key_item.get('id', "")
    # else:
    #     endpoint = create_custom_field('endpoint',
    #                                    gotosocial_libretranslate_hostname)
    #     libretranslate_api_key_id = bitwarden.create_login(
    #             name=f'gotosocial-libretranslate-credentials-{gotosocial_hostname}',
    #             item_url=gotosocial_libretranslate_hostname,
    #             user="n/a",
    #             password=libre_api_key,
    #             fields=[endpoint]
    #             )
    # {'gotosocial_admin_credentials_bitwarden_id': admin_id,
    #  'gotosocial_libretranslate_bitwarden_id': libretranslate_api_key_id,
    argocd.update_appset_secret(
            {'gotosocial_smtp_credentials_bitwarden_id': smtp_id,
             'gotosocial_postgres_credentials_bitwarden_id': db_id,
             'gotosocial_valkey_bitwarden_id': valkey_id,
             'gotosocial_s3_admin_credentials_bitwarden_id': s3_admin_id,
             'gotosocial_s3_postgres_credentials_bitwarden_id': s3_db_id,
             'gotosocial_s3_gotosocial_credentials_bitwarden_id': s3_id,
             'gotosocial_s3_backups_credentials_bitwarden_id': s3_backups_id,
             'gotosocial_elasticsearch_credentials_bitwarden_id': elastic_id,
             'gotosocial_server_secrets_bitwarden_id': secrets_id}
            )


def setup_bitwarden_items(argocd: ArgoCD,
                          gotosocial_hostname: str,
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
                          bitwarden: BwCLI) -> None:
    """
    setup secrets in bitwarden for gotosocial.

    removed the following from the clone of the mastodon file:
      rake_secrets: dict,
      gotosocial_libretranslate_hostname: str,
      libre_api_key: str,
    """

    # S3 credentials
    # endpoint that gets put into the secret should probably have http in it
    if "http" not in s3_endpoint:
        log.debug(f"gotosocial s3_endpoint did not have http in it: {s3_endpoint}")
        s3_endpoint = "https://" + s3_endpoint
        log.debug(f"gotosocial s3_endpoint - after prepending 'https://': {s3_endpoint}")

    gotosocial_s3_endpoint_obj = create_custom_field("s3Endpoint", s3_endpoint)
    gotosocial_s3_host_obj = create_custom_field("s3Hostname",
                                               s3_endpoint.replace("https://",
                                                                   ""))
    gotosocial_s3_bucket_obj = create_custom_field("s3Bucket", "gotosocial")
    s3_id = bitwarden.create_login(
            name='gotosocial-user-s3-credentials',
            item_url=gotosocial_hostname,
            user=s3_access_id,
            password=s3_access_key,
            fields=[
                gotosocial_s3_endpoint_obj,
                gotosocial_s3_host_obj,
                gotosocial_s3_bucket_obj
                ]
            )

    pgsql_s3_key = create_password()
    s3_db_id = bitwarden.create_login(
            name='gotosocial-postgres-s3-credentials',
            item_url=gotosocial_hostname,
            user="gotosocial-postgres",
            password=pgsql_s3_key
            )

    admin_s3_key = create_password()
    s3_admin_id = bitwarden.create_login(
            name='gotosocial-admin-s3-credentials',
            item_url=gotosocial_hostname,
            user="gotosocial-root",
            password=admin_s3_key
            )

    # credentials for remote backups of the s3 PVC
    restic_repo_pass_obj = create_custom_field("resticRepoPassword", restic_repo_pass)
    s3_backups_id = bitwarden.create_login(
            name='gotosocial-backups-s3-credentials',
            item_url=gotosocial_hostname,
            user=backups_s3_user,
            password=backups_s3_password,
            fields=[restic_repo_pass_obj]
            )

    # elastic search password
    gotosocial_elasticsearch_password = bitwarden.generate()
    elastic_id = bitwarden.create_login(
            name='gotosocial-elasticsearch-credentials',
            item_url=gotosocial_hostname,
            user='gotosocial',
            password=gotosocial_elasticsearch_password
            )

    # PostgreSQL credentials
    gotosocial_pgsql_password = bitwarden.generate()
    postrges_pass_obj = create_custom_field("postgresPassword",
                                            gotosocial_pgsql_password)
    db_id = bitwarden.create_login(
            name='gotosocial-pgsql-credentials',
            item_url=gotosocial_hostname,
            user='gotosocial',
            password=gotosocial_pgsql_password,
            fields=[postrges_pass_obj]
            )

    # valkey credentials
    gotosocial_valkey_password = bitwarden.generate()
    valkey_id = bitwarden.create_login(
            name='gotosocial-valkey-credentials',
            item_url=gotosocial_hostname,
            user='gotosocial',
            password=gotosocial_valkey_password
            )

    # SMTP credentials
    gotosocial_smtp_host_obj = create_custom_field("smtpHostname", mail_host)
    smtp_id = bitwarden.create_login(
            name='gotosocial-smtp-credentials',
            item_url=gotosocial_hostname,
            user=mail_user,
            password=mail_pass,
            fields=[gotosocial_smtp_host_obj]
            )

    # admin credentials for gotosocial itself
    # toot_password = create_password()
    # email_obj = create_custom_field("email", gotosocial_admin_email)
    # admin_id = bitwarden.create_login(
    #         name='gotosocial-admin-credentials',
    #         item_url=gotosocial_hostname,
    #         user=gotosocial_admin_username,
    #         password=toot_password,
    #         fields=[email_obj]
    #         )

    # gotosocial secrets
    # secret_key_base_obj = create_custom_field(
    #         "SECRET_KEY_BASE",
    #         rake_secrets['SECRET_KEY_BASE']
    #         )
    # otp_secret_obj = create_custom_field(
    #         "OTP_SECRET",
    #         rake_secrets['OTP_SECRET']
    #         )
    # vapid_pub_key_obj = create_custom_field(
    #         "VAPID_PUBLIC_KEY",
    #         rake_secrets['VAPID_PUBLIC_KEY']
    #         )
    # vapid_priv_key_obj = create_custom_field(
    #         "VAPID_PRIVATE_KEY",
    #         rake_secrets['VAPID_PRIVATE_KEY']
    #         )
    # active_record_encryption_deterministic_obj = create_custom_field(
    #         "ACTIVE_RECORD_ENCRYPTION_DETERMINISTIC_KEY",
    #         rake_secrets['ACTIVE_RECORD_ENCRYPTION_DETERMINISTIC_KEY']
    #         )
    # active_record_encryption_derivation_obj = create_custom_field(
    #         "ACTIVE_RECORD_ENCRYPTION_KEY_DERIVATION_SALT",
    #         rake_secrets['ACTIVE_RECORD_ENCRYPTION_KEY_DERIVATION_SALT']
    #         )
    # active_record_encryption_primary_obj = create_custom_field(
    #         "ACTIVE_RECORD_ENCRYPTION_PRIMARY_KEY",
    #         rake_secrets['ACTIVE_RECORD_ENCRYPTION_PRIMARY_KEY']
    #         )

    # secrets_id = bitwarden.create_login(
    #         name='gotosocial-server-secrets',
    #         item_url=gotosocial_hostname,
    #         user="gotosocial",
    #         password="none",
    #         fields=[
    #             secret_key_base_obj,
    #             otp_secret_obj,
    #             vapid_priv_key_obj,
    #             vapid_pub_key_obj,
    #             active_record_encryption_primary_obj,
    #             active_record_encryption_derivation_obj,
    #             active_record_encryption_deterministic_obj
    #             ]
    #         )

    # endpoint = create_custom_field('endpoint', gotosocial_libretranslate_hostname)
    # libretranslate_api_key_id = bitwarden.create_login(
    #         name=f'gotosocial-libretranslate-credentials-{gotosocial_hostname}',
    #         item_url=gotosocial_libretranslate_hostname,
    #         user="n/a",
    #         password=libre_api_key,
    #         fields=[endpoint]
    #         )

    # update the gotosocial values for the argocd appset
    # 'gotosocial_admin_credentials_bitwarden_id': admin_id,
    # 'gotosocial_server_secrets_bitwarden_id': secrets_id,
    # 'gotosocial_libretranslate_bitwarden_id': libretranslate_api_key_id})
    argocd.update_appset_secret(
            {'gotosocial_smtp_credentials_bitwarden_id': smtp_id,
             'gotosocial_postgres_credentials_bitwarden_id': db_id,
             'gotosocial_valkey_bitwarden_id': valkey_id,
             'gotosocial_s3_admin_credentials_bitwarden_id': s3_admin_id,
             'gotosocial_s3_postgres_credentials_bitwarden_id': s3_db_id,
             'gotosocial_s3_gotosocial_credentials_bitwarden_id': s3_id,
             'gotosocial_s3_backups_credentials_bitwarden_id': s3_backups_id,
             'gotosocial_elasticsearch_credentials_bitwarden_id': elastic_id})

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


def restore_gotosocial(argocd: ArgoCD,
                     gotosocial_hostname: str,
                     gotosocial_namespace: str,
                     argo_dict: dict,
                     secrets: dict,
                     restore_dict: dict,
                     backup_dict: dict,
                     global_pvc_storage_class: str,
                     pgsql_cluster_name: str,
                     bitwarden: BwCLI) -> None:
    """
    restore gotosocial seaweedfs PVCs, gotosocial files and/or config PVC(s),
    and CNPG postgresql cluster

    removed vars:
         gotosocial_libretranslate_hostname: str,
         libre_api_key: str,
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
        # gotosocial_libretranslate_hostname, libre_api_key,
        refresh_bweso(argocd, gotosocial_hostname, bitwarden)

        # apply the external secrets so we can immediately use them for restores
        external_secrets_yaml = (
                f"https://raw.githubusercontent.com/small-hack/argocd-apps/{revision}/"
                f"{argo_path}external_secrets_argocd_appset.yaml"
                )
        argocd.k8s.apply_manifests(external_secrets_yaml, argocd.namespace)

        # postgresql s3 ID
        s3_db_creds = bitwarden.get_item(
                f"gotosocial-postgres-s3-credentials-{gotosocial_hostname}", False
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
            'gotosocial',
            gotosocial_namespace,
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
                             'gotosocial',
                             gotosocial_namespace,
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

    # then we begin the restic restore of all the gotosocial PVCs we lost
    for pvc in ['valkey_primary', 'valkey_replica']:
        pvc_enabled = secrets.get('valkey_pvc_enabled', 'false')
        if pvc_enabled and pvc_enabled.lower() != 'false':
            # restores the gotosocial pvc
            k8up_restore_pvc(
                    k8s_obj=argocd.k8s,
                    app='gotosocial',
                    pvc=f'gotosocial-{pvc.replace("_","-")}',
                    namespace='gotosocial',
                    s3_endpoint=s3_backup_endpoint,
                    s3_bucket=s3_backup_bucket,
                    access_key_id=access_key_id,
                    secret_access_key=secret_access_key,
                    restic_repo_password=restic_repo_password,
                    snapshot_id=snapshot_ids[f'gotosocial_{pvc}'],
                    pod_config="file-backups-podconfig"
                    )

    # todo: from here on out, this could be async to start on other tasks
    # install gotosocial as usual, but wait on it this time
    argocd.install_app('gotosocial', argo_dict, True)
