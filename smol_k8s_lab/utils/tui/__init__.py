from .base import BaseApp


def launch_config_tui():
    """
    Run all the TUI screens
    """
    res = BaseApp().run()
    config = res[0]
    bitwarden_credentials = res[1]

    # assume there's no secrets
    secrets = {}

    # check if we're using the appset_secret_plugin at all
    if config['apps']['appset_secret_plugin']['enabled']:
        # if we are using the appset_secret_plugin, then grab all the secret keys
        for app, metadata in config['apps'].items():
            if metadata['enabled']:
                secret_keys = metadata['argo'].get('secret_keys', None)
                if secret_keys:
                    for key, value in secret_keys.items():
                        secrets[f"{app}_{key}"] = value

        # this is to set the cluster issuer for all applications
        global_cluster_issuer = config['apps_global_config']['cluster_issuer']
        secrets['global_cluster_issuer'] = global_cluster_issuer

    return config, secrets, bitwarden_credentials
