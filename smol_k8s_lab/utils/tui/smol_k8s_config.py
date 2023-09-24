#!/usr/bin/env python3.11
from smol_k8s_lab.utils.tui.cluster_config_help import HelpScreen
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.binding import Binding
from textual.widgets import (Footer, Header, Input, Label, Switch, RadioButton,
                             RadioSet)
from textual.widget import Widget
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
                        show=True),
                Binding(key="q",
                        key_display="q",
                        action="save_and_quit",
                        description="Save and Quit",
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

        # Footer to show help keys, if enabled
        footer = Footer()
        if not self.cfg['interactive']['show_footer']:
            footer.display = False
        yield Footer()

        with Container(id="config-screen"):
            # interactive config for hide_footer, always_enabled, and k9s
            yield TuiConfig(self.cfg['interactive'])

            yield LoggingConfig(self.cfg['log'])

            # local password manager config for enabled, name, and overwrite
            yield PasswordManagerConfig(self.cfg['local_password_manager'])

    def on_mount(self) -> None:
        """
        screen and box border styling
        """
        self.title = "ʕ ᵔᴥᵔʔ smol k8s lab"
        self.sub_title = "now with more 🦑"

    def action_request_help(self) -> None:
        """
        if the user presses 'h' or '?', show the help modal screen
        """
        self.push_screen(HelpScreen())

    def update_parent_cfg(self, key: str) -> None:
        """
        udpate parent cfg
        """
        # self.ancestors[-1].usr_cfg['smol_k8s_lab'][key] = self.cfg[key]
        return

class TuiConfig(Widget):
    def __init__(self, config: dict) -> None:
        self.cfg = config
        super().__init__()

    def compose(self) -> ComposeResult:
        """
        Compose widget for configuring the interactive experience
        """

        with Container(id="tui-config"):
            with Horizontal(classes="double-switch-row"):
                yield bool_option(
                        label="show footer:",
                        name="show_footer",
                        switch_value=self.cfg['show_footer'],
                        tooltip="show the footer at the bottom of the screen"
                        )

                yield bool_option(
                        label="always enabled:",
                        name="always_enabled",
                        switch_value=self.cfg['always_enabled'],
                        tooltip="always enable interactive mode"
                        )

            yield bool_option(
                    label="k9s enabled:",
                    name="k9s-enabled",
                    switch_value=self.cfg['k9s']['enabled'],
                    tooltip="launch k9s, a k8s TUI dashboard when cluster is up"
                    )

            yield input_field(
                    label="k9s command:",
                    name="k9s-command",
                    initial_value=self.cfg['k9s']['command'],
                    placeholder="command to run when k9s starts",
                    tooltip="command to run via k9s"
                    )

    def on_mount(self) -> None:
        """
        box border styling
        """
        tui_title = "🖥️ [green]Terminal UI Config"
        self.get_widget_by_id("tui-config").border_title = tui_title

    @on(Switch.Changed)
    def update_parent_config_for_switch(self, event: Switch.Changed) -> None:
        """
        update the parent app's config file yaml obj
        """
        truthy_value = event.value
        switch_name = event.switch.name

        parent_cfg = event.switch.ancestors[-1].cfg['interactive']

        if "k9s" in switch_name:
            name = switch_name.replace("k9s-","")
            self.cfg['k9s'][name] = truthy_value
            parent_cfg['k9s'][name] = truthy_value
        else:
            self.cfg[switch_name] = truthy_value
            parent_cfg[switch_name] = truthy_value

        event.switch.ancestors[-1].update_parent_cfg('interactive')

    @on(Input.Changed)
    def update_parent_config_for_input(self, event: Input.Changed) -> None:
        input = event.input
        parent_cfg = input.ancestors[-1].cfg['interactive']['k9s']

        parent_cfg[input.name] = input.value
        input.ancestors[-1].update_parent_cfg('interactive')


class LoggingConfig(Widget):
    def __init__(self, config: dict) -> None:
        self.cfg = config
        super().__init__()

    def compose(self) -> ComposeResult:
        """
        Compose widget for configuring logging
        """
        # logging config for log.level and log.file
        logging_opt = self.cfg
        current_level = logging_opt['level']
        possible_levels = ['debug' , 'info', 'warn', 'error']
        possible_levels.remove(current_level)

        with Container(id="logging-config"):
            with Horizontal(classes="radioset-row"):
                yield Label("level:", classes="radioset-row-label")
                with RadioSet(classes="radioset-row-radioset"):
                    button = RadioButton(current_level, value=True)
                    button.BUTTON_INNER = "♥"
                    yield button
                    for level in possible_levels:
                        button = RadioButton(level)
                        button.BUTTON_INNER = "♥"
                        yield button

            yield input_field("file:",
                              logging_opt['file'],
                              XDG_STATE_HOME,
                              "File to log to")

    def on_mount(self) -> None:
        """
        box border styling
        """
        log_title = "🪵[gold3]Logging Config"
        self.get_widget_by_id("logging-config").border_title = log_title

    @on(Input.Changed)
    def update_parent_config_for_input(self, event: Input.Changed) -> None:
        """
        update self and parent app self config with changed input field
        """
        input = event.input
        parent_cfg = input.ancestors[-1]

        parent_cfg.cfg['log'][input.name] = input.value
        parent_cfg.update_parent_cfg('log')

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """
        update  self and parent app self config with changed radio set
        """
        parent_cfg = event.radio_set.ancestors[-1]
        self.cfg['level'] = parent_cfg.cfg['log']['level'] = event.pressed.label
        parent_cfg.update_parent_cfg('log')


class PasswordManagerConfig(Widget):
    def __init__(self, config: dict) -> None:
        self.cfg = config
        super().__init__()

    def compose(self) -> ComposeResult:
        """
        Compose widget for configuring the local password manager
        """
        with Container(id="password-manager-config"):
            yield Label("Only Bitwarden is supported at this time")

            enabled_tooltip = "enable storing passwords for apps in a password manager"
            with Horizontal(classes="double-switch-row"):
                yield bool_option("enabled:",
                                  self.cfg['enabled'],
                                  "enabled",
                                  enabled_tooltip)

                yield bool_option("Overwrite existing:",
                                  self.cfg['overwrite'],
                                  "overwrite",
                                  "Overwrite existing items in your password vault. "
                                  "If disabled, smol-k8s-lab will create duplicates, "
                                  "which can be dangerous")

    def on_mount(self) -> None:
        """
        box border styling
        """
        pass_title = "🔒[cornflower_blue]Password Manager"
        self.get_widget_by_id("password-manager-config").border_title = pass_title

    @on(Switch.Changed)
    def update_parent_config(self, event: Switch.Changed) -> None:
        """
        update the parent app's config file yaml obj
        """
        truthy_value = event.value
        switch_name = event.switch.name
        parent_cfg = event.switch.ancestors[-1].cfg['local_password_manager']

        # update our own truthy value
        parent_cfg[switch_name] = self.cfg[switch_name] = truthy_value

        event.switch.ancestors[-1].update_parent_cfg('interactive')


def bool_option(label: str, switch_value: bool, name: str, tooltip: str) -> Horizontal:
    """
    returns a label and switch row in a Horizontal container
    """
    label = Label(label, classes="bool-switch-row-label")
    label.tooltip = tooltip

    switch = Switch(value=switch_value,
                    classes="bool-switch-row-switch",
                    name=name)

    return Horizontal(label, switch, classes="bool-switch-row")

def input_field(label: str, initial_value: str, name: str, placeholder: str,
                tooltip: str = "") -> Horizontal:
    """ 
    returns an input label and field within a Horizontal container
    """
    label = Label(label, classes="input-row-label")
    label.tooltip = tooltip

    input_dict = {"placeholder": placeholder,
                  "classes": "input-row-input",
                  "name": name}
    if initial_value:
        input_dict["value"] = initial_value

    input = Input(**input_dict)

    return Horizontal(label, input, classes="input-row")

if __name__ == "__main__":
    # this is temporary during testing
    from smol_k8s_lab.constants import INITIAL_USR_CONFIG
    reply = SmolK8sLabConfig(INITIAL_USR_CONFIG['smol_k8s_lab']).run()
    print(reply)
