from .configure_all_screen import ConfigureAll


def launch_tui():
    """
    Run all the TUI screens
    """
    ConfigureAll().run()

    return True
