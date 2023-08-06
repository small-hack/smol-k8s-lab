#!/usr/bin/env python3.11
"""
NAME: env_config.py
DESC: everything to do with initial configuration of a new environment
"""

from rich.prompt import Confirm
from rich.live import Live
from rich.table import Table
from .constants import OS, VERSION, USR_CONFIG_FILE
from .console_logging import print_panel


def check_os_support(supported_os=('Linux', 'Darwin')):
    """
    verify we're on a supported OS and ask to quit if not.
    """
    if OS[0] not in supported_os:
        offical_supported_list = ", ".join(supported_os)
        msg = (f"[ohno]{OS[0]}[/ohno] isn't officially supported in {VERSION}."
               f" We have only tested the following: {offical_supported_list}")
        print_panel(msg, "⚠️  [warn]WARNING")

        quit_y = Confirm.ask("🌊 You're in uncharted waters. Wanna quit?")
        if quit_y:
            print_panel("That's probably safer. Have a safe day, friend.",
                        "Safety Award ☆ ")
            quit()
        else:
            print_panel("[red]Yeehaw, I guess.", "¯\\_(ツ)_/¯")
    else:
        print_panel("Operating System and Architechure [green]supported ♥",
                    "[cornflower_blue]Compatibility Check")


def generate_table() -> Table:
    """
    Make a new table.
    """
    table = Table()
    table.add_column("Parameter")
    table.add_column("Value")

    table.add_row("")
    return table


def create_new_config():
    """
    interactive create new config
    """

    with Live(generate_table(), refresh_per_second=4) as live:
        live.update(generate_table())

        return


def process_configs():
    """
    process the config in ~/.config/smol-k8s-lab/config.yaml if it exists,
    then process the cli dict, and fill in defaults for anything not explicitly
    defined. Returns full final config as dict for use in script.
    """

    if USR_CONFIG_FILE:
        print(f"🗂 ⚙️  user_config_file: \n{USR_CONFIG_FILE}\n")
    else:
        USR_CONFIG_FILE = create_new_config()

    return USR_CONFIG_FILE
