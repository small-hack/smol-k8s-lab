#!/usr/bin/env python3.11
from smol_k8s_lab.tui.util import bool_option, input_field
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Grid
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Label, Switch, Select
from textual.widget import Widget
from xdg_base_dirs import xdg_state_home


XDG_STATE_HOME = str(xdg_state_home()) + "/smol-k8s-lab/smol.log"

logging_tool_tip = (
        "[deep_sky_blue3]Logging verbosity levels[/]:\n\n"
        "[on grey11][grey50]error[/]:  only print error messages[/]\n\n"
        "[grey50]warn[/]:   print warnings, plus errors\n\n"
        "[on grey11][grey50]info[/]:   check ins at each stage, plus warnings/errors[/]"
        "\n\n"
        "[grey50]debug[/]:  most detailed, includes all sorts of variable printing"
        )

duplicate_tool_tip = (
    "[deep_sky_blue3]Handling vault item duplicates[/]:\n\n"
    "[on grey11][grey50]ask[/]:       (default) display a dialog window asking how to "
    "proceed[/]\n\n"
    "[grey50]edit[/]:      if 1 item found, edit item. Still ask if multiple found\n\n"
    "[on grey11][grey50]duplicate[/]: create an additional item with the same name[/]"
    "\n\n"
    "[grey50]no_action[/]: don't do anything, just continue on with the script")


class SmolK8sLabConfig(Screen):
    """
    Textual app to configure smol-k8s-lab itself
    """
    CSS_PATH = ["./css/smol_k8s_cfg.tcss"]

    BINDINGS = [Binding(key="b,q,escape",
                        key_display="b",
                        action="app.pop_screen",
                        description="Back"),
                Binding(key="n",
                        key_display="n",
                        action="app.request_confirm",
                        description="Next")]

    def __init__(self, config: dict) -> None:
        self.cfg = config
        self.show_footer = self.app.cfg['smol_k8s_lab']['tui']['show_footer']
        super().__init__()

    def compose(self) -> ComposeResult:
        """
        Compose app with tabbed content.
        """
        # header to be cute
        yield Header()

        # Footer to show help keys, if enabled
        footer = Footer()
        if not self.show_footer:
            footer.display = False
        yield footer

        with Grid(id="config-screen"):
            yield LoggingConfig(self.cfg['log'])

            # local password manager config for enabled, name, and duplicate strategy
            yield PasswordManagerConfig(self.cfg['local_password_manager'])

            # configure command to run after tui phase
            yield RunCommandConfig(self.cfg['run_command'])

    def on_mount(self) -> None:
        """
        screen and box border styling
        """
        sub_title = "Configure logging and password manager"
        self.sub_title = sub_title

        self.call_after_refresh(self.app.play_screen_audio, screen="config")


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
        possible_levels = ['error', 'warn', 'debug', 'info']

        with Grid(id="logging-config"):
            yield Label("Configure logging for all of smol-k8s-lab.",
                        classes="soft-text")

            with Grid(id="logging-config-row-grid"):
                with Grid(classes="selection-row"):
                    label = Label("level:", classes="selection-label")
                    label.tooltip = logging_tool_tip
                    yield label

                    yield Select(((line, line) for line in possible_levels),
                                 id="log-level-select",
                                 value=current_level)

                yield input_field(label="file",
                                  initial_value=logging_opt['file'],
                                  name="file",
                                  placeholder=XDG_STATE_HOME,
                                  tooltip="File to log to. If provided, no console "
                                          "logging will take place")

    def on_mount(self) -> None:
        """
        box border styling
        """
        log_title = "🪵[i]Configure[/] [#C1FF87]Logging"
        self.get_widget_by_id("logging-config").border_title = log_title

    @on(Select.Changed)
    def update_parent_for_select(self, event: Select.Changed) -> None:
        self.app.cfg['smol_k8s_lab']['log']['level'] = str(event.value)
        self.app.write_yaml()

    @on(Input.Changed)
    def update_parent_config_for_input(self, event: Input.Changed) -> None:
        """
        update self and parent app self config with changed input field
        """
        self.app.cfg['smol_k8s_lab']['log'][input.name] = event.input.value
        self.app.write_yaml()


class PasswordManagerConfig(Widget):
    def __init__(self, config: dict) -> None:
        self.cfg = config
        super().__init__()

    def compose(self) -> ComposeResult:
        """
        Compose widget for configuring the local password manager
        """
        with Container(id="password-manager-config"):
            yield Label("Save app credentials to a local password manager vault. "
                        "Only Bitwarden is supported at this time, but if enabled,"
                        " Bitwarden can be used as your k8s external secret provider."
                        " To avoid a password prompt, export the following env vars: "
                        "BW_PASSWORD, BW_CLIENTID, BW_CLIENTSECRET",
                        classes="soft-text")

            enabled_tooltip = "enable storing passwords for apps in a password manager"
            with Grid(id="password-manager-options-grid"):
                yield bool_option("enabled",
                                  self.cfg['enabled'],
                                  "enabled",
                                  enabled_tooltip)

                with Grid(classes="selection-row"):
                    label = Label("duplicate strategy:",
                                  classes="radioset-row-label")
                    label.tooltip = duplicate_tool_tip
                    yield label

                    current_value = self.cfg['duplicate_strategy']
                    possible_values = ["ask", "edit", "duplicate", "no_action"]

                    yield Select(((line, line) for line in possible_values),
                                 id="duplicate-strategy-select",
                                 value=current_value)

    def on_mount(self) -> None:
        """
        box border styling
        """
        pass_title = "🔒[i]Configure[/] [#C1FF87]Password Manager"
        self.get_widget_by_id("password-manager-config").border_title = pass_title

    @on(Switch.Changed)
    def update_parent_config(self, event: Switch.Changed) -> None:
        """
        update the parent app's config file yaml obj
        """
        value = event.value
        switch_name = event.switch.name
        self.app.cfg['smol_k8s_lab']['local_password_manager'][switch_name] = value
        self.app.write_yaml()

    @on(Select.Changed)
    def update_parent_for_select(self, event: Select.Changed) -> None:
        password_cfg = self.app.cfg['smol_k8s_lab']['local_password_manager']
        password_cfg['duplicate_strategy'] = str(event.value)
        self.app.write_yaml()


class RunCommandConfig(Widget):
    def __init__(self, config: dict) -> None:
        self.cfg = config
        super().__init__()

    def compose(self) -> ComposeResult:
        """
        Compose widget for configuring run-command
        """
        tip = ("If window behavior is set to same window, command runs "
               "[i]after[/i] smol-k8s-lab has completed.")
        # run-command config for log.level and log.file
        with Grid(id="run-command-config"):

            yield Label(tip, classes="soft-text")

            with Grid(id="run-command-config-row-grid"):
                with Grid(classes="selection-row"):
                    label = Label("terminal:", classes="selection-label")
                    label.tooltip = (
                            "terminal to use for running command in split pane,"
                            " new tab, or new window. Not used if [b]window "
                            "behavior[/b] set to [b]same window[/b]"
                            )
                    yield label

                    yield Select(((line, line) for line in ['wezterm', 'zellij']),
                                 id="terminal-select",
                                 name="terminal",
                                 value=self.cfg['terminal'],
                                 allow_blank=False)

                window_behavior_list = ['same window', 'split left', 'split right',
                                        'split top', 'split bottom', 'new tab',
                                        'new window']

                with Grid(classes="selection-row"):
                    label = Label("window behavior:", classes="selection-label")
                    label.tooltip = (
                            "terminal to use for running command in split pane,"
                            " new tab, or new window. Not used if window "
                            "behavior set to default"
                            )
                    yield label

                    yield Select(((line, line) for line in window_behavior_list),
                                 id="window-behavior-select",
                                 value=self.cfg['window_behavior'],
                                 allow_blank=False)

            yield input_field(label="command",
                              initial_value=self.cfg['command'],
                              name="command",
                              placeholder="command to run after config stage",
                              tooltip="Command to run at start of CLI phase")

    def on_mount(self) -> None:
        """
        box border styling
        """
        self.border_title = "💻 [i]Configure[/] [#C1FF87]command to run after config"

    @on(Select.Changed)
    def update_parent_for_select(self, event: Select.Changed) -> None:
        if event.select.name == "terminal":
            self.app.cfg['smol_k8s_lab']['run_command']['terminal'] = str(event.value)
        else:
            self.app.cfg['smol_k8s_lab']['run_command']['window_behavior'] = str(event.value)
        self.app.write_yaml()

    @on(Input.Changed)
    def update_parent_config_for_input(self, event: Input.Changed) -> None:
        """
        update self and parent app self config with changed input field
        """
        self.app.cfg['smol_k8s_lab']['run_command'][event.input.name] = event.input.value
        self.app.write_yaml()
