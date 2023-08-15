#!/usr/bin/env python3.11
"""
           NAME: smol-k8s-lab
    DESCRIPTION: Works with k3s and KinD
         AUTHOR: jessebot(AT)linux(d0t)com
        LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE
"""

from click import option, command
import logging
from os import path
from rich.logging import RichHandler
from rich.panel import Panel
from sys import exit

# custom libs and constants
from .env_config import check_os_support, process_configs
from .constants import (KUBECONFIG, HOME_DIR, DEFAULT_CONFIG,
                        INITIAL_USR_CONFIG, VERSION)
from .k8s_tools.argocd import install_with_argocd
from .k8s_tools.k8s_lib import K8s
from .k8s_distros.base import create_k8s_distro, delete_cluster
from .k8s_apps.base_install import install_base_apps
from .k8s_apps.external_secrets_operator import configure_external_secrets
from .k8s_apps.keycloak import configure_keycloak_and_vouch
from .k8s_apps.federated import (configure_nextcloud, configure_matrix,
                                 configure_mastodon)
from .k8s_apps.zitadel import configure_zitadel_and_vouch
from .pretty_printing.console_logging import CONSOLE, header, sub_header
from .pretty_printing.help_text import RichCommand, options_help
from .utils.bw_cli import BwCLI
HELP = options_help()
HELP_SETTINGS = dict(help_option_names=['-h', '--help'])


def process_log_config(log_dict: dict = {'log':
                                         {'level': 'warn', 'file': None}}):
    """
    Sets up rich logger for the entire project. (ᐢ._.ᐢ) <---- who is he? :3
    Returns logging.getLogger("rich")
    """
    # determine logging level
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

    # this uses the opts dictionary as parameters to logging.basicConfig()
    logging.basicConfig(**opts)

    if log_file:
        return logging
    else:
        return logging.getLogger("rich")


# an ugly list of decorators, but these are the opts/args for the whole script
@command(cls=RichCommand, context_settings=HELP_SETTINGS)
@option('--config', '-c', metavar="CONFIG_FILE", type=str,
        default=path.join(HOME_DIR, '.config/smol-k8s-lab/config.yaml'),
        help=HELP['config'])
@option('--delete', '-D', is_flag=True, help=HELP['delete'])
@option('--setup', '-s', is_flag=True, help=HELP['setup'])
@option('--k9s', '-K', is_flag=True, help=HELP['k9s'])
@option('--version', '-v', is_flag=True, help=HELP['version'])
def main(config: str = "",
         delete: bool = False,
         setup: bool = False,
         k9s: bool = False,
         log_file: str = "",
         bitwarden: bool = False,
         version: bool = False):
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

    if setup:
        # installs extra tooling such as helm, k9s, and krew
        from .utils.setup_k8s_tools import do_setup
        do_setup()

    k8s = INITIAL_USR_CONFIG.get('k8s_distros', DEFAULT_CONFIG['k8s_distros'])
    if delete:
        for distro in k8s:
            # exits the script after deleting the cluster
            delete_cluster(k8s)
        exit()

    # process all of the config file, or create a new one and also grab secrets
    USR_CFG, SECRETS = process_configs(DEFAULT_CONFIG, INITIAL_USR_CONFIG)

    # setup logging immediately
    log = process_log_config(USR_CFG['log'])
    log.debug("Logging configured.")

    for distro in k8s:
        # this is a dict of all the apps we can install
        apps = USR_CFG['apps']
        # check immediately if metallb is enabled
        metallb_enabled = apps['metallb']['enabled']

        # install the actual KIND, k0s, k3s, or k3d (experimental) cluster
        create_k8s_distro(distro, metallb_enabled,
                          USR_CFG['k3s'].get('extra_args', []))

        argo_enabled = apps['argo_cd']['enabled']

        k8s_obj = K8s()

        # installs all the base apps: metallb, ingess-nginx, and cert-manager
        install_base_apps(k8s_obj, k8s, metallb_enabled, argo_enabled,
                          apps['argo_cd_appset_secret_plugin']['enabled'],
                          SECRETS['cert-manager_email'],
                          SECRETS['metallb_address_pool'])

        # 🦑 Install Argo CD: continuous deployment app for k8s
        if argo_enabled:
            bw = None
            # if we're using bitwarden, unlock the vault
            if bitwarden:
                bw = BwCLI(USR_CFG['bitwarden']['overwrite'])
                bw.unlock()

            # user can configure a special domain for argocd
            argocd_fqdn = SECRETS['argo_cd_hostname']
            from .k8s_apps.argocd import configure_argocd
            configure_argocd(k8s_obj, argocd_fqdn, bw,
                             apps['argo_cd_appset_secret_plugin']['enabled'],
                             SECRETS)

            # setup bitwarden external secrets if we're using that
            if apps['external_secrets_operator']['enabled']:
                eso = apps.pop('external_secrets_operator')
                bitwarden_eso_provider = apps.pop('bitwarden_eso_provider')
                configure_external_secrets(k8s_obj, eso, bitwarden_eso_provider,
                                           bw)

            # setup keycloak if we're using that for OIDC
            if apps['keycloak']['enabled']:
                keycloak = apps.pop('keycloak')
                vouch = apps.pop('vouch')
                configure_keycloak_and_vouch(k8s_obj, keycloak, vouch, bw)

            # setup zitadel if we're using that for OIDC
            elif apps['zitadel']['enabled']:
                zitadel = apps.pop('zitadel')
                vouch = apps.pop('vouch')
                configure_zitadel_and_vouch(k8s_obj, zitadel, vouch, bw)

            if apps['nextcloud']['enabled']:
                nextcloud = apps.pop('nextcloud')
                configure_nextcloud(k8s_obj, nextcloud, bw)

            if apps['mastodon']['enabled']:
                mastodon = apps.pop('mastodon')
                configure_mastodon(k8s_obj, mastodon, bw)

            if apps['matrix']['enabled']:
                matrix = apps.pop('matrix')
                configure_matrix(k8s_obj, matrix, bw)

            # after argocd, keycloak, bweso, and vouch are up, we install all
            # apps as Argo CD Applications
            for app_key, app in apps.items():
                if app['enabled'] and not app['argo']['part_of_app_of_apps']:
                    install_with_argocd(app_key, app['argo'])

            # lock the bitwarden vault on the way out, to be polite :3
            if bitwarden:
                bw.lock()

    # we're done :D
    print("")
    CONSOLE.print(Panel("\nSmol K8s Lab completed!\n\nMake sure you run:\n"
                        f"[b]export KUBECONFIG={KUBECONFIG}\n",
                        title='[green]◝(ᵔᵕᵔ)◜ Success!',
                        subtitle='♥ [cyan]Have a nice day[/] ♥',
                        border_style="cornflower_blue"))
    print("")


if __name__ == '__main__':
    main()
