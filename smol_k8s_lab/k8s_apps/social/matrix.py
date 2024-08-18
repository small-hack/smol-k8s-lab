# internal libraries
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_apps.operators.minio import create_minio_alias
from smol_k8s_lab.k8s_apps.identity_provider.zitadel_api import Zitadel
from smol_k8s_lab.k8s_tools.argocd_util import ArgoCD
from smol_k8s_lab.k8s_tools.restores import (restore_seaweedfs,
                                             k8up_restore_pvc,
                                             recreate_pvc,
                                             restore_cnpg_cluster)
from smol_k8s_lab.utils.value_from import process_backup_vals, extract_secret
from smol_k8s_lab.utils.rich_cli.console_logging import sub_header, header
from smol_k8s_lab.utils.passwords import create_password

# external libraries
import logging as log
from ulid import ULID


def configure_matrix(argocd: ArgoCD,
                     cfg: dict,
                     pvc_storage_class: str,
                     zitadel: Zitadel,
                     bitwarden: BwCLI = None) -> bool:
    """
    creates a matrix app and initializes it with secrets if you'd like :)

    required:
        argocd            - ArgoCD() object for Argo CD operations
        cfg               - dict, with at least argocd key and init key
        pvc_storage_class - str, storage class of PVC

    optional:
        zitadel     - Zitadel() object with session token to create zitadel oidc app and roles
        bitwarden   - BwCLI() object with session token to create bitwarden items
    """
    # verify immediately if matrix is installed
    app_installed = argocd.check_if_app_exists('matrix')

    # verify if initialization is enabled
    init = cfg.get('init', {'enabled': True, 'restore': {'enabled': False}})
    init_enabled = init.get('enabled', True)
    init_values = init.get('values', {})

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

    header(f"{header_start} [green]Matrix[/], so you can self host your own chat",
           '💬')

    secrets = cfg['argo']['secret_keys']
    if secrets:
        matrix_hostname = secrets['hostname']

    # always declare matrix namespace immediately
    matrix_namespace = cfg['argo']['namespace']

    if init_enabled:
        backup_vals = process_backup_vals(cfg['backups'], 'matrix', argocd)

    # initial secrets to deploy this app from scratch
    if init_enabled and not app_installed:
        argocd.k8s.create_namespace(matrix_namespace)

        # configure s3 credentials
        s3_endpoint = secrets.get('s3_endpoint', "")
        s3_bucket = secrets.get('s3_bucket', "matrix")
        s3_access_id = 'matrix'
        s3_access_key = create_password()

        # configure the smtp credentials
        mail_user = init_values['smtp_user']
        mail_pass = extract_secret(init_values['smtp_password'])
        mail_host = init_values['smtp_host']

        # create a local alias to check and make sure matrix is functional
        create_minio_alias("matrix", s3_endpoint, "matrix", s3_access_key)

        # secret for the token header for matrix to talk to sliding sync
        syncv3_secret = create_password()

        # create Matrix OIDC Application
        if zitadel and not restore_enabled:
            log.debug("Creating an OIDC application in Zitadel...")
            mas_issuer = f"https://{zitadel.hostname}"
            mas_client_id = str(ULID())
            mas_provider_ulid = str(ULID())
            mas_client_secret = create_password()
            mas_admin_token = create_password()
            matrix_auth_hostname = secrets.get("auth_hostname", "")
            zitadel_hostname = zitadel.hostname
            logout_uris = [f"https://{matrix_hostname}"]

            # If using MAS (Matrix authentication service), use different redirect URI
            if matrix_auth_hostname:
                redirect_uris = f"https://{matrix_auth_hostname}/upstream/callback/{mas_provider_ulid}"
            else:
                redirect_uris = f"https://{matrix_hostname}/_synapse/client/oidc/callback"

            oidc_creds = zitadel.create_application("matrix",
                                                    redirect_uris,
                                                    logout_uris)
            zitadel.create_role("matrix_users", "Matrix Users", "matrix_users")
            zitadel.update_user_grant(['matrix_users'])
        else:
            zitadel_hostname = ""

        # if the user has bitwarden enabled
        if bitwarden and not restore_enabled:
            if "bridges" in cfg['argo']['path'] and init_enabled:
                github_app_id = extract_secret(init_values.get("github_app_id"))
                github_webhook_secret = extract_secret(init_values.get("github_webhook_secret"))
                github_client_id = extract_secret(init_values.get("github_client_id"))
                github_client_secret = extract_secret(init_values.get("github_client_secret"))
                github_private_key = extract_secret(init_values.get("github_private_key"))
            else:
                github_app_id = "not applicable"
                github_webhook_secret = "not applicable"
                github_client_id = "not applicable"
                github_client_secret = "not applicable"
                github_private_key = "not applicable"

            setup_bitwarden_items(argocd,
                                  matrix_hostname,
                                  matrix_namespace,
                                  s3_endpoint,
                                  s3_access_id,
                                  s3_access_key,
                                  s3_bucket,
                                  backup_vals['s3_user'],
                                  backup_vals['s3_password'],
                                  backup_vals['restic_repo_pass'],
                                  mail_host,
                                  mail_user,
                                  mail_pass,
                                  zitadel_hostname,
                                  oidc_creds,
                                  mas_provider_ulid,
                                  mas_issuer,
                                  mas_client_id,
                                  mas_client_secret,
                                  mas_admin_token,
                                  syncv3_secret,
                                  github_app_id,
                                  github_webhook_secret,
                                  github_client_id,
                                  github_client_secret,
                                  github_private_key,
                                  bitwarden)

        # else create these as Kubernetes secrets
        elif not bitwarden and not restore_enabled:
            # postgresql credentials
            argocd.k8s.create_secret(
                    'matrix-pgsql-credentials',
                    'matrix',
                    {"password": "we-use-tls-instead-of-password-now",
                     "database": "matrix-postgres",
                     "hostname": f"matrix-postgres-rw.{matrix_namespace}.svc"}
                    )

            argocd.k8s.create_secret(
                    'mas-pgsql-credentials',
                    'matrix',
                    {"password": "we-use-tls-instead-of-password-now",
                     "database": "mas",
                     "hostname": f"mas-rw.{matrix_namespace}.svc"}
                    )

            pgconnstr = ("user=syncv3 dbname=syncv3 "
                         f"host=mas-rw.{matrix_namespace}.svc "
                         "sslmode=verify-full sslkey=/etc/secrets/synvcv3/tls.key"
                         " sslcert=/etc/secrets/syncv3/tls.crt "
                         "sslrootcert=/etc/secrets/ca/ca.crt")
            argocd.k8s.create_secret(
                    'syncv3-pgsql-credentials',
                    'matrix',
                    {"password": pgconnstr}
                    )

            # registation key
            matrix_registration_key = create_password()
            argocd.k8s.create_secret(
                    'matrix-registration',
                    'matrix',
                    {"registrationSharedSecret": matrix_registration_key}
                    )

            if zitadel:
                # oidc secret
                argocd.k8s.create_secret(
                        'matrix-oidc-credentials',
                        'matrix',
                        {'user': oidc_creds['client_id'],
                         'password': oidc_creds['client_secret'],
                         'issuer': zitadel.hostname}
                        )

                # matrix-athentication-service secret
                argocd.k8s.create_secret(
                        'matrix-authentication-service-secret',
                        'matrix',
                        {'provider_id': mas_provider_ulid,
                         'issuer': mas_issuer,
                         'client_id': mas_client_id,
                         'client_auth_method': "client_secret_basic",
                         'client_secret': mas_client_secret,
                         'admin_token': mas_admin_token,
                         'account_management_url': zitadel.hostname}
                        )

    if init_enabled:
        # if there's trusted key servers, create a secret for them
        trusted_key_servers = init_values.get("trusted_key_servers", [])

        # if init is enabled, always create trusted_key_servers secret
        if trusted_key_servers:
            argocd.k8s.create_secret(name="trusted-key-servers",
                                     namespace=matrix_namespace,
                                     str_data={"trusted_key_servers": trusted_key_servers},
                                     inline_key="trustedKeyServers"
                                     )

    if not app_installed:
        # if the user is restoring, the process is a little different
        if init_enabled and restore_enabled:
            restore_matrix(argocd,
                           matrix_hostname,
                           matrix_namespace,
                           cfg['argo'],
                           secrets,
                           restore_dict,
                           backup_vals,
                           pvc_storage_class,
                           "matrix-postgres",
                           bitwarden)

        argocd.install_app('matrix', cfg['argo'])
    else:
        if bitwarden and init_enabled:
            refresh_bweso(argocd, matrix_hostname, bitwarden)


def refresh_bweso(argocd: ArgoCD, matrix_hostname: str, bitwarden: BwCLI):
    """
    refresh the bitwarden item IDs for use with argocd-appset-secret-plugin
    """
    log.info("matrix already installed 🎉")
    # update the matrix values for the argocd appset
    log.debug("making sure matrix bitwarden IDs are present in appset "
              "secret plugin")

    reg_id = bitwarden.get_item(
            f"matrix-registration-key-{matrix_hostname}"
            )[0]['id']

    smtp_id = bitwarden.get_item(
            f"matrix-smtp-credentials-{matrix_hostname}", False
            )[0]['id']

    ## BEGIN BRIDGES

    try:
        alertmanager_id = bitwarden.get_item(
                f"matrix-alertmanager-bridge-{matrix_hostname}", False
                )[0]['id']
    except TypeError:
        log.info("No matrix alertmanager bridge id found")
        alertmanager_id = "Not Applicable"

    try:
        discord_id = bitwarden.get_item(
                f"matrix-discord-bridge-{matrix_hostname}", False
                )[0]['id']
    except TypeError:
        log.info("No matrix discord bridge id found")
        discord_id = "Not Applicable"

    ## END BRIDGES

    s3_admin_id = bitwarden.get_item(
            f"matrix-admin-s3-credentials-{matrix_hostname}", False
            )[0]['id']

    s3_db_id = bitwarden.get_item(
            f"matrix-postgres-s3-credentials-{matrix_hostname}", False
            )[0]['id']

    s3_id = bitwarden.get_item(
            f"matrix-user-s3-credentials-{matrix_hostname}", False
            )[0]['id']

    s3_backups_id = bitwarden.get_item(
            f"matrix-backups-s3-credentials-{matrix_hostname}", False
            )[0]['id']

    db_id = bitwarden.get_item(
            f"matrix-pgsql-credentials-{matrix_hostname}", False
            )[0]['id']

    oidc_id = bitwarden.get_item(
            f"matrix-oidc-credentials-{matrix_hostname}", False
            )[0]

    try:
        sync_db_id = bitwarden.get_item(
                f"syncv3-pgsql-credentials-{matrix_hostname}", False
                )[0]['id']
    except TypeError:
        log.info("No matrix sync db id found")
        sync_db_id = "Not Applicable"

    try:
        mas_db_id = bitwarden.get_item(
                f"mas-pgsql-credentials-{matrix_hostname}", False
                )[0]['id']
    except TypeError:
        log.info("No matrix mas db id found")
        mas_db_id = "Not Applicable"

    try:
        mas_id = bitwarden.get_item(
                f"matrix-authentication-service-credentials-{matrix_hostname}", False
                )[0]['id']
    except TypeError:
        log.info("No matrix mas id found")
        mas_id = "Not Applicable"

    try:
        sync_id = bitwarden.get_item(
                f"matrix-syncv3-credentials-{matrix_hostname}", False
                )[0]['id']
    except TypeError:
        log.info("No matrix sync id found")
        sync_id = "Not Applicable"

    # identity provider name and id are nested in the oidc item fields
    for field in oidc_id['fields']:
        if field['name'] == 'idp_id':
            idp_id = field['value']
        if field['name'] == 'idp_name':
            idp_name = field['value']

    # 'matrix_trusted_key_servers_bitwarden_id': trusted_key_servers_id,
    argocd.update_appset_secret(
            {'matrix_registration_credentials_bitwarden_id': reg_id,
             'matrix_smtp_credentials_bitwarden_id': smtp_id,
             'matrix_s3_admin_credentials_bitwarden_id': s3_admin_id,
             'matrix_s3_postgres_credentials_bitwarden_id': s3_db_id,
             'matrix_s3_matrix_credentials_bitwarden_id': s3_id,
             'matrix_s3_backups_credentials_bitwarden_id': s3_backups_id,
             'matrix_postgres_credentials_bitwarden_id': db_id,
             'matrix_sliding_sync_bitwarden_id': sync_id,
             'matrix_mas_postgres_credentials_bitwarden_id': mas_db_id,
             'matrix_authentication_service_bitwarden_id': mas_id,
             'matrix_sliding_sync_postgres_credentials_bitwarden_id': sync_db_id,
             'matrix_oidc_credentials_bitwarden_id': oidc_id['id'],
             'matrix_discord_bitwarden_id': discord_id,
             'matrix_alertmanager_bitwarden_id': alertmanager_id,
             'matrix_idp_name': idp_name,
             'matrix_idp_id': idp_id})


def setup_bitwarden_items(argocd: ArgoCD,
                          matrix_hostname: str,
                          matrix_namespace: str,
                          s3_endpoint: str,
                          s3_access_id: str,
                          s3_access_key: str,
                          s3_bucket: str,
                          backups_s3_user: str,
                          backups_s3_password: str,
                          restic_repo_pass: str,
                          mail_host: str,
                          mail_user: str,
                          mail_pass: str,
                          zitadel_hostname: str,
                          oidc_creds: str,
                          mas_provider_ulid: str,
                          mas_issuer: str,
                          mas_client_id: str,
                          mas_client_secret: str,
                          mas_admin_token: str,
                          syncv3_secret: str,
                          github_app_id: str,
                          github_webhook_secret: str,
                          github_client_id: str,
                          github_client_secret: str,
                          github_private_key: str,
                          bitwarden: BwCLI):
    """
    setup all the required secrets as items in bitwarden
    """
    sub_header("Creating matrix secrets in Bitwarden")

    # if trusted_key_servers:
    #     trusted_key_servers_id = bitwarden.create_login(
    #             name='matrix-trusted-key-servers',
    #             item_url=matrix_hostname,
    #             user="nousername",
    #             password=trusted_key_servers
    #             )
    # else:
    #     trusted_key_servers_id = "not applicable"

    # S3 credentials
    if "http" not in s3_endpoint:
        s3_endpoint = "https://" + s3_endpoint
    matrix_s3_endpoint_obj = create_custom_field("s3Endpoint", s3_endpoint)
    matrix_s3_host_obj = create_custom_field("s3Hostname",
                                             s3_endpoint.replace("https://", ""))
    matrix_s3_bucket_obj = create_custom_field("s3Bucket", s3_bucket)
    s3_id = bitwarden.create_login(
            name='matrix-user-s3-credentials',
            item_url=matrix_hostname,
            user=s3_access_id,
            password=s3_access_key,
            fields=[
                matrix_s3_endpoint_obj,
                matrix_s3_host_obj,
                matrix_s3_bucket_obj
                ]
            )

    pgsql_s3_key = create_password()
    s3_db_id = bitwarden.create_login(
            name='matrix-postgres-s3-credentials',
            item_url=matrix_hostname,
            user="matrix-postgres",
            password=pgsql_s3_key
            )

    admin_s3_key = create_password()
    s3_admin_id = bitwarden.create_login(
            name='matrix-admin-s3-credentials',
            item_url=matrix_hostname,
            user="matrix-root",
            password=admin_s3_key
            )

    # credentials for remote backups of the s3 PVC
    restic_repo_pass_obj = create_custom_field("resticRepoPassword", restic_repo_pass)
    s3_backups_id = bitwarden.create_login(
            name='matrix-backups-s3-credentials',
            item_url=matrix_hostname,
            user=backups_s3_user,
            password=backups_s3_password,
            fields=[restic_repo_pass_obj]
            )

    # postgresql credentials
    db_host_obj = create_custom_field("hostname",
                                      f"matrix-postgres-rw.{matrix_namespace}.svc")
    # the database name
    db_obj = create_custom_field("database", "matrix")
    db_id = bitwarden.create_login(
            name='matrix-pgsql-credentials',
            item_url=matrix_hostname,
            user='matrix',
            password="we-use-tls-instead-of-password-now",
            fields=[db_host_obj, db_obj]
            )

    # postgres matrix authentication service credentials
    mas_db_host_obj = create_custom_field("hostname",
                                          f"mas-postgres-rw.{matrix_namespace}.svc")
    mas_db_obj = create_custom_field("database", "mas")
    # MAS doesn't support TLS auth to databases yet
    mas_db_pw = create_password()
    mas_db_id = bitwarden.create_login(
            name='mas-pgsql-credentials',
            item_url=matrix_hostname,
            user='mas',
            password=mas_db_pw,
            fields=[mas_db_host_obj, mas_db_obj]
            )

    # postgres sliding sync connection string
    conn_str = ("user=syncv3 dbname=syncv3 "
                f"host=syncv3-postgres-rw.{matrix_namespace}.svc sslmode=require "
                "sslkey=/etc/secrets/syncv3/tls.key "
                "sslcert=/etc/secrets/syncv3/tls.crt "
                "sslrootcert=/etc/secrets/ca/ca.crt")
    sync_db_id = bitwarden.create_login(
            name='syncv3-pgsql-credentials',
            item_url=matrix_hostname,
            user='syncv3',
            password=conn_str,
            )

    # SMTP credentials
    matrix_smtp_host_obj = create_custom_field("smtpHostname", mail_host)
    smtp_id = bitwarden.create_login(
            name='matrix-smtp-credentials',
            item_url=matrix_hostname,
            user=mail_user,
            password=mail_pass,
            fields=[matrix_smtp_host_obj]
            )

    # registration key
    matrix_registration_key = bitwarden.generate()
    reg_id = bitwarden.create_login(
            name='matrix-registration-key',
            item_url=matrix_hostname,
            user="admin",
            password=matrix_registration_key
            )

    # alert manager bot as_token + hs_token
    alertmanager_as_token = bitwarden.generate()
    alertmanager_as_token_obj = create_custom_field("as_token", alertmanager_as_token)
    alertmanager_hs_token = bitwarden.generate()
    alertmanager_hs_token_obj = create_custom_field("hs_token", alertmanager_hs_token)
    alertmanager_id = bitwarden.create_login(
            name='matrix-alertmanager-bridge',
            item_url=matrix_hostname,
            user="none",
            fields=[alertmanager_as_token_obj, alertmanager_hs_token_obj]
            )

    # discord bot as_token + hs_token
    discord_as_token = bitwarden.generate()
    discord_as_token_obj = create_custom_field("as_token", discord_as_token)
    discord_hs_token = bitwarden.generate()
    discord_hs_token_obj = create_custom_field("hs_token", discord_hs_token)
    discord_id = bitwarden.create_login(
            name='matrix-discord-bridge',
            item_url=matrix_hostname,
            user="none",
            fields=[discord_as_token_obj, discord_hs_token_obj]
            )

    # matrix sliding sync
    sync_id = bitwarden.create_login(
            name='matrix-syncv3-credentials',
            item_url=matrix_hostname,
            user="syncv3",
            password=syncv3_secret
            )

    # OIDC credentials
    log.info("Creating OIDC credentials for Matrix in Bitwarden")
    if zitadel_hostname:
        idp_id = "zitadel"
        idp_name = "Zitadel Auth"
        issuer_url = "https://" + zitadel_hostname

        if oidc_creds:
            issuer_obj = create_custom_field("issuer", issuer_url)
            idp_id_obj = create_custom_field("idp_id", idp_id)
            idp_name_obj = create_custom_field("idp_name", idp_name)

            # for the credentials to zitadel
            oidc_id = bitwarden.create_login(
                    name='matrix-oidc-credentials',
                    item_url=matrix_hostname,
                    user=oidc_creds['client_id'],
                    password=oidc_creds['client_secret'],
                    fields=[issuer_obj, idp_id_obj, idp_name_obj]
                    )

            # for credentials b/w matrix authentication service and synapse (matrix homeserver)
            mas_token_obj = create_custom_field("admin_token", mas_admin_token)
            acct_url_obj = create_custom_field("account_management_url", issuer_url)
            issuer_obj = create_custom_field("issuer", mas_issuer)
            provider_ulid_obj = create_custom_field("provider_id", mas_provider_ulid)
            mas_id = bitwarden.create_login(
                    name='matrix-authentication-service-credentials',
                    item_url=matrix_hostname,
                    user=mas_client_id,
                    password=mas_client_secret,
                    fields=[issuer_obj, mas_token_obj, acct_url_obj, provider_ulid_obj]
                    )
        else:
            # we assume the credentials already exist if they fail to create
            oidc_id = bitwarden.get_item(
                    f"matrix-oidc-credentials-{matrix_hostname}"
                    )[0]['id']
            mas_id = bitwarden.get_item(
                    f"matrix-authentication-service-credentials-{matrix_hostname}"
                    )[0]['id']

    # update the matrix values for the argocd appset
    # 'matrix_trusted_key_servers_bitwarden_id': trusted_key_servers_id}
    argocd.update_appset_secret(
            {'matrix_registration_credentials_bitwarden_id': reg_id,
             'matrix_smtp_credentials_bitwarden_id': smtp_id,
             'matrix_s3_admin_credentials_bitwarden_id': s3_admin_id,
             'matrix_s3_postgres_credentials_bitwarden_id': s3_db_id,
             'matrix_s3_matrix_credentials_bitwarden_id': s3_id,
             'matrix_s3_backups_credentials_bitwarden_id': s3_backups_id,
             'matrix_postgres_credentials_bitwarden_id': db_id,
             'matrix_sliding_sync_bitwarden_id': sync_id,
             'matrix_mas_postgres_credentials_bitwarden_id': mas_db_id,
             'matrix_sliding_sync_postgres_credentials_bitwarden_id': sync_db_id,
             'matrix_oidc_credentials_bitwarden_id': oidc_id,
             'matrix_authentication_service_bitwarden_id': mas_id,
             'matrix_alertmanager_bitwarden_id': alertmanager_id,
             'matrix_discord_bitwarden_id': discord_id,
             'matrix_idp_name': idp_name,
             'matrix_idp_id': idp_id}
            )

    # reload the bitwarden ESO provider
    try:
        argocd.k8s.reload_deployment('bitwarden-eso-provider',
                                     'external-secrets')
    except Exception as e:
        log.error(
                "Couldn't scale down the [magenta]bitwarden-eso-provider[/]"
                "deployment in [green]external-secrets[/] namespace. Recieved: "
                f"{e}"
                )


def restore_matrix(argocd: ArgoCD,
                   matrix_hostname: str,
                   matrix_namespace: str,
                   argo_dict: dict,
                   secrets: dict,
                   restore_dict: dict,
                   backup_dict: dict,
                   pvc_storage_class: str,
                   pgsql_cluster_name: str,
                   bitwarden: BwCLI) -> None:
    """
    restore matrix seaweedfs PVCs, matrix files and/or config PVC(s),
    and CNPG postgresql cluster
    """
    # this is the info for the REMOTE backups
    s3_backup_endpoint = backup_dict['endpoint']
    s3_backup_bucket = backup_dict['bucket']
    access_key_id = backup_dict["s3_user"]
    secret_access_key = backup_dict["s3_password"]
    restic_repo_password = backup_dict['restic_repo_pass']
    cnpg_backup_schedule = backup_dict['postgres_schedule']

    # get argocd git repo info
    revision = argo_dict['revision']
    argo_path = argo_dict['path']

    # first we grab existing bitwarden items if they exist
    if bitwarden:
        refresh_bweso(argocd, matrix_hostname, bitwarden)

        # apply the external secrets so we can immediately use them for restores
        external_secrets_yaml = (
                "https://raw.githubusercontent.com/small-hack/argocd-apps"
                f"/{revision}/{argo_path}/external_secrets_argocd_appset.yaml"
                )
        argocd.k8s.apply_manifests(external_secrets_yaml, argocd.namespace)

        # postgresql s3 ID
        s3_db_creds = bitwarden.get_item(
                f"matrix-postgres-s3-credentials-{matrix_hostname}", False
                )[0]['login']

        pg_access_key_id = s3_db_creds["username"]
        pg_secret_access_key = s3_db_creds["password"]

    # these are the remote backups for seaweedfs
    s3_pvc_capacity = secrets['s3_pvc_capacity']

    # then we create all the seaweedfs pvcs we lost and restore them
    snapshot_ids = restore_dict['restic_snapshot_ids']
    restore_seaweedfs(
            argocd,
            'matrix',
            matrix_namespace,
            revision,
            argo_path,
            s3_backup_endpoint,
            s3_backup_bucket,
            access_key_id,
            secret_access_key,
            restic_repo_password,
            s3_pvc_capacity,
            pvc_storage_class,
            "ReadWriteOnce",
            snapshot_ids['seaweedfs_volume'],
            snapshot_ids['seaweedfs_filer']
            )

    # then we finally can restore the postgres database :D
    if restore_dict.get("cnpg_restore", False):
        psql_version = restore_dict.get("postgresql_version", 16)
        s3_endpoint = secrets.get('s3_endpoint', "")
        restore_cnpg_cluster(argocd.k8s,
                             'matrix',
                             matrix_namespace,
                             pgsql_cluster_name,
                             psql_version,
                             s3_endpoint,
                             pg_access_key_id,
                             pg_secret_access_key,
                             pgsql_cluster_name,
                             cnpg_backup_schedule)

    # then we begin the restic restore of all the matrix PVCs we lost
    for pvc in ['media', 'synapse_config', 'signing_key']:
        pvc_enabled = secrets.get(f'{pvc}_pvc_enabled', 'false')
        if pvc_enabled and pvc_enabled.lower() != 'false':
            pvc_name = "matrix-" + pvc.replace("_","-")
            # creates the matrix pvc
            recreate_pvc(argocd.k8s,
                         'matrix',
                         pvc_name,
                         matrix_namespace,
                         secrets[f'{pvc}_storage'],
                         pvc_storage_class,
                         secrets[f'{pvc}_access_mode'],
                         "matrix-pvc")

            # restores the restic backup to this pvc
            k8up_restore_pvc(argocd.k8s,
                             'matrix',
                             pvc_name,
                             'matrix',
                             s3_backup_endpoint,
                             s3_backup_bucket,
                             access_key_id,
                             secret_access_key,
                             restic_repo_password,
                             snapshot_ids[f'matrix_{pvc}']
                             )
