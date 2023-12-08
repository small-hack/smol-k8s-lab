# internal libraries
from smol_k8s_lab.k8s_apps.operators.minio import create_minio_alias
from smol_k8s_lab.k8s_apps.identity_provider.zitadel_api import Zitadel
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_tools.argocd_util import (install_with_argocd,
                                                check_if_argocd_app_exists,
                                                update_argocd_appset_secret)
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.utils.rich_cli.console_logging import sub_header, header
from smol_k8s_lab.utils.passwords import create_password

# external libraries
import logging as log


def configure_appflowy(k8s_obj: K8s,
                       config_dict: dict,
                       bitwarden: BwCLI = None,
                       zitadel: Zitadel = None) -> None:
    """
    creates a appflowy app and initializes it with secrets if you'd like :)

    required:
        k8s_obj     - K8s() object with cluster credentials
        config_dict - dictionary with at least argocd key and init key

    optional:
        bitwarden   - BwCLI() object with session token to create bitwarden items
        zitadel     - Zitadel() object with session token to create zitadel oidc app and roles
    """
    # check immediately if this app is installed
    app_installed = check_if_argocd_app_exists('appflowy')

    # get any secret keys passed in
    secrets = config_dict['argo']['secret_keys']
    if secrets:
        appflowy_hostname = secrets['hostname']

    # verify if initialization is enabled
    init_enabled = config_dict['init']['enabled']

    # if the user has chosen to use smol-k8s-lab initialization
    if not app_installed and init_enabled:
        k8s_obj.create_namespace(config_dict['argo']['namespace'])
        header("Setting up [green]appflowy[/], to self host your files",
               '🩵')

        # grab all possile init values
        init_values = config_dict['init'].get('values', None)
        if init_values:
            admin_email = init_values.get('admin_email', '')
            # credentials of remote backups of s3 PVCs
            restic_repo_pass = init_values.get('restic_repo_password', "")
            backups_s3_user = init_values.get('s3_backup_access_id', "")
            backups_s3_password = init_values.get('s3_backup_secret_key', "")

        if secrets:
            s3_endpoint = secrets.get('s3_endpoint', "")
            if s3_endpoint:
                s3_access_key = create_password()
                # create a local alias to check and make sure appflowy is functional
                create_minio_alias("appflowy", s3_endpoint, "appflowy", s3_access_key)

        # configure OIDC
        # if zitadel:
        #     log.debug("Creating a appflowy OIDC application in Zitadel...")
        #     redirect_uris = f"https://{appflowy_hostname}/apps/oidc_login/oidc"
        #     logout_uris = [f"https://{appflowy_hostname}"]
        #     oidc_creds = zitadel.create_application(
        #             "appflowy",
        #             redirect_uris,
        #             logout_uris
        #             )
        #     zitadel.create_role("appflowy_users", "appflowy Users", "appflowy_users")
        #     zitadel.create_role("appflowy_admins", "appflowy Admins", "appflowy_admins")
        #     zitadel.update_user_grant(['appflowy_admins'])

        # if bitwarden is enabled, we create login items for each set of credentials
        if bitwarden:
            sub_header("Creating appflowy items in Bitwarden")
            # gotrue credentials
            ext_url_obj = create_custom_field('extUrl', s3_endpoint)
            jwt_obj = create_custom_field('jwt', create_password())
            gotrue_id = bitwarden.create_login(
                    name='appflowy-gotrue-credentials',
                    item_url=appflowy_hostname,
                    user=admin_email,
                    password=create_password(),
                    fields=[ext_url_obj, jwt_obj]
                    )

            # s3 credentials creation
            endpoint_obj = create_custom_field('endpoint', s3_endpoint)
            region_obj = create_custom_field('region', "eu-west-1")
            bucket_obj = create_custom_field('bucket', "appflowy")
            s3_id = bitwarden.create_login(
                    name='appflowy-user-s3-credentials',
                    item_url=appflowy_hostname,
                    user="appflowy",
                    password=s3_access_key,
                    fields=[region_obj, bucket_obj, endpoint_obj]
                    )

            pgsql_s3_key = create_password()
            s3_db_id = bitwarden.create_login(
                    name='appflowy-postgres-s3-credentials',
                    item_url=appflowy_hostname,
                    user="appflowy-postgres",
                    password=pgsql_s3_key
                    )

            admin_s3_key = create_password()
            s3_admin_id = bitwarden.create_login(
                    name='appflowy-admin-s3-credentials',
                    item_url=appflowy_hostname,
                    user="appflowy-root",
                    password=admin_s3_key
                    )

            # credentials for remote backups of the s3 PVC
            restic_repo_pass_obj = create_custom_field("resticRepoPassword", restic_repo_pass)
            s3_backups_id = bitwarden.create_login(
                    name='appflowy-backups-s3-credentials',
                    item_url=appflowy_hostname,
                    user=backups_s3_user,
                    password=backups_s3_password,
                    fields=[restic_repo_pass_obj]
                    )

            # oidc credentials if they were given, else they're probably already there
            # if oidc_creds:
            #     log.debug("Creating OIDC credentials for appflowy in Bitwarden...")
            #     issuer_obj = create_custom_field("issuer", "https://" + zitadel.hostname)
            #     oidc_id = bitwarden.create_login(
            #             name='appflowy-oidc-credentials',
            #             item_url=appflowy_hostname,
            #             user=oidc_creds['client_id'],
            #             password=oidc_creds['client_secret'],
            #             fields=[issuer_obj]
            #             )
            # else:
            #     oidc_id = bitwarden.get_item(
            #             f"appflowy-oidc-credentials-{appflowy_hostname}"
            #             )[0]['id']

            # postgres db credentials creation
            db_id = bitwarden.create_login(
                    name='appflowy-pgsql-credentials',
                    item_url=appflowy_hostname,
                    user='appflowy',
                    password='we-dont-use-the-password-anymore-we-use-tls'
                    )

            # update the appflowy values for the argocd appset
            update_argocd_appset_secret(
                    k8s_obj,
                    {'appflowy_gotrue_bitwarden_id': gotrue_id,
                     'appflowy_postgres_credentials_bitwarden_id': db_id,
                     'appflowy_s3_admin_credentials_bitwarden_id': s3_admin_id,
                     'appflowy_s3_postgres_credentials_bitwarden_id': s3_db_id,
                     'appflowy_s3_appflowy_credentials_bitwarden_id': s3_id,
                     'appflowy_s3_backups_credentials_bitwarden_id': s3_backups_id}
                    )

        # these are standard k8s secrets
        else:
            # s3 credentials creation
            k8s_obj.create_secret('appflowy-s3-credentials', 'appflowy',
                                  {"S3_USER": "appflowy",
                                   "S3_PASSWORD": s3_access_key,
                                   "S3_ENDPOINT": s3_endpoint})

    if not app_installed:
        install_with_argocd(k8s_obj, 'appflowy', config_dict['argo'])
    else:
        log.info("appflowy already installed 🎉")

        # if bitwarden and init are enabled, make sure we populate appset secret
        # plugin secret with bitwarden item IDs
        if bitwarden and init_enabled:
            log.debug("Making sure appflowy Bitwarden item IDs are in appset "
                      "secret plugin secret")

            db_id = bitwarden.get_item(
                    f"appflowy-pgsql-credentials-{appflowy_hostname}"
                    )[0]['id']

            s3_admin_id = bitwarden.get_item(
                    f"appflowy-admin-s3-credentials-{appflowy_hostname}"
                    )[0]['id']

            s3_id = bitwarden.get_item(
                    f"appflowy-user-s3-credentials-{appflowy_hostname}"
                    )[0]['id']

            s3_backups_id = bitwarden.get_item(
                    f"appflowy-backups-s3-credentials-{appflowy_hostname}"
                    )[0]['id']

            s3_db_id = bitwarden.get_item(
                    f"appflowy-postgres-s3-credentials-{appflowy_hostname}"
                    )[0]['id']

            gotrue_id = bitwarden.get_item(
                    f"appflowy-gotrue-credentials-{appflowy_hostname}"
                    )[0]['id']

            update_argocd_appset_secret(
                    k8s_obj,
                    {'appflowy_gotrue_bitwarden_id': gotrue_id,
                     'appflowy_postgres_credentials_bitwarden_id': db_id,
                     'appflowy_s3_postgres_credentials_bitwarden_id': s3_db_id,
                     'appflowy_s3_admin_credentials_bitwarden_id': s3_admin_id,
                     'appflowy_s3_appflowy_credentials_bitwarden_id': s3_id,
                     'appflowy_s3_backups_credentials_bitwarden_id': s3_backups_id
                    })
