from .configure_all_screen import SmolK8sLabConfig
from smol_k8s_lab.constants import INITIAL_USR_CONFIG


def launch_config_tui():
    """
    Run all the TUI screens
    """
    config = SmolK8sLabConfig(INITIAL_USR_CONFIG).run()

    apps = config['apps']
    if apps['appset_secret_plugin']['enabled']:
        secrets = {}
        for app, metadata in apps.items():
            if metadata['enabled']:
                secrets_keys = metadata['argo']['secrets_keys']
                if secrets_keys:
                    for key, value in secrets_keys.items():
                        secrets[f"{app}_{key}"] = value

    return config, secrets
