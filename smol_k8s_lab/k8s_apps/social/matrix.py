from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_apps.operators.minio import create_minio_alias
from smol_k8s_lab.k8s_apps.identity_provider.zitadel_api import Zitadel
from smol_k8s_lab.k8s_tools.argocd_util import (install_with_argocd,
                                                check_if_argocd_app_exists,
                                                update_argocd_appset_secret)
from smol_k8s_lab.k8s_tools.restores import (restore_seaweedfs,
                                             k8up_restore_pvc,
                                             restore_postgresql)
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.utils.rich_cli.console_logging import sub_header, header
from smol_k8s_lab.utils.passwords import create_password

import logging as log


def configure_matrix(k8s_obj: K8s,
                     config_dict: dict,
                     argocd_namespace: str,
                     pvc_storage_class: str,
                     zitadel: Zitadel,
                     bitwarden: BwCLI = None) -> bool:
    """
    creates a matrix app and initializes it with secrets if you'd like :)
    """

    app_installed = check_if_argocd_app_exists('matrix')
    secrets = config_dict['argo']['secret_keys']
    if secrets:
        matrix_hostname = secrets['hostname']

    init_enabled = config_dict['init']['enabled']
    # initial secrets to deploy this app from scratch
    if app_installed:
        header("Syncing [green]Matrix[/], so you can self host your own chat",
               '💬')
    elif init_enabled and not app_installed:
        init_values = config_dict['init']['values']

        restore_dict = config_dict['init'].get('restore', {"enabled": False})
        restore_enabled = restore_dict['enabled']
        if restore_enabled:
            header_start = "Restoring"
        else:
            header_start = "Setting up"

        header(f"{header_start} [green]Matrix[/], so you can self host your own chat",
               '💬')

        s3_endpoint = secrets.get('s3_endpoint', "")
        s3_bucket = secrets.get('s3_bucket', "matrix")
        # configure s3 credentials
        s3_access_id = 'matrix'
        s3_access_key = create_password()
        # credentials of remote backups of s3 PVCs
        restic_repo_pass = init_values.get('restic_repo_password', "")
        backups_s3_user = init_values.get('s3_backup_access_id', "")
        backups_s3_password = init_values.get('s3_backup_secret_key', "")

        # configure the smtp credentials
        mail_user = init_values['smtp_user']
        mail_pass = init_values['smtp_password']
        mail_host = init_values['smtp_host']

        # create a local alias to check and make sure matrix is functional
        create_minio_alias("matrix", s3_endpoint, "matrix", s3_access_key)

        # create Matrix OIDC Application
        if zitadel and not restore_enabled:
            log.debug("Creating a Matrix OIDC application in Zitadel...")
            redirect_uris = f"https://{matrix_hostname}/_synapse/client/oidc/callback"
            logout_uris = [f"https://{matrix_hostname}"]
            oidc_creds = zitadel.create_application("matrix",
                                                    redirect_uris,
                                                    logout_uris)
            zitadel.create_role("matrix_users", "Matrix Users", "matrix_users")
            zitadel.update_user_grant(['matrix_users'])
            zitadel_hostname = zitadel.hostname
        else:
            zitadel_hostname = ""

        # if the user has bitwarden enabled
        if bitwarden and not restore_enabled:
            matrix_namespace = config_dict['argo']['namespace']
            setup_bitwarden_items(matrix_hostname, matrix_namespace,
                                  s3_endpoint,
                                  s3_access_id, s3_access_key, s3_bucket,
                                  backups_s3_user, backups_s3_password,
                                  restic_repo_pass,
                                  mail_host, mail_user, mail_pass, oidc_creds,
                                  zitadel_hostname, k8s_obj, bitwarden)

        # else create these as Kubernetes secrets
        else:
            # postgresql credentials
            k8s_obj.create_secret(
                    'matrix-pgsql-credentials',
                    'matrix',
                    {"password": "we-use-tls-instead-of-password-now"}
                    )

            # registation key
            matrix_registration_key = create_password()
            k8s_obj.create_secret(
                    'matrix-registration',
                    'matrix',
                    {"registrationSharedSecret": matrix_registration_key}
                    )

            # oidc secret
            k8s_obj.create_secret(
                    'matrix-oidc-credentials',
                    'matrix',
                    {'user': oidc_creds['client_id'],
                     'password': oidc_creds['client_secret'],
                     'issuer': zitadel.hostname}
                    )

    if not app_installed:
        # if the user is restoring, the process is a little different
        if init_enabled and restore_enabled:
            restore_matrix(argocd_namespace,
                           matrix_hostname,
                           matrix_namespace,
                           config_dict,
                           secrets,
                           restore_dict,
                           pvc_storage_class,
                           k8s_obj,
                           bitwarden)

        install_with_argocd(k8s_obj, 'matrix', config_dict['argo'])
    else:
        if bitwarden and config_dict['init']['enabled']:
            refresh_bweso(matrix_hostname, k8s_obj, bitwarden)


def refresh_bweso(matrix_hostname, k8s_obj, bitwarden):
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

    # identity provider name and id are nested in the oidc item fields
    for field in oidc_id['fields']:
        if field['name'] == 'idp_id':
            idp_id = field['value']
        if field['name'] == 'idp_name':
            idp_name = field['value']

    update_argocd_appset_secret(
            k8s_obj,
            {'matrix_registration_credentials_bitwarden_id': reg_id,
             'matrix_smtp_credentials_bitwarden_id': smtp_id,
             'matrix_s3_admin_credentials_bitwarden_id': s3_admin_id,
             'matrix_s3_postgres_credentials_bitwarden_id': s3_db_id,
             'matrix_s3_matrix_credentials_bitwarden_id': s3_id,
             'matrix_s3_backups_credentials_bitwarden_id': s3_backups_id,
             'matrix_postgres_credentials_bitwarden_id': db_id,
             'matrix_oidc_credentials_bitwarden_id': oidc_id['id'],
             'matrix_idp_name': idp_name,
             'matrix_idp_id': idp_id})


def setup_bitwarden_items(matrix_hostname: str,
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
                          oidc_creds: str,
                          zitadel_hostname: str,
                          k8s_obj: str,
                          bitwarden):
    """
    setup all the required secrets as items in bitwarden
    """
    sub_header("Creating matrix secrets in Bitwarden")

    # S3 credentials
    if "http" not in s3_endpoint:
        s3_endpoint = "https://" + s3_endpoint
    matrix_s3_endpoint_obj = create_custom_field("s3Endpoint", s3_endpoint)
    matrix_s3_host_obj = create_custom_field("s3Hostname", s3_endpoint.replace("https://", ""))
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
    # matrix_pgsql_password = bitwarden.generate()
    db_hostname_obj = create_custom_field("hostname",
                                          f"matrix-postgres-rw.{matrix_namespace}.svc")
    # the database name
    db_obj = create_custom_field("database", "matrix")
    db_id = bitwarden.create_login(
            name='matrix-pgsql-credentials',
            item_url=matrix_hostname,
            user='matrix',
            password="we-use-tls-instead-of-password-now",
            fields=[db_hostname_obj, db_obj]
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

    # OIDC credentials
    log.info("Creating OIDC credentials for Matrix in Bitwarden")
    if zitadel_hostname:
        idp_id = "zitadel"
        idp_name = "Zitadel Auth"
        if oidc_creds:
            issuer_obj = create_custom_field("issuer", "https://" + zitadel_hostname)
            idp_id_obj = create_custom_field("idp_id", idp_id)
            idp_name_obj = create_custom_field("idp_name", idp_name)
            oidc_id = bitwarden.create_login(
                    name='matrix-oidc-credentials',
                    item_url=matrix_hostname,
                    user=oidc_creds['client_id'],
                    password=oidc_creds['client_secret'],
                    fields=[issuer_obj, idp_id_obj, idp_name_obj]
                    )
        else:
            # we assume the credentials already exist if they fail to create
            oidc_id = bitwarden.get_item(
                    f"matrix-oidc-credentials-{matrix_hostname}"
                    )[0]['id']

    # update the matrix values for the argocd appset
    update_argocd_appset_secret(
            k8s_obj,
            {'matrix_registration_credentials_bitwarden_id': reg_id,
             'matrix_smtp_credentials_bitwarden_id': smtp_id,
             'matrix_s3_admin_credentials_bitwarden_id': s3_admin_id,
             'matrix_s3_postgres_credentials_bitwarden_id': s3_db_id,
             'matrix_s3_matrix_credentials_bitwarden_id': s3_id,
             'matrix_s3_backups_credentials_bitwarden_id': s3_backups_id,
             'matrix_postgres_credentials_bitwarden_id': db_id,
             'matrix_oidc_credentials_bitwarden_id': oidc_id,
             'matrix_idp_name': idp_name,
             'matrix_idp_id': idp_id})

    # reload the bitwarden ESO provider
    try:
        k8s_obj.reload_deployment('bitwarden-eso-provider', 'external-secrets')
    except Exception as e:
        log.error(
                "Couldn't scale down the [magenta]bitwarden-eso-provider[/]"
                "deployment in [green]external-secrets[/] namespace. Recieved: "
                f"{e}"
                )


def restore_matrix(argocd_namespace: str,
                   matrix_hostname: str,
                   matrix_namespace: str,
                   config_dict: dict,
                   secrets: dict,
                   restore_dict: dict,
                   pvc_storage_class: str,
                   k8s_obj: K8s,
                   bitwarden: BwCLI,
                   pgsql_cluster_name: str = 'matrix-postgres') -> None:
    """
    restore matrix seaweedfs PVCs, matrix files and/or config PVC(s),
    and CNPG postgresql cluster
    """
    # first we grab existing bitwarden items if they exist
    if bitwarden:
        refresh_bweso(matrix_hostname, k8s_obj, bitwarden)

        # apply the external secrets so we can immediately use them for restores
        ref = "add-pvc-helm-chart-for-nextcloud"
        external_secrets_yaml = (
                "https://raw.githubusercontent.com/small-hack/argocd-apps"
                f"/{ref}/matrix/app_of_apps/external_secrets_appset.yaml"
                )
        k8s_obj.apply_manifests(external_secrets_yaml, argocd_namespace)

    # these are the remote backups for seaweedfs
    s3_backup_endpoint = secrets['s3_backup_endpoint']
    s3_backup_bucket = secrets['s3_backup_bucket']
    access_key_id = config_dict['init']['values']['s3_backup_access_id']
    secret_access_key = config_dict['init']['values']['s3_backup_secret_key']
    restic_repo_password = config_dict['init']['values']['restic_repo_password']
    s3_pvc_capacity = secrets['s3_pvc_capacity']

    # then we create all the seaweedfs pvcs we lost and restore them
    snapshot_ids = config_dict['init']['restore']['restic_snapshot_ids']
    restore_seaweedfs(
            k8s_obj,
            'matrix',
            matrix_namespace,
            s3_backup_endpoint,
            s3_backup_bucket,
            access_key_id,
            secret_access_key,
            restic_repo_password,
            s3_pvc_capacity,
            pvc_storage_class,
            snapshot_ids['seaweedfs_volume'],
            snapshot_ids['seaweedfs_master'],
            snapshot_ids['seaweedfs_filer']
            )

    # then we begin the restic restore of all the matrix PVCs we lost
    for pvc in ['media', 'synapse_config', 'signing_key']:
        pvc_enabled = secrets.get(f'{pvc}_pvc_enabled', 'false')
        if pvc_enabled and pvc_enabled.lower() != 'false':
            pvc_name = pvc.replace("_","-")
            pvc_dict = {
                    "kind": "PersistentVolumeClaim",
                    "apiVersion": "v1",
                    "metadata": {
                        "name": f"matrix-{pvc_name}",
                        "namespace": matrix_namespace,
                        "annotations": {"k8up.io/backup": "true"},
                        "labels": {
                            "argocd.argoproj.io/instance": "matrix-pvc"
                            }
                        },
                    "spec": {
                        "storageClassName": pvc_storage_class,
                        "accessModes": [secrets[f'{pvc}_access_mode']],
                        "resources": {
                            "requests": {
                                "storage": secrets[f'{pvc}_storage']}
                            }
                        }
                    }

            # creates the matrix files pvc
            k8s_obj.apply_custom_resources([pvc_dict])
            s3_endpoint = secrets.get('s3_endpoint', "")
            k8up_restore_pvc(k8s_obj,
                             'matrix',
                             f'matrix-{pvc}',
                             'matrix',
                             s3_backup_endpoint,
                             s3_backup_bucket,
                             access_key_id,
                             secret_access_key,
                             restic_repo_password,
                             snapshot_ids[f'matrix_{pvc}']
                             )

    # then we finally can restore the postgres database :D
    if restore_dict.get("cnpg_restore", False):
        psql_version = restore_dict.get("postgresql_version", 16)
        restore_postgresql('matrix',
                           matrix_namespace,
                           pgsql_cluster_name,
                           psql_version,
                           s3_endpoint,
                           pgsql_cluster_name)
