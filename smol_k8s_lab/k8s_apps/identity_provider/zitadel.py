from base64 import standard_b64decode as b64dec
from json import loads
import logging as log
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_apps.identity_provider.zitadel_api import Zitadel
from smol_k8s_lab.k8s_apps.operators.minio import create_minio_alias
from smol_k8s_lab.k8s_tools.argocd_util import ArgoCD
from smol_k8s_lab.k8s_tools.restores import restore_seaweedfs, restore_cnpg_cluster
from smol_k8s_lab.utils.value_from import process_backup_vals, extract_secret
from smol_k8s_lab.utils.passwords import create_password
from smol_k8s_lab.utils.rich_cli.console_logging import sub_header, header


def configure_zitadel(argocd: ArgoCD,
                      cfg: dict,
                      pvc_storage_class: str = "",
                      api_tls_verify: bool = False,
                      bitwarden: BwCLI = None) -> dict | None:
    """
    Installs zitadel as a Argo CD Applications. If cfg['init']['enabled']
    is True, it also configures Argo CD as OIDC Clients.

    Required Arguments:
        argocd:             ArgoCD obj for doing Argo operations
        cfg:                dict, Argo CD parameters for zitadel
        pvc_storage_class:  str, storage class of PVC

    Optional Arguments:
        api_tls_verify:    bool, enable https verification for zitadel api
        bitwarden:         BwCLI obj, [optional] contains bitwarden session

    If no init: Returns True if successful.
    If init AND vouch_hostname, returns vouch credentials
    """
    # check to make sure the app instead already installed with Argo CD
    app_installed = argocd.check_if_app_exists('zitadel')

    # declare the init dict
    init_dict = cfg.get('init', {'enabled': False, 'restore': {'enabled': False}})
    init_enabled = init_dict['enabled']

    # immediately load in all the secret keys
    secrets = cfg['argo']['secret_keys']
    if secrets:
        zitadel_hostname = secrets['hostname']

    restore_dict = cfg['init'].get('restore', {"enabled": False})
    restore_enabled = restore_dict['enabled']
    if restore_enabled:
        prefix = "Restoring"
    else:
        if app_installed:
            prefix = "Syncing"
        else:
            prefix = "Setting up"

    zitadel_namespace = cfg['argo']['namespace']

    header(f"{prefix} [green]Zitadel[/], for your self hosted identity management",
           "👥")

    if init_enabled:
        # configure backup s3 credentials
        backup_vals = process_backup_vals(cfg.get('backups', ''), 'zitadel', argocd)

    if init_enabled and not app_installed:
        # process init and secret values
        init_values = init_dict['values']


        s3_endpoint = secrets.get('s3_endpoint', "")
        if s3_endpoint and not restore_enabled:
            s3_access_key = create_password()
            # create a local alias to check and make sure nextcloud is functional
            create_minio_alias(minio_alias="zitadel",
                               minio_hostname=s3_endpoint,
                               access_key="zitadel",
                               secret_key=s3_access_key)

        # first we make sure the namespace exists
        argocd.k8s.create_namespace(zitadel_namespace)

        # get the mail credentials
        smtp_host = extract_secret(init_values.pop("smtp_host",
                                                   "not applicable"))
        smtp_user = extract_secret(init_values.pop("smtp_user",
                                                   "not applicable"))
        smtp_password = extract_secret(init_values.pop("smtp_password",
                                                       "not applicable"))
        smtp_from_address = extract_secret(init_values.pop("smtp_from_address",
                                                           "not applicable"))
        smtp_from_name = extract_secret(init_values.pop("smtp_from_name",
                                                        "not applicable"))
        smtp_reply_to_address = extract_secret(
                init_values.pop("smtp_reply_to_address",
                                "not applicable")
                )

        if bitwarden and not restore_enabled:
            setup_bitwarden_items(argocd,
                                  zitadel_hostname,
                                  s3_endpoint,
                                  s3_access_key,
                                  backup_vals['s3_user'],
                                  backup_vals['s3_password'],
                                  backup_vals['restic_repo_pass'],
                                  smtp_host,
                                  smtp_user,
                                  smtp_password,
                                  smtp_from_address,
                                  smtp_from_name,
                                  smtp_reply_to_address,
                                  bitwarden)

        elif not bitwarden and not restore_enabled:
            # create the zitadel core key
            secret_dict = {'masterkey': create_password()}
            argocd.k8s.create_secret(name="zitadel-core-key",
                                     namespace=zitadel_namespace,
                                     str_data=secret_dict)

            # this is just for the db username
            argocd.k8s.create_secret(name="zitadel-db-credentials",
                                     namespace=zitadel_namespace,
                                     str_data={'username': 'zitadel'})

            # postgres db credentials creation
            argocd.k8s.create_secret('zitadel-pgsql-credentials', 'zitadel',
                                     {"username": 'zitadel',
                                      "password": 'we-use-tls-instead-of-password'})

            # smtp credentials creation
            argocd.k8s.create_secret('zitadel-smtp-credentials', 'zitadel',
                                     {"host": smtp_host,
                                      "user": smtp_user,
                                      "password": smtp_password,
                                      "from_address": smtp_from_address,
                                      "from_name": smtp_from_name,
                                      "reply_to_address": smtp_reply_to_address})

    if not app_installed and restore_enabled:
        restore_zitadel(argocd,
                        zitadel_hostname,
                        zitadel_namespace,
                        cfg['argo'],
                        secrets,
                        restore_dict,
                        backup_vals,
                        pvc_storage_class,
                        'zitadel-postgres',
                        bitwarden)

    # install Zitadel using ArgoCD
    argocd.install_app('zitadel', cfg['argo'])

    # only continue through the rest of the function if we're initializes a
    # user and argocd client in zitadel
    if not app_installed and init_enabled and not restore_enabled:
        initial_user_dict = init_values
        # don't need the smtp password past this point
        try:
            initial_user_dict.pop('smtp_password')
        except Exception as e:
            log.debug(e)
            pass

        # Before initialization, we need to wait for zitadel's API to be up
        argocd.wait_for_app('zitadel', retry=True)
        argocd.wait_for_app('zitadel-web-app', retry=True)

        vouch_dict = initialize_zitadel(argocd,
                                        zitadel_hostname=zitadel_hostname,
                                        zitadel_namespace=zitadel_namespace,
                                        api_tls_verify=api_tls_verify,
                                        user_dict=initial_user_dict,
                                        bitwarden=bitwarden)
        return vouch_dict
    else:
        log.info("Zitadel is already installed 🎉")

        if bitwarden and init_enabled:
            # get the zitadel service account private key json for generating a jwt
            private_key_dict = get_zitadel_admin_service_account(
                    argocd.k8s,
                    zitadel_hostname,
                    zitadel_namespace,
                    bitwarden)

            # setup and return the zitadel python api wrapper
            zitadel = Zitadel(
                    zitadel_hostname,
                    private_key_dict,
                    api_tls_verify
                    )
            try:
                zitadel.set_user_by_login_name(
                        cfg['init']['values']['admin_user']
                        )
            except Exception as e:
                log.error(e)

            try:
                zitadel.set_project_by_name(
                        cfg['init']['values']['project']
                        )
            except Exception as e:
                log.error(e)
                raise Exception(e)

            refresh_bitwarden(argocd, zitadel_hostname, bitwarden)

            # argocd.sync_app('argo-cd')

            return zitadel


def get_zitadel_admin_service_account(k8s_obj,
                                      zitadel_hostname: str,
                                      zitadel_namespace: str = "zitadel",
                                      bitwarden: BwCLI = None) -> dict | None:
    """
    Try to get the zitadel admin service account from k8s secret or bitwarden.
    If it finds the admin service account secret, it returns a dict like:
    {"keyId": "", "key": "", "userId": ""}
    """
    # get the zitadel service account private key json for generating a jwt
    try:
        # first, we try to get private key from a k8s secret in the zitadel ns
        adm_secret = k8s_obj.get_secret('zitadel-admin-sa', zitadel_namespace)
        adm_secret_file = adm_secret['data']['zitadel-admin-sa.json']
        private_key_dict = loads(b64dec(str.encode(adm_secret_file)).decode('utf8'))
    except Exception as e:
        # if that fails, then we try to get the key from bitwarden
        log.warn(f"Encountered error while getting secret: {e}")
        if bitwarden:
            log.info("Trying to get admin service account secret from bitwarden.")
            adm_secret = bitwarden.get_item(
                    f"zitadel-admin-service-account-{zitadel_hostname}"
                    )[0]
            private_key_dict = {"keyId": adm_secret['fields'][0]['value'],
                                "key": adm_secret['login']['password'],
                                "userId": adm_secret['login']['username']}
        else:
            return None
    else:
        # if we find the key in a k8s secret, we try to put into bitwarden, so
        # that if the whole namespace is blown away, we still have access to it
        key_id_field = create_custom_field("keyId", private_key_dict['keyId'])
        bitwarden.create_login(
            name='zitadel-admin-service-account',
            item_url=zitadel_hostname,
            user=private_key_dict['userId'],
            password=private_key_dict['key'],
            fields=[key_id_field]
            )

    return private_key_dict


def initialize_zitadel(argocd: ArgoCD,
                       zitadel_hostname: str,
                       zitadel_namespace: str = "zitadel",
                       api_tls_verify: bool = False,
                       user_dict: dict = {},
                       bitwarden: BwCLI = None) -> dict | None:
    """
    Sets up initial zitadel user, Argo CD client
    Arguments:
      zitadel_hostname:  str, the hostname of Zitadel
      api_tls_verify:    bool, whether or not to verify the TLS cert on request to api
      user_dict:         dict of initial admin_user, email, first name, last name
                         gender, and project to create
      argocd_hostname:   str, the hostname of Argo CD for oidc app
      bitwarden:         BwCLI obj, [optional] session to use for bitwarden

    returns Zitadel() with admin user/admin service account created with session token
    """
    k8s_obj = argocd.k8s
    argocd_hostname = argocd.hostname

    sub_header("Configuring zitadel as your OIDC SSO for Argo CD")
    private_key_dict = get_zitadel_admin_service_account(k8s_obj,
                                                         zitadel_hostname,
                                                         zitadel_namespace,
                                                         bitwarden)
    if not private_key_dict:
        log.error("No private key dict was recieved, can't initialize zitadel api")

    # setup the zitadel python api wrapper
    zitadel =  Zitadel(zitadel_hostname, private_key_dict, api_tls_verify)

    # create our first project
    project_name = user_dict.pop('project')
    zitadel.create_project(project_name)

    log.info("Creating a groups Zitadel Action (sends group info to Argo CD)")
    zitadel.create_groups_claim_action()

    # create Argo CD OIDC Application
    log.info("Creating an Argo CD application...")
    redirect_uris = f"https://{argocd_hostname}/auth/callback"
    logout_uris = [f"https://{argocd_hostname}"]
    argocd_client = zitadel.create_application("argocd",
                                               redirect_uris,
                                               logout_uris)

    # create roles for both Argo CD Admins and regular users
    zitadel.create_role("argocd_administrators", "Argo CD Administrators",
                        "argocd_administrators")
    zitadel.create_role("argocd_users", "Argo CD Users", "argocd_users")

    # fields for updating the appset secret
    fields = {
            'argo_cd_oidc_issuer': f"https://{zitadel_hostname}",
            'argo_cd_oidc_client_id': argocd_client['client_id'],
            'argo_cd_oidc_logout_url': f"https://{zitadel_hostname}/oidc/v1/end_session"
            }

    # if bitwarden is enabled, we store the argocd odic secret there
    if bitwarden:
        sub_header("Creating OIDC secret for Argo CD in Bitwarden")
        id = bitwarden.create_login(name='argocd-oidc-credentials',
                                    item_url=argocd_hostname,
                                    user=argocd_client['client_id'],
                                    password=argocd_client['client_secret'])
        fields['argo_cd_oidc_bitwarden_id'] = id
    else:
        # the argocd secret needs labels.app.kubernetes.io/part-of: "argocd"
        k8s_obj.create_secret('argocd-oidc-credentials',
                              'argocd',
                              {'user': argocd_client['client_id'],
                               'password': argocd_client['client_secret']},
                              labels={'app.kubernetes.io/part-of': 'argocd'})

    # create zitadel admin user that the project is setup
    header("Creating a Zitadel user...")
    user_id = zitadel.create_user(bitwarden=bitwarden, **user_dict)
    zitadel.set_user_by_login_name(user_dict['admin_user'])
    try:
        zitadel.create_user_grant(['argocd_administrators'])
    except Exception as e:
        log.error(e)
        zitadel.update_user_grant(['argocd_administrators'])

    # grant admin access to first user
    sub_header("creating user IAM membership with IAM_OWNER")
    zitadel.create_iam_membership(user_id, 'IAM_OWNER')

    # update appset-secret-vars secret with issuer, client_id, logout_url
    argocd.update_appset_secret(fields)

    return zitadel


def setup_bitwarden_items(argocd: ArgoCD,
                          zitadel_hostname: str,
                          s3_endpoint: str,
                          s3_access_key: str,
                          backups_s3_user: str,
                          backups_s3_password: str,
                          restic_repo_pass: str,
                          smtp_host: str,
                          smtp_user: str,
                          smtp_password: str,
                          smtp_from_address: str,
                          smtp_from_name: str,
                          smtp_reply_to_address: str,
                          bitwarden: BwCLI) -> None:
    """
    setup all zitadel related bitwarden items and refresh the appset secret plugin
    """
    restic_repo_obj = create_custom_field('resticRepoPassword', restic_repo_pass)
    s3_backup_id = bitwarden.create_login(
            name='zitadel-backups-s3-credentials',
            item_url=zitadel_hostname,
            user=backups_s3_user,
            password=backups_s3_password,
            fields=[restic_repo_obj]
            )

    # S3 credentials
    db_access_key = create_password()
    s3_id = bitwarden.create_login(
            name='zitadel-postgres-s3-credentials',
            item_url=zitadel_hostname,
            user="zitadel-postgres",
            password=db_access_key
            )

    admin_s3_key = create_password()
    s3_admin_id = bitwarden.create_login(
            name='zitadel-admin-s3-credentials',
            item_url=zitadel_hostname,
            user="zitadel-root",
            password=admin_s3_key
            )

    # postgres db credentials creation
    db_id = bitwarden.create_login(
            name='zitadel-pgsql-credentials',
            item_url=zitadel_hostname,
            user='zitadel',
            password="using-tls-now-so-we-do-not-need-a-password"
            )

    # zitadel smtp credentials creation
    smtp_host_obj = create_custom_field('host', smtp_host)
    smtp_from_address_obj = create_custom_field('from_address', smtp_from_address)
    smtp_from_name_obj = create_custom_field('from_name', smtp_from_name)
    smtp_reply_to_address_obj = create_custom_field('reply_to_address', smtp_reply_to_address)
    smtp_id = bitwarden.create_login(
            name='zitadel-smtp-credentials',
            item_url=zitadel_hostname,
            user=smtp_user,
            password=smtp_password,
            fields=[smtp_host_obj,
                    smtp_from_address_obj,
                    smtp_from_name_obj,
                    smtp_reply_to_address_obj]
            )

    # create zitadel core key
    new_key = bitwarden.generate()
    core_id = bitwarden.create_login(name="zitadel-core-key",
                                     user="admin-service-account",
                                     item_url=zitadel_hostname,
                                     password=new_key)

    # update the zitadel values for the argocd appset
    argocd.update_appset_secret(
            {'zitadel_core_bitwarden_id': core_id,
             'zitadel_smtp_credentials_bitwarden_id': smtp_id,
             'zitadel_postgres_credentials_bitwarden_id': db_id,
             'zitadel_s3_postgres_credentials_bitwarden_id': s3_id,
             'zitadel_s3_admin_credentials_bitwarden_id': s3_admin_id,
             'zitadel_s3_backups_credentials_bitwarden_id': s3_backup_id}
            )

    # reload the bitwarden ESO provider
    try:
        argocd.k8s.reload_deployment('bitwarden-eso-provider', 'external-secrets')
    except Exception as e:
        log.error(
                "Couldn't scale down the [magenta]bitwarden-eso-provider[/]"
                "deployment in [green]external-secrets[/] namespace. Recieved: "
                f"{e}"
                )


def refresh_bitwarden(argocd: ArgoCD,
                      zitadel_hostname: str,
                      bitwarden: BwCLI) -> None:
    """
    makes sure we update the appset secret with bitwarden IDs regardless
    """
    db_id = bitwarden.get_item(
            f"zitadel-pgsql-credentials-{zitadel_hostname}", False
            )[0]['id']

    s3_backup_id = bitwarden.get_item(
            f"zitadel-backups-s3-credentials-{zitadel_hostname}", False
            )[0]['id']

    s3_admin_id = bitwarden.get_item(
            f"zitadel-admin-s3-credentials-{zitadel_hostname}", False
            )[0]['id']

    s3_id = bitwarden.get_item(
            f"zitadel-postgres-s3-credentials-{zitadel_hostname}", False
            )[0]['id']

    try:
        smtp_id = bitwarden.get_item(
                f"zitadel-smtp-credentials-{zitadel_hostname}", False
                )[0]['id']
    except Exception as e:
        log.warn(e)
        smtp_id = "Not applicable"

    core_id = bitwarden.get_item(
            f"zitadel-core-key-{zitadel_hostname}", False
            )[0]['id']

    argo_oidc_item = bitwarden.get_item(
            f"argocd-oidc-credentials-{argocd.hostname}", False
            )[0]

    argo_client_id = argo_oidc_item['login']['username']

    # update the zitadel values for the argocd appset

    argocd.update_appset_secret(
            {
            'zitadel_core_bitwarden_id': core_id,
            'zitadel_smtp_credentials_bitwarden_id': smtp_id,
            'zitadel_postgres_credentials_bitwarden_id': db_id,
            'zitadel_s3_postgres_credentials_bitwarden_id': s3_id,
            'zitadel_s3_backups_credentials_bitwarden_id': s3_backup_id,
            'zitadel_s3_admin_credentials_bitwarden_id': s3_admin_id,
            'argo_cd_oidc_issuer': f"https://{zitadel_hostname}",
            'argo_cd_oidc_client_id': argo_client_id,
            'argo_cd_oidc_logout_url': f"https://{zitadel_hostname}/oidc/v1/end_session",
            'argo_cd_oidc_bitwarden_id': argo_oidc_item['id']
            }
            )


def restore_zitadel(argocd: ArgoCD,
                    zitadel_hostname: str,
                    zitadel_namespace: str,
                    argo_dict: dict,
                    secrets: dict,
                    restore_dict: dict,
                    backup_dict: dict,
                    pvc_storage_class: str,
                    pgsql_cluster_name: str,
                    bitwarden: BwCLI) -> None:
    """
    restore zitadel seaweedfs PVCs, zitadel files and/or config PVC(s),
    and CNPG postgresql cluster
    """
    # this is the info for the REMOTE backups
    s3_backup_endpoint = backup_dict['endpoint']
    s3_backup_bucket = backup_dict['bucket']
    access_key_id = backup_dict["s3_user"]
    secret_access_key = backup_dict["s3_password"]
    restic_repo_password = backup_dict['restic_repo_pass']
    cnpg_backup_schedule = backup_dict['postgres_schedule']

    # get where the current argo cd app is located in git
    revision = argo_dict["revision"]
    argo_path = argo_dict["path"]

    # first we grab existing bitwarden items if they exist
    if bitwarden:
        refresh_bitwarden(argocd, zitadel_hostname, bitwarden)

        # apply the external secrets so we can immediately use them for restores
        external_secrets_yaml = (
                "https://raw.githubusercontent.com/small-hack/argocd-apps/"
                f"{revision}/{argo_path}/external_secrets_argocd_appset.yaml"
                )
        argocd.k8s.apply_manifests(external_secrets_yaml, argocd.namespace)

        # postgresql s3 ID
        s3_db_creds = bitwarden.get_item(
                f"zitadel-postgres-s3-credentials-{zitadel_hostname}", False
                )[0]['login']

        pg_access_key_id = s3_db_creds["username"]
        pg_secret_access_key = s3_db_creds["password"]

    # these are the remote backups for seaweedfs
    s3_pvc_capacity = secrets['s3_pvc_capacity']

    # then we create all the seaweedfs pvcs we lost and restore them
    snapshot_ids = restore_dict['restic_snapshot_ids']
    restore_seaweedfs(
            argocd,
            'zitadel',
            zitadel_namespace,
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
                             'zitadel',
                             zitadel_namespace,
                             pgsql_cluster_name,
                             psql_version,
                             s3_endpoint,
                             pg_access_key_id,
                             pg_secret_access_key,
                             pgsql_cluster_name,
                             cnpg_backup_schedule)
