# internal libraries
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_apps.operators.minio import create_minio_alias, BetterMinio
from smol_k8s_lab.k8s_apps.social.mastodon_rake import generate_rake_secrets
from smol_k8s_lab.k8s_tools.argocd_util import (install_with_argocd,
                                                check_if_argocd_app_exists,
                                                wait_for_argocd_app,
                                                sync_argocd_app,
                                                update_argocd_appset_secret)
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.utils.passwords import create_password
from smol_k8s_lab.utils.rich_cli.console_logging import sub_header, header
from smol_k8s_lab.utils.subproc import subproc

# external libraries
import logging as log


def configure_mastodon(k8s_obj: K8s,
                       config_dict: dict,
                       bitwarden: BwCLI = None,
                       minio_obj: BetterMinio = {}) -> bool:
    """
    creates a mastodon app and initializes it with secrets if you'd like :)
    """
    header("Setting up [green]Mastodon[/], so you can self host your social media"
           '🐘')
    app_installed = check_if_argocd_app_exists('mastodon')
    init_enabled = config_dict['init']['enabled']
    secrets = config_dict['argo']['secret_keys']
    if secrets:
        mastodon_hostname = secrets['hostname']

    if init_enabled and not app_installed:
        k8s_obj.create_namespace('mastodon')

        # declare custom values for mastodon
        init_values = config_dict['init']['values']

        # configure the admin user credentials
        mastodon_admin_username = init_values['admin_user']
        mastodon_admin_email = init_values['admin_email']

        # configure the smtp credentials
        smtp_user = init_values['smtp_user']
        smtp_pass = init_values['smtp_password']
        smtp_host = init_values['smtp_host']

        s3_endpoint = secrets.get('s3_endpoint', "")
        log.debug(f"Mastodon s3_endpoint at the start is: {s3_endpoint}")
        # configure s3 credentials
        s3_access_id = 'mastodon'
        s3_access_key = create_password()
        # credentials of remote backups of s3 PVCs
        restic_repo_pass = init_values.get('restic_repo_password', "")
        backups_s3_user = init_values.get('s3_backup_access_id', "")
        backups_s3_password = init_values.get('s3_backup_secret_key', "")

        # main mastodon rake secrets
        rake_secrets = generate_rake_secrets()

        # create a local alias to check and make sure mastodon is functional
        create_minio_alias("mastodon", s3_endpoint, "mastodon", s3_access_key)

        if bitwarden:
            # S3 credentials
            # endpoint that gets put into the secret should probably have http in it
            if "http" not in s3_endpoint:
                log.debug(f"Mastodon s3_endpoint did not have http in it: {s3_endpoint}")
                s3_endpoint = "https://" + s3_endpoint
                log.debug(f"Mastodon s3_endpoint - after prepending 'https://': {s3_endpoint}")
            mastodon_s3_endpoint_obj = create_custom_field("s3Endpoint", s3_endpoint)
            mastodon_s3_host_obj = create_custom_field("s3Hostname", s3_endpoint.replace("https://", ""))
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

            # Redis credentials
            mastodon_redis_password = bitwarden.generate()
            redis_id = bitwarden.create_login(
                    name='mastodon-redis-credentials',
                    item_url=mastodon_hostname,
                    user='mastodon',
                    password=mastodon_redis_password
                    )

            # SMTP credentials
            mastodon_smtp_host_obj = create_custom_field("smtpHostname", smtp_host)
            smtp_id = bitwarden.create_login(
                    name='mastodon-smtp-credentials',
                    item_url=mastodon_hostname,
                    user=smtp_user,
                    password=smtp_pass,
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

            secrets_id = bitwarden.create_login(
                    name='mastodon-server-secrets',
                    item_url=mastodon_hostname,
                    user="mastodon",
                    password="none",
                    fields=[
                        secret_key_base_obj,
                        otp_secret_obj,
                        vapid_priv_key_obj,
                        vapid_pub_key_obj
                        ]
                    )
            
            # update the mastodon values for the argocd appset
            # 'mastodon_admin_credentials_bitwarden_id': admin_id,
            update_argocd_appset_secret(
                    k8s_obj,
                    {'mastodon_smtp_credentials_bitwarden_id': smtp_id,
                     'mastodon_postgres_credentials_bitwarden_id': db_id,
                     'mastodon_redis_bitwarden_id': redis_id,
                     'mastodon_s3_admin_credentials_bitwarden_id': s3_admin_id,
                     'mastodon_s3_postgres_credentials_bitwarden_id': s3_db_id,
                     'mastodon_s3_mastodon_credentials_bitwarden_id': s3_id,
                     'mastodon_s3_backups_credentials_bitwarden_id': s3_backups_id,
                     'mastodon_elasticsearch_credentials_bitwarden_id': elastic_id,
                     'mastodon_server_secrets_bitwarden_id': secrets_id})

            # reload the bitwarden ESO provider
            try:
                k8s_obj.reload_deployment('bitwarden-eso-provider', 'external-secrets')
            except Exception as e:
                log.error(
                        "Couldn't scale down the [magenta]bitwarden-eso-provider"
                        "[/] deployment in [green]external-secrets[/] namespace."
                        f"Recieved: {e}"
                        )

        # these are standard k8s secrets yaml
        else:
            # admin creds k8s secret
            # k8s_obj.create_secret('mastodon-admin-credentials', 'mastodon',
            #               {"username": username,
            #                "email": email})

            # postgres creds k8s secret
            mastodon_pgsql_password = create_password()
            k8s_obj.create_secret('mastodon-pgsql-credentials', 'mastodon',
                          {"password": mastodon_pgsql_password,
                           'postrgesPassword': mastodon_pgsql_password})

            # redis creds k8s secret
            mastodon_redis_password = create_password()
            k8s_obj.create_secret('mastodon-redis-credentials', 'mastodon',
                                  {"password": mastodon_redis_password})

            # mastodon rake secrets
            k8s_obj.create_secret('mastodon-server-secrets', 'mastodon',
                                  rake_secrets)

    if not app_installed:
        install_with_argocd(k8s_obj=k8s_obj,
                            app='mastodon',
                            argo_dict=config_dict['argo']
                            )
        if init_enabled:
            # for for all the mastodon apps to come up
            wait_for_argocd_app('mastodon')
            sync_argocd_app('mastodon-web-app')
            wait_for_argocd_app('mastodon-web-app')

            # create admin credentials
            password = create_user(mastodon_admin_username,
                                   mastodon_admin_email,
                                   config_dict['argo']['namespace'])
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

        # if mastodon already installed, but bitwarden and init are enabled
        # still populate the bitwarden IDs in the appset secret plugin secret
        if bitwarden and config_dict['init']['enabled']:
            log.debug("Making sure mastodon Bitwarden item IDs are in appset "
                      "secret plugin secret")

            # admin_id = bitwarden.get_item(
            #         f"mastodon-admin-credentials-{mastodon_hostname}"
            #         )[0]['id']

            db_id = bitwarden.get_item(
                    f"mastodon-pgsql-credentials-{mastodon_hostname}"
                    )[0]['id']

            elastic_id = bitwarden.get_item(
                    f"mastodon-elasticsearch-credentials-{mastodon_hostname}"
                    )[0]['id']

            redis_id = bitwarden.get_item(
                    f"mastodon-redis-credentials-{mastodon_hostname}"
                    )[0]['id']

            smtp_id = bitwarden.get_item(
                    f"mastodon-smtp-credentials-{mastodon_hostname}"
                    )[0]['id']

            s3_admin_id = bitwarden.get_item(
                    f"mastodon-admin-s3-credentials-{mastodon_hostname}"
                    )[0]['id']

            s3_db_id = bitwarden.get_item(
                    f"mastodon-postgres-s3-credentials-{mastodon_hostname}"
                    )[0]['id']

            s3_id = bitwarden.get_item(
                    f"mastodon-user-s3-credentials-{mastodon_hostname}"
                    )[0]['id']

            s3_backups_id = bitwarden.get_item(
                    f"mastodon-backups-s3-credentials-{mastodon_hostname}"
                    )[0]['id']

            secrets_id = bitwarden.get_item(
                    f"mastodon-server-secrets-{mastodon_hostname}"
                    )[0]['id']

            # {'mastodon_admin_credentials_bitwarden_id': admin_id,
            update_argocd_appset_secret(
                    k8s_obj,
                    {'mastodon_smtp_credentials_bitwarden_id': smtp_id,
                     'mastodon_postgres_credentials_bitwarden_id': db_id,
                     'mastodon_redis_bitwarden_id': redis_id,
                     'mastodon_s3_admin_credentials_bitwarden_id': s3_admin_id,
                     'mastodon_s3_postgres_credentials_bitwarden_id': s3_db_id,
                     'mastodon_s3_mastodon_credentials_bitwarden_id': s3_id,
                     'mastodon_s3_backups_credentials_bitwarden_id': s3_backups_id,
                     'mastodon_elasticsearch_credentials_bitwarden_id': elastic_id,
                     'mastodon_server_secrets_bitwarden_id': secrets_id}
                    )


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
