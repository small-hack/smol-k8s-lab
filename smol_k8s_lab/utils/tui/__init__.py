from .configure_all_screen import SmolK8sLabConfig
from smol_k8s_lab.constants import INITIAL_USR_CONFIG


def launch_config_tui():
    """
    Run all the TUI screens
    """
    return SmolK8sLabConfig(INITIAL_USR_CONFIG).run()
