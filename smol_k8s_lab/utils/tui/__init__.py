from .select_distro import SelectK8sDistro
from .select_apps import SelectApps
from .configure_apps import ConfigureApps
import logging as log


def launch_tui():
    """
    Run all the TUI screens
    """
    distros = SelectK8sDistro().run()
    log.info(f"selected_distro: {distros}")

    selected_apps = SelectApps().run()
    log.info(f"selected_apps: {selected_apps}")

    configured_apps = ConfigureApps(selected_apps).run()
    log.info(configured_apps)

    return True
