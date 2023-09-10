from .select_distro import SelectDistro


def launch_tui():
    """
    Run all the TUI screens
    """
    SelectDistro().run()
    return True
