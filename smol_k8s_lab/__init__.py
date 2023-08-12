#!/usr/bin/env python3.11
"""
           NAME: smol-k8s-lab
    DESCRIPTION: Works with k3s and KinD
         AUTHOR: jessebot(AT)linux(d0t)com
        LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE
"""

from click import option, argument, command, Choice
import logging
from os import path
from pathlib import Path
from rich.panel import Panel
from rich.logging import RichHandler
from sys import exit

# custom libs and constants
from .k8s_tools.argocd import install_with_argocd
from .k8s_apps.base_install import install_base_apps, install_k8s_distro
from .k8s_apps.setup_bweso import setup_bweso_secret
from .bw_cli import BwCLI
from .console_logging import CONSOLE, header, sub_header
from .constants import (XDG_CACHE_DIR, KUBECONFIG, HOME_DIR, DEFUALT_CONFIG,
                        INITIAL_USR_CONFIG, VERSION)
from .env_config import check_os_support, process_app_configs
from .help_text import RichCommand, options_help


HELP = options_help()
HELP_SETTINGS = dict(help_option_names=['-h', '--help'])
SUPPORTED_DISTROS = ['k0s', 'k3s', 'kind']
# process all of the config file, or create a new one and also grab secrets
USR_CFG, SECRETS = process_app_configs(DEFUALT_CONFIG, INITIAL_USR_CONFIG)


def setup_logger(level="", log_file=""):
    """
    Sets up rich logger for the entire project.
    (ᐢ._.ᐢ) <---- who is he? :3
    Returns logging.getLogger("rich")
    """
    # determine logging level
    if not level:
        level = USR_CFG['log']['level']

    log_level = getattr(logging, level.upper(), None)

    # these are params to be passed into logging.basicConfig
    opts = {'level': log_level, 'format': "%(message)s", 'datefmt': "[%X]"}

    # we only log to a file if one was passed into config.yaml or the cli
    if not log_file:
        log_file = USR_CFG['log'].get('file', None)

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


def delete_cluster(k8s_distro="k3s"):
    """
    Delete a k0s, k3s, or KinD cluster entirely.
    It is suggested to perform a reboot after deleting a k0s cluster.
    """
    header(f"Bye bye, [b]{k8s_distro}[/b]!")

    if k8s_distro == 'k3s':
        from .k8s_distros.k3s import uninstall_k3s
        uninstall_k3s()

    elif k8s_distro == 'kind':
        from .k8s_distros.kind import delete_kind_cluster
        delete_kind_cluster()

    elif k8s_distro == 'k0s':
        from .k8s_distros.k0s import uninstall_k0s
        uninstall_k0s()

    else:
        header("┌（・o・）┘≡З  Whoops. {k8s_distro} not YET supported.")

    sub_header("[grn]◝(ᵔᵕᵔ)◜ Success![/grn]")
    exit()


# an ugly list of decorators, but these are the opts/args for the whole script
@command(cls=RichCommand, context_settings=HELP_SETTINGS)
@argument("k8s", metavar="<k0s, k3s, kind>", default="")
@option('--config', '-c', metavar="CONFIG_FILE", type=str,
        default=path.join(HOME_DIR, '.config/smol-k8s-lab/config.yaml'),
        help=HELP['config'])
@option('--delete', '-D', is_flag=True, help=HELP['delete'])
@option('--setup', '-s', is_flag=True, help=HELP['setup'])
@option('--k9s', '-K', is_flag=True, help=HELP['k9s'])
@option('--log_level', '-l', metavar='LOGLEVEL', help=HELP['log_level'],
        type=Choice(['debug', 'info', 'warn', 'error']))
@option('--log_file', '-o', metavar='LOGFILE', help=HELP['log_file'])
@option('--bitarden', '-b', is_flag=True,
        help=HELP['bitwarden'])
@option('--version', '-v', is_flag=True, help=HELP['version'])
def main(k8s: str = "",
         config: str = "",
         delete: bool = False,
         setup: bool = False,
         k9s: bool = False,
         log_level: str = "",
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

    # setup logging immediately
    log = setup_logger(log_level, log_file)
    log.debug("Logging configured.")

    # make sure this OS is supported
    check_os_support()

    if setup:
        # installs extra tooling such as helm, k9s, and krew
        from .setup_k8s_tools import do_setup
        do_setup()
        if not k8s:
            exit()

    # make sure we got a valid k8s distro
    if k8s not in SUPPORTED_DISTROS:
        CONSOLE.print(f'\n☹ Sorry, "[b]{k8s}[/]" is not a currently supported '
                      'k8s distro. Please try again with any of '
                      f'{SUPPORTED_DISTROS}.\n')
        exit()

    if delete:
        # exits the script after deleting the cluster
        delete_cluster(k8s)

    # make sure the cache directory exists (typically ~/.cache/smol-k8s-lab)
    Path(XDG_CACHE_DIR).mkdir(exist_ok=True)

    # this is a dict of all the apps we can install
    apps = USR_CFG['apps']
    # check immediately if argo_cd or metallb are enabled
    argo_enabled = apps['argo_cd']['enabled']
    metallb_enabled = apps['metallb']['enabled']

    # install the actual KIND, k0s, or k3s cluster
    install_k8s_distro(k8s, metallb_enabled,
                       USR_CFG['k3s'].get('extra_args', []))


    # installs all the base apps: metallb, ingess-nginx, and cert-manager
    install_base_apps(k8s, metallb_enabled, argo_enabled,
                      apps['argo_cd_appset_secret_plugin']['enabled'],
                      SECRETS['cert-manager_email'],
                      SECRETS['metallb_ip']['address_pool'])

    # setup bitwarden external secrets if we're using that
    if apps['bitwarden_eso_provider']['enabled']:
        setup_bweso_secret()

    # if we're using bitwarden
    if bitwarden:
        bw = BwCLI()
        bw.unlock()

    # 🦑 Install Argo CD: continuous deployment app for k8s
    if argo_enabled:
        # user can configure a special domain for argocd
        argocd_fqdn = SECRETS['argo_cd_domain']
        from .k8s_apps.argocd import configure_argocd
        configure_argocd(argocd_fqdn, bw,
                         apps['argo_cd_appset_secret_plugin']['enabled'],
                         SECRETS)

        # after argocd is up, we install all apps as argocd apps
        for app_key, app in apps.items():
            if app['enabled'] and not app['argo']['part_of_app_of_apps']:
                install_with_argocd(app_key, app['argo'])

    if password_manager:
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
