#!/usr/bin/env python3.11
from smol_k8s_lab.utils.tui.smol_k8s_help import HelpScreen
from smol_k8s_lab.utils.write_yaml import dump_to_file
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.binding import Binding
from textual.widgets import (Footer, Header, Input, Label, Switch, RadioButton,
                             RadioSet)
from xdg_base_dirs import xdg_state_home

XDG_STATE_HOME = xdg_state_home

class SmolK8sLabConfig(App):
    """
    Textual app to configure smol-k8s-lab itself
    """
    CSS_PATH = ["./css/smol_k8s_cfg.tcss"]
    BINDINGS = [Binding(key="h,?",
                        key_display="h",
                        action="request_help",
                        description="Show Help",
                        show=True)]

    def __init__(self, config: dict) -> None:
        self.cfg = config
        super().__init__()

    def compose(self) -> ComposeResult:
        """
        Compose app with tabbed content.
        """
        # header to be cute
        yield Header()

        # Footer to show keys
        footer = Footer()
        if not self.cfg['interactive']['show_footer']:
            footer.display = False

        yield Footer()

        yield 

        # interactive config for hide_footer, always_enabled, and k9s
        interactive_opt = self.cfg['interactive']
        with Container(id="interactive-config"):
            yield bool_option("show footer:",
                              interactive_opt['show_footer'],
                              "show the footer at the bottom of the screen")

            yield bool_option("always enabled:",
                              interactive_opt['always_enabled'],
                              "always enable interactive mode")

            yield bool_option("k9s enabled:",
                              interactive_opt['k9s']['enabled'],
                              "launch k9s, a k8s TUI dashboard, after we're finished")

            yield input_field("k9s command:",
                              interactive_opt['k9s']['command'],
                              "applications.argoproj.io",
                              "command to run via k9s")

        # logging config for log.level and log.file
        logging_opt = self.cfg['log']
        current_level = logging_opt['level']
        possible_levels = ['debug' , 'info', 'warn', 'error']
        possible_levels.remove(current_level)

        with Container(id="logging-config"):
            with Horizontal(classes="radioset-row"):
                yield Label("level:", classes="radioset-row-label")
                with RadioSet(classes="radioset-row-radioset"):
                    yield RadioButton(current_level, value=True)
                    for level in possible_levels:
                        yield RadioButton(level)

            yield input_field("file:",
                              logging_opt['file'],
                              XDG_STATE_HOME,
                              "File to log to")

        # local password manager config for enabled, name, and overwrite
        pw_opt = self.cfg['local_password_manager']
        with Container(id="password-manager-config"):
            yield Label("Only Bitwarden is supported at this time")

            enabled_tooltip = "enable storing passwords for apps in a password manager"
            yield bool_option("enabled:", pw_opt['enabled'], enabled_tooltip)

            yield bool_option("Overwrite existing:",
                              pw_opt['overwrite'],
                              "Overwrite existing items in your password vault. "
                              "If disabled, smol-k8s-lab will create duplicates, "
                              "which can be dangerous")

    def on_mount(self) -> None:
        """
        screen and box border styling
        """
        self.title = "ʕ ᵔᴥᵔʔ smol k8s lab"
        self.sub_title = "now with more 🦑"

        pass_title = "🔒[pink]Password Manager"
        self.get_widget_by_id("password-manager-config").border_title = pass_title

        tui_title = "⚙️ [green]Terminal UI Config"
        self.get_widget_by_id("interactive-config").border_title = tui_title

        log_title = "🪵[gold3]Logging Config"
        self.get_widget_by_id("logging-config").border_title = log_title

    def action_request_help(self) -> None:
        """
        if the user presses 'h' or '?', show the help modal screen
        """
        self.push_screen(HelpScreen())

    def save_and_leave(self) -> None:
        """
        if user presses '?', 'h', or 'q', we exit the help screen
        """
        dump_to_file(self.cfg)
        # self.app.pop_screen()
        self.exit(self.cfg)


def bool_option(label: str, switch_value: bool, tooltip: str):
    label = Label(label, classes="bool-switch-row-label")
    label.tooltip = tooltip

    switch = Switch(value=switch_value, classes="bool-switch-row-switch")

    return Horizontal(label, switch, classes="bool-switch-row")

def input_field(label: str, initial_value: str, placeholder: str, tooltip: str = ""):
    label = Label(label, classes="input-row-label")
    label.tooltip = tooltip

    input_dict = {"placeholder": placeholder,
                  "classes": "input-row-input"}
    if initial_value:
        input_dict["value"] = initial_value

    input = Input(**input_dict)

    return Horizontal(label, input, classes="input-row")

if __name__ == "__main__":
    # this is temporary during testing
    from smol_k8s_lab.constants import INITIAL_USR_CONFIG
    reply = SmolK8sLabConfig(INITIAL_USR_CONFIG['smol_k8s_lab']).run()
    print(reply)
