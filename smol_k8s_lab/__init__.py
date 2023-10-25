#!/usr/bin/env python3.11
"""
           NAME: smol-k8s-lab
    DESCRIPTION: Works with k3s, KinD, and k3d
         AUTHOR: jessebot(AT)linux(d0t)com
        LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE
"""

from click import option, command
import logging
from os import environ as env
from rich.logging import RichHandler
from rich.panel import Panel

# custom libs and constants
from .constants import INITIAL_USR_CONFIG, XDG_CONFIG_FILE
from .env_config import check_os_support, process_configs
from .bitwarden.bw_cli import BwCLI
from .bitwarden.tui.bitwarden_app import BitwardenCredentialsApp
from .constants import KUBECONFIG, VERSION
from .k8s_apps import (setup_oidc_provider, setup_base_apps,
                       setup_k8s_secrets_management, setup_federated_apps)
from .k8s_apps.argocd import configure_argocd
from .k8s_distros import create_k8s_distro, delete_cluster
from .k8s_tools.argocd_util import install_with_argocd
from .tui import launch_config_tui
from .utils.rich_cli.console_logging import CONSOLE, sub_header, header
from .utils.rich_cli.help_text import RichCommand, options_help


HELP = options_help()
HELP_SETTINGS = dict(help_option_names=['-h', '--help'])


def process_log_config(log_dict: dict = {'level': 'warn', 'file': None}):
    """
    Sets up rich logger for the entire project.
    Returns logging.getLogger("rich")
    """
    # determine logging level and default to warning level
    level = log_dict.get('level', 'warn')
    log_level = getattr(logging, level.upper(), None)

    # these are params to be passed into logging.basicConfig
    opts = {'level': log_level, 'format': "%(message)s", 'datefmt': "[%X]"}

    # we only log to a file if one was passed into config.yaml
    # determine logging level
    log_file = log_dict.get('file', None)

    # rich typically handles much of this but we don't use rich with files
    if log_file:
        opts['filename'] = log_file
        opts['format'] = "%(asctime)s %(levelname)s %(funcName)s: %(message)s"
    else:
        rich_handler_opts = {'rich_tracebacks': True}
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
@option('--config', '-c',
        metavar="CONFIG_FILE",
        type=str,
        default=XDG_CONFIG_FILE,
        help=HELP['config'])
@option('--delete', '-D',
        metavar="CLUSTER_NAME",
        type=str,
        help=HELP['delete'])
@option('--setup', '-s',
        is_flag=True,
        help=HELP['setup'])
@option('--interactive', '-i',
        is_flag=True,
        help=HELP['interactive'])
@option('--version', '-v',
        is_flag=True,
        help=HELP['version'])
def main(config: str = "",
         delete: bool = False,
         setup: bool = False,
         log_file: str = "",
         version: bool = False,
         interactive: bool = False):
    """
    Quickly install a k8s distro for a homelab setup. Installs k3s
    with metallb, ingess-nginx, cert-manager, and argocd
    """
    # only return the version if --version was passed in
    if version:
        print(f'\n🎉 v{VERSION}\n')
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

    if interactive or INITIAL_USR_CONFIG['smol_k8s_lab']['tui']['enabled']:
        cluster_name, USR_CFG, SECRETS, bitwarden_credentials = launch_config_tui()
    else:
        if setup:
            # installs required/extra tooling: kubectl, helm, k9s, argocd, krew
            from .utils.setup_k8s_tools import do_setup
            do_setup()

        # process all of the config file, or create a new one and also grab secrets
        USR_CFG, SECRETS = process_configs()

        # if we're using bitwarden, unlock the vault
        pw_mngr = USR_CFG['smol_k8s_lab']['local_password_manager']
        using_bw_pw_manager = pw_mngr['enabled'] and pw_mngr['name'] == 'bitwarden'
        using_bweso = USR_CFG['apps']['bitwarden_eso_provider']['enabled']

        if using_bw_pw_manager or using_bweso:
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

    # installs all the base apps: metallb/cilium, ingess-nginx, cert-manager
    setup_base_apps(k8s_obj,
                    distro,
                    apps['cilium'],
                    apps['metallb'],
                    apps['ingress_nginx'],
                    apps['cert_manager'],
                    argo_enabled,
                    apps['appset_secret_plugin']['enabled'])

    # 🦑 Install Argo CD: continuous deployment app for k8s
    if argo_enabled:
        # user can configure a special domain for argocd
        argocd_fqdn = SECRETS['argo_cd_hostname']

        configure_argocd(k8s_obj, argocd_fqdn, bw,
                         apps['appset_secret_plugin']['enabled'],
                         SECRETS)

        setup_k8s_secrets_management(k8s_obj,
                                     distro,
                                     apps.pop('external_secrets_operator'),
                                     apps.pop('bitwarden_eso_provider'),
                                     apps.pop('infisical'),
                                     bw)

        # if the global cluster issuer is set to letsencrypt-staging don't
        # verify TLS certs in requests to APIs
        if 'staging' in SECRETS['global_cluster_issuer']:
            api_tls_verify = False
        else:
            api_tls_verify = True

        setup_oidc_provider(k8s_obj,
                            api_tls_verify,
                            apps.pop('zitadel'),
                            apps.pop('vouch'),
                            bw,
                            argocd_fqdn)

        setup_federated_apps(k8s_obj,
                             api_tls_verify,
                             apps.pop('minio'),
                             apps.pop('nextcloud'),
                             apps.pop('mastodon'),
                             apps.pop('matrix'),
                             bw)

        # after argocd, zitadel, bweso, and vouch are up, we install all apps
        # as Argo CD Applications
        header("Installing the rest of the Argo CD apps")
        for app_key, app_meta in apps.items():
            if app_meta['enabled']:
                if not app_meta['argo'].get('part_of_app_of_apps', False):
                    argo_app = app_key.replace('_', '-')
                    sub_header(f"Installing app: {argo_app}")
                    install_with_argocd(k8s_obj, argo_app, app_meta['argo'])

        # lock the bitwarden vault on the way out, to be polite :3
        if bw:
            bw.lock()

    # we're done :D
    print("")
    final_msg = ("\nSmol K8s Lab completed!\n\nMake sure you run:"
                 f"\n[green]export KUBECONFIG={KUBECONFIG}[/green]\n")

    if zitadel_enabled:
        if bw:
            creds = " (credentials are in Bitwarden)"
        else:
            creds = ""
        final_msg += (
                f"\nYou can log into Zitadel, your identity provider here{creds}:\n"
                f"[blue][link]https://{SECRETS['zitadel_hostname']}[/][/]\n"
                 )

    if argo_enabled:
        final_msg += ("\nYou can checkout your k8s apps via Argo CD here:\n"
                      f"[blue][link]https://{argocd_fqdn}[/]\n")

    CONSOLE.print(Panel(final_msg,
                        title='[green]◝(ᵔᵕᵔ)◜ Success!',
                        subtitle='♥ [cyan]Have a nice day[/] ♥',
                        border_style="cornflower_blue"))
    print("")


if __name__ == '__main__':
    main()
