from .base import BaseApp


def launch_config_tui():
    """
    Run all the TUI screens
    """
    config = BaseApp().run()

    # assume there's no secrets
    secrets = {}

    # check is we're using the appset_secret_plugin at all
    if config['apps']['appset_secret_plugin']['enabled']:
        # if we are using the appset_secret_plugin, then grab all the secret keys
        for app, metadata in config['apps'].items():
            if metadata['enabled']:
                secret_keys = metadata['argo']['secret_keys']
                if secret_keys:
                    for key, value in secret_keys.items():
                        secrets[f"{app}_{key}"] = value

    return config, secrets
