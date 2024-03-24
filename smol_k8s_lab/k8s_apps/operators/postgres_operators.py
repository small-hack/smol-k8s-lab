# internal libraries
from smol_k8s_lab.bitwarden.bw_cli import BwCLI
from smol_k8s_lab.k8s_tools.argocd_util import (install_with_argocd,
                                                update_argocd_appset_secret,
                                                sync_argocd_app,
                                                check_if_argocd_app_exists)
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.utils.passwords import create_password

# external libraries
import logging as log


def configure_cnpg_operator(k8s_obj: K8s, config: dict) -> None:
    """
    setup the CNPG operator as an Argo CD Application
    """
    # check if minio is using smol_k8s_lab init and if already present in Argo CD
    if not check_if_argocd_app_exists('cnpg-operator'):
        # actual installation of the minio app
        install_with_argocd(k8s_obj,
                            'cnpg-operator',
                            config['argo'])


def configure_postgres_operator(k8s_obj: K8s,
                                config: dict,
                                bw: BwCLI = None) -> None:
    """
    setup the zalando postgres operator as an Argo CD Application
    """
    # get hostname and if init is enabled
    init_enabled = config['init']['enabled']
    hostname = config['argo']['secret_keys']['hostname']

    # check if minio is using smol_k8s_lab init and if already present in Argo CD
    if not check_if_argocd_app_exists('postgres-operator'):
        if init_enabled:
            access_id = config['init']['values']['s3_backup_access_id']
            secret_key = config['init']['values']['s3_backup_secret_key']
            if bw:
                # s3 credentials for zalando postgres operator access
                pgsql_s3_pass = create_password()
                s3_id = bw.create_login(
                        name='postgres-operator-s3-credentials',
                        item_url=hostname,
                        user="postgres-operator",
                        password=pgsql_s3_pass
                        )

                # s3 credentials for admin access to e.g. seaweedfs
                pgsql_s3_admin_pass = create_password()
                s3_admin_id = bw.create_login(
                        name='postgres-operator-admin-s3-credentials',
                        item_url=hostname,
                        user='postgres-operator-root',
                        password=pgsql_s3_admin_pass
                        )

                # s3 credentials for *remote* backups e.g. b2
                s3_backups_id = bw.create_login(
                        name='postgres-operator-backups-s3-credentials',
                        item_url=hostname,
                        user=access_id,
                        password=secret_key
                        )

                # update the postgres_operator values for the argocd appset
                update_argocd_appset_secret(
                        k8s_obj,
                        {'postgres_operator_s3_admin_credentials_bitwarden_id': s3_admin_id,
                         'postgres_operator_s3_user_credentials_bitwarden_id': s3_id,
                         'postgres_operator_s3_backups_credentials_bitwarden_id': s3_backups_id}
                        )

        # actual installation of the minio app
        install_with_argocd(k8s_obj,
                            'postgres-operator',
                            config['argo'])
    else:
        if bw and init_enabled:
            log.debug("Making sure postgres_operator Bitwarden item IDs are in "
                      "appset secret plugin secret")

            s3_admin_id = bw.get_item(
                    f"postgres-operator-admin-s3-credentials-{hostname}"
                    )[0]['id']

            s3_id = bw.get_item(
                    f"postgres-operator-user-s3-credentials-{hostname}", False
                    )[0]['id']

            s3_backups_id = bw.get_item(
                    f"postgres-operator-backups-s3-credentials-{hostname}", False
                    )[0]['id']

            update_argocd_appset_secret(
                    k8s_obj,
                    {'postgres_operator_s3_admin_credentials_bitwarden_id': s3_admin_id,
                     'postgres_operator_s3_user_credentials_bitwarden_id': s3_id,
                     'postgres_operator_s3_backups_credentials_bitwarden_id': s3_backups_id
                    })

        sync_argocd_app('postgres-operator')
