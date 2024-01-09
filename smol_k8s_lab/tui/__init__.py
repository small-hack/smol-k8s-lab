from smol_k8s_lab.tui.base import BaseApp
from smol_k8s_lab.utils.rich_cli.console_logging import print_msg
import sys


def launch_config_tui(config_file: str = ""):
    """
    Run all the TUI screens
    """
    if config_file:
        res = BaseApp(config_file).run()
    else:
        res = BaseApp().run()
    if not res:
        print_msg("[blue]♥[/] [cyan]Have a nice day[/] [blue]♥\n", style="italic")
        sys.exit()

    cluster_name = res[0]
    config = res[1]
    bitwarden_credentials = res[2]

    # assume there's no secrets
    secrets = {}

    # check if we're using the appset_secret_plugin at all
    # if config['apps']['appset_secret_plugin']['enabled']:

    # if we are using the appset_secret_plugin, then grab all the secret keys
    for app, metadata in config['apps'].items():
        if metadata['enabled']:
            secret_keys = metadata['argo'].get('secret_keys', None)
            if secret_keys:
                for key, value in secret_keys.items():
                    secrets[f"{app}_{key}"] = value

    # this is to set global secret keys for all applications
    global_secrets = config['apps_global_config']
    if global_secrets:
        for secret_key, value in global_secrets.items():
            secrets[f'global_{secret_key}'] = value

    return cluster_name, config, secrets, bitwarden_credentials
