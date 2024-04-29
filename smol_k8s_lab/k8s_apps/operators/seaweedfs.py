import logging as log

from smol_k8s_lab.bitwarden.bw_cli import BwCLI
from smol_k8s_lab.k8s_apps.operators.minio import create_minio_alias
from smol_k8s_lab.k8s_tools.argocd_util import ArgoCD
from smol_k8s_lab.utils.passwords import create_password


def configure_seaweedfs(argocd: ArgoCD,
                        seaweedfs_config: dict,
                        bitwarden: BwCLI = None) -> None:
    """
    seaweedfs tenant installation and configuration

    if secure is set to True, we write a config with https:// prefixing the
    hostname, else we use http://

    if bitwarden obj:
        We'll store all your secrets in bitwarden

    if init is enabled we:
      - write a seaweedfs config file with alias called seaweedfs-root for use with mc cli
      - return a Betterseaweedfs object ready to create users, buckets, and policies
    """

    k8s_obj = argocd.k8s
    seaweedfs_init_enabled = seaweedfs_config['init']['enabled']
    argo_app_exists = argocd.check_if_app_exists('seaweedfs')

    secrets = seaweedfs_config['argo']['secret_keys']
    if secrets:
        seaweedfs_hostname = secrets.get('s3_endpoint', "")

    # if the app already exists and bitwarden is enabled return the credentials
    if seaweedfs_init_enabled and argo_app_exists:
        if bitwarden:
            res = bitwarden.get_item(
                    f'seaweedfs-admin-credentials-{seaweedfs_hostname}')
            access_key = seaweedfs_config['init']['values']['root_user']
            secret_key = res[0]['login']['password']
        # if app already exists but bitwarden is not enabled, return None
        return

    # if the user has enabled smol_k8s_lab init, we create an initial user
    if seaweedfs_init_enabled and not argo_app_exists:
        # the namespace probably doesn't exist yet, so we try to create it
        k8s_obj.create_namespace(seaweedfs_config['argo']['namespace'])
        access_key = "admin"
        secret_key = create_password(characters=72)

        if bitwarden:
            log.info("Creating seaweedfs admin credentials in Bitwarden")
            # admin credentials + metrics server info token
            s3_id = bitwarden.create_login(
                    name='seaweedfs-admin-credentials',
                    item_url=seaweedfs_hostname,
                    user=access_key,
                    password=secret_key
                    )
            # update the nextcloud values for the argocd appset
            argocd.update_appset_secret(
                    {'seaweedfs_s3_credentials_bitwarden_id': s3_id}
                    )

    if not argo_app_exists:
        # actual installation of the seaweedfs tenant Argo CD Application
        argocd.install_app('seaweedfs', seaweedfs_config['argo'], True)


        # while we wait for the app to come up, update the config file
        if seaweedfs_init_enabled:
            create_minio_alias("seaweedfs-root",
                               seaweedfs_hostname,
                               access_key,
                               secret_key)

        # if seaweedfs_init_enabled:
        #     # immediately create an admin and readonly policy
        #     seaweedfs_obj = BetterMinio('seaweedfs-root', seaweedfs_hostname,
        #                             access_key, secret_key)
        #     # so that zitadel groups names match up with seaweedfs policy names
        #     seaweedfs_obj.create_admin_group_policy()
        #     seaweedfs_obj.create_read_user_group_policy()
    else:
        # if the seaweedfs tenant Argo CD app already exists, but init is enabed...
        if bitwarden:
            creds = bitwarden.get_item(
                    f'seaweedfs-admin-credentials-{seaweedfs_hostname}'
                    )[0]

            # update the nextcloud values for the argocd appset
            argocd.update_appset_secret(
                    {'seaweedfs_s3_credentials_bitwarden_id': creds['id']}
                    )

        # if seaweedfs_init_enabled:
        #     access_key = creds['login']['username']
        #     secret_key = creds['login']['password']
        #     return BetterMinio('seaweedfs-root',
        #                        seaweedfs_hostname,
        #                        access_key,
        #                        secret_key)
