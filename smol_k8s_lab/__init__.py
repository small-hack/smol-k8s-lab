#!/usr/bin/env python3.11
"""
           NAME: smol-k8s-lab
    DESCRIPTION: package, cli, and tui for setting up k8s on metal with
                 k3s, KinD, and k3d, as well as installing our or your own
                 Argo CD Apps, ApplicationSets, and Projects.
                 
         AUTHOR: jessebot(AT)linux(d0t)com
        LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE
"""

from click import option, command
import logging
from os import environ as env
from rich.logging import RichHandler
from rich.panel import Panel

# custom libs and constants
from .constants import INITIAL_USR_CONFIG, XDG_CONFIG_FILE, load_yaml
from .env_config import check_os_support, process_configs
from .bitwarden.bw_cli import BwCLI
from .bitwarden.tui.bitwarden_app import BitwardenCredentialsApp
from .constants import KUBECONFIG, VERSION
from .k8s_apps import (setup_oidc_provider, setup_base_apps,
                       setup_k8s_secrets_management, setup_federated_apps)
from .k8s_apps.operators import setup_operators
from .k8s_apps.operators.minio import configure_minio_tenant
from .k8s_distros import create_k8s_distro, delete_cluster
from .k8s_tools.argocd_util import install_with_argocd, check_if_argocd_app_exists
from .tui import launch_config_tui
from .utils.rich_cli.console_logging import CONSOLE, sub_header, header
from .utils.rich_cli.help_text import RichCommand, options_help


HELP = options_help()
HELP_SETTINGS = dict(help_option_names=["-h", "--help"])


def process_log_config(log_dict: dict = {"level": "warn", "file": ""}):
    """
    Sets up rich logger for the entire project.
    Returns logging.getLogger("rich")

    TODO: change this to always add file logger

    """

    # determine logging level and default to warning level
    level = log_dict.get("level", "warn")
    log_level = getattr(logging, level.upper(), None)

    # these are params to be passed into logging.basicConfig
    opts = {"level": log_level, "format": "%(message)s", "datefmt": "[%X]"}

    # we only log to a file if one was passed into config.yaml
    # determine logging level
    log_file = log_dict.get("file", None)

    # rich typically handles much of this but we don't use rich with files
    if log_file:
        opts['filename'] = log_file
        opts['format'] = "%(asctime)s %(levelname)s %(funcName)s: %(message)s"
    else:
        rich_handler_opts = {"rich_tracebacks": True}
        # 10 is the DEBUG logging level int value
        if log_level == 10:
            # log the name of the function if we're in debug mode :)
            opts['format'] = "[bold]%(funcName)s()[/bold]: %(message)s"
            rich_handler_opts['markup'] = True
        else:
            rich_handler_opts['show_path'] = False
            rich_handler_opts['show_level'] = False

        opts['handlers'] = [RichHandler(**rich_handler_opts)]

    # this removes all former loggers, we hope
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # this uses the opts dictionary as parameters to logging.basicConfig()
    logging.basicConfig(**opts)

    if not log_file:
        return logging.getLogger("rich")
    # if the user requested logging to a file, we don't use rich logging
    else:
        return logging


# an ugly list of decorators, but these are the opts/args for the whole script
@command(cls=RichCommand, context_settings=HELP_SETTINGS)
@option("--config", "-c",
        metavar="CONFIG_FILE",
        type=str,
        default=XDG_CONFIG_FILE,
        help=HELP['config'])
@option("--delete", "-D",
        metavar="CLUSTER_NAME",
        type=str,
        help=HELP['delete'])
@option("--interactive", "-i",
        is_flag=True,
        help=HELP['interactive'])
@option("--version", "-v",
        is_flag=True,
        help=HELP['version'])
def main(config: str = "",
         delete: bool = False,
         log_file: str = "",
         version: bool = False,
         interactive: bool = False):
    """
    Quickly install a k8s distro for a homelab setup. Installs k3s
    with metallb, ingess-nginx, cert-manager, and argocd
    """
    # only return the version if --version was passed in
    if version:
        print(f"\n🎉 v{VERSION}\n")
        return True

    # make sure this OS is supported
    check_os_support()

    # if we're just deleting a cluster, do that immediately
    if delete:
        logging.debug("Cluster deletion was requested")
        # exits the script after deleting the cluster
        delete_cluster(delete)

    # declaring bitwarden for the future in case user doesn't enable this
    bitwarden_credentials = None

    # declaring the default name to be smol-k8s-lab
    cluster_name = "smol-k8s-lab"

    # verify if the TUI should be used
    tui_enabled = INITIAL_USR_CONFIG['smol_k8s_lab']['tui']['enabled']
    if config:
        config_dict = load_yaml(config)
        tui_enabled = config_dict['smol_k8s_lab']['tui']['enabled']
    else:
        config_dict = INITIAL_USR_CONFIG

    if interactive or tui_enabled:
        cluster_name, USR_CFG, SECRETS, bitwarden_credentials = launch_config_tui(config_dict)
    else:
        # process all of the config file, or create a new one and also grab secrets
        USR_CFG, SECRETS = process_configs(config_dict)

        # if we're using bitwarden, unlock the vault
        pw_mngr = USR_CFG['smol_k8s_lab']['local_password_manager']
        using_bw_pw_manager = pw_mngr['enabled'] and pw_mngr['name'] == 'bitwarden'
        using_bweso = SECRETS['global_external_secrets']

        if using_bw_pw_manager or using_bweso == 'bitwarden':
            # get bitwarden credentials from the env if there are any
            password = env.get("BW_PASSWORD", None)
            client_id = env.get("BW_CLIENTID", None)
            client_secret = env.get("BW_CLIENTSECRET", None)

            # if any of the credentials are missing from the env, launch the tui
            if not any([password, client_id, client_secret]):
                bitwarden_credentials = BitwardenCredentialsApp().run()
                if not bitwarden_credentials:
                    raise Exception("Exiting because no credentials were passed in "
                                    "but bitwarden is enabled")
            else:
                bitwarden_credentials = {"password": password,
                                         "client_id": client_id,
                                         "client_secret": client_secret}

    # setup logging immediately
    log = process_log_config(USR_CFG['smol_k8s_lab']['log'])
    log.debug("Logging configured.")

    k8s_distros = USR_CFG['k8s_distros']

    # if we have bitwarden credetials unlock the vault
    if bitwarden_credentials:
        strat = USR_CFG['smol_k8s_lab']['local_password_manager']['duplicate_strategy']
        bw = BwCLI(**bitwarden_credentials, duplicate_strategy=strat)
        bw.unlock()
    else:
        bw = None

    # this is a dict of all the apps we can install
    apps = USR_CFG['apps']

    # check immediately if metallb is enabled
    metallb_enabled = apps['metallb']['enabled']
    # check immediately if cilium is enabled
    cilium_enabled = apps['cilium']['enabled']

    # iterate through each passed in k8s distro and create cluster + install apps
    for distro, metadata in k8s_distros.items():
        # if the cluster isn't enabled, just continue on
        if k8s_distros[distro].get('enabled', False):
            selected_distro = distro
            break

    # install the actual KIND, k3s, or k3d cluster
    k8s_obj = create_k8s_distro(cluster_name, selected_distro, metadata,
                                metallb_enabled, cilium_enabled)

    # check if argo is enabled
    argo_enabled = apps['argo_cd']['enabled']
    # check if zitadel is enabled
    zitadel_enabled = apps['zitadel']['enabled']

    # installs all the base apps: metallb/cilium, ingess-nginx, cert-manager, and argocd
    setup_base_apps(k8s_obj,
                    distro,
                    apps['cilium'],
                    apps['metallb'],
                    apps.pop('ingress_nginx'),
                    apps['cert_manager'],
                    argo_enabled,
                    apps['argo_cd']['argo']['directory_recursion'],
                    SECRETS,
                    bw)

    # 🦑 Install Argo CD: continuous deployment app for k8s
    if argo_enabled:
        # setup k8s secrets management and secret stores
        setup_k8s_secrets_management(k8s_obj,
                                     distro,
                                     apps.pop('external_secrets_operator'),
                                     SECRETS['global_external_secrets'],
                                     apps.pop('infisical'),
                                     apps.pop('vault'),
                                     bw)

        # if the global cluster issuer is set to letsencrypt-staging don't
        # verify TLS certs in requests to APIs
        if 'staging' in SECRETS['global_cluster_issuer']:
            api_tls_verify = False
        else:
            api_tls_verify = True

        # Setup minio, our local s3 provider, is essential for creating buckets
        # and cnpg operator, our postgresql operator for creating postgres clusters
        setup_operators(k8s_obj,
                        apps.pop('k8up'),
                        apps.pop('minio_operator'),
                        apps.pop('seaweedfs'),
                        apps.pop('cnpg_operator'),
                        bw)

        # setup OIDC for securing all endpoints with SSO
        oidc_obj = setup_oidc_provider(
                k8s_obj,
                api_tls_verify,
                apps.pop('zitadel'),
                apps.pop('vouch'),
                bw,
                SECRETS['argo_cd_hostname']
                )

        zitadel_hostname = SECRETS.get('zitadel_hostname', "")
        setup_federated_apps(
                k8s_obj,
                api_tls_verify,
                apps.pop('nextcloud'),
                apps.pop('mastodon'),
                apps.pop('matrix'),
                zitadel_hostname,
                oidc_obj,
                bw
                )

        # we support creating a default minio tenant with oidc enabled
        # we set it up here in case other apps rely on it
        minio_tenant_config = apps.pop('minio_tenant')
        if minio_tenant_config and minio_tenant_config.get('enabled', False):
            configure_minio_tenant(k8s_obj,
                                   minio_tenant_config,
                                   api_tls_verify,
                                   zitadel_hostname,
                                   oidc_obj,
                                   bw)

        # after argocd, zitadel, bweso, and vouch are up, we install all apps
        # as Argo CD Applications
        header("Installing the rest of the Argo CD apps")
        for app_key, app_meta in apps.items():
            if app_meta['enabled']:
                app_installed = check_if_argocd_app_exists(app_key)
                if not app_installed:
                    argo_app = app_key.replace('_', '-')
                    sub_header(f"Installing app: {argo_app}")
                    install_with_argocd(k8s_obj, argo_app, app_meta['argo'])

        # lock the bitwarden vault on the way out, to be polite :3
        if bw:
            bw.lock()

    # we're done :D
    print("")
    final_msg = ("\nMake sure you run the following to pick up your k8s configuration:"
                 f"\n[gold3]export[/gold3] [green]KUBECONFIG={KUBECONFIG}[/green]\n")
    if bw:
        final_msg += "\n[i]All credentials are in Bitwarden[/i]\n"

    if argo_enabled:
        if zitadel_enabled:
            final_msg += (
                    f"\n🔑 Zitadel, your identity provider:\n"
                    f"[blue][link]https://{SECRETS['zitadel_hostname']}[/][/]\n"
                     )

        final_msg += ("\n🦑 Argo CD, your k8s apps console:\n"
                      f"[blue][link]https://{SECRETS['argo_cd_hostname']}[/][/]\n")

        minio_admin_hostname = SECRETS.get('minio_admin_console_hostname', "")
        if minio_admin_hostname:
            final_msg += ("\n🦩 Minio operator admin console, for your s3 storage:"
                          f"\n[blue][link]https://{minio_admin_hostname}[/][/]\n")

        minio_tenant_hostname = SECRETS.get('minio_user_console_hostname', "")
        if minio_tenant_hostname:
            final_msg += ("\n🪿 Minio user console, for your s3 storage:"
                          f"\n[blue][link]https://{minio_tenant_hostname}[/][/]\n")

        nextcloud_hostname = SECRETS.get('nextcloud_hostname', "")
        if nextcloud_hostname:
            final_msg += ("\n☁️ Nextcloud, for your worksuite:\n"
                          f"[blue][link]https://{nextcloud_hostname}[/][/]\n")

        mastodon_hostname = SECRETS.get('mastodon_hostname', "")
        if mastodon_hostname:
            final_msg += ("\n🐘 Mastodon, for your social media:\n"
                          f"[blue][link]https://{mastodon_hostname}[/][/]\n")

        matrix_hostname = SECRETS.get('matrix_hostname', "")
        if matrix_hostname:
            final_msg += ("\n🗣️ Matrix, for your chat:\n"
                          f"[blue][link]https://{matrix_hostname}[/][/]\n")

    CONSOLE.print(Panel(final_msg,
                        title='[green]◝(ᵔᵕᵔ)◜ Success!',
                        subtitle='♥ [cyan]Have a nice day[/] ♥',
                        border_style="cornflower_blue"))
    print("")


if __name__ == '__main__':
    main()
