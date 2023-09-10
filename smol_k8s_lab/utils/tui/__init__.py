from .select_distro import SelectDistro
from .select_apps import SelectApps
from .configure_apps import ConfigureApps
import logging as log


def launch_tui():
    """
    Run all the TUI screens
    """
    selected_distros = SelectDistro().run()
    log.info(f"selected_distros: {selected_distros}")

    selected_apps = SelectApps().run()
    log.info(f"selected_apps: {selected_apps}")

    ConfigureApps().run()

    return True
