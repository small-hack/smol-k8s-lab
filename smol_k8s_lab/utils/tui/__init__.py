from .configure_all_screen import ClusterConfig
from smol_k8s_lab.constants import INITIAL_USR_CONFIG


def launch_config_tui():
    """
    Run all the TUI screens
    """
    config = ClusterConfig(INITIAL_USR_CONFIG).run()

    apps = config['apps']

    secrets = {}
    if apps['appset_secret_plugin']['enabled']:
        for app, metadata in apps.items():
            if metadata['enabled']:
                secret_keys = metadata['argo']['secret_keys']
                if secret_keys:
                    for key, value in secret_keys.items():
                        secrets[f"{app}_{key}"] = value

    return config, secrets
