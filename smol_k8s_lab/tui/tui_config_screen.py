#!/usr/bin/env python3.11
from smol_k8s_lab.tui.util import bool_option, input_field
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Label, Switch
from textual.widget import Widget


class TuiConfigScreen(Screen):
    """
    Textual app to configure smol-k8s-lab itself
    """
    CSS_PATH = ["./css/tui_config.tcss"]

    BINDINGS = [Binding(key="b,q,escape",
                        key_display="b",
                        action="app.pop_screen",
                        description="Back")]

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
        footer.display = False
        yield footer

        with Grid(id="config-screen"):
            # tui config for hide_footer, enabled, and k9s
            yield TuiConfig(self.cfg)

    def on_mount(self) -> None:
        """
        screen and box border styling
        """
        self.title = "ʕ ᵔᴥᵔʔ smol k8s lab"
        self.sub_title = "configure smol-k8s-lab itself"

        # turn on the footer if it's enabled in the root app cfg
        if self.app.cfg['smol_k8s_lab']['tui']['show_footer']:
            self.query_one(Footer).display = True


class TuiConfig(Widget):
    def __init__(self, config: dict) -> None:
        self.cfg = config
        super().__init__()

    def compose(self) -> ComposeResult:
        """
        Compose widget for configuring the tui experience
        """

        with Grid(id="tui-config"):
            yield Label("These parameters are all related to the TUI itself.",
                        classes="soft-text")
            with Grid(classes="triple-switch-row"):
                yield bool_option(
                        label="enabled:",
                        name="enabled",
                        switch_value=self.cfg['enabled'],
                        tooltip=("Enable tui mode (also known as TUI mode) by "
                                 "default, otherwise you need to pass in -i each time")
                        )

                yield bool_option(
                        label="footer:",
                        name="show_footer",
                        switch_value=self.cfg['show_footer'],
                        tooltip="show the footer at the bottom of the screen"
                        )

                yield bool_option(
                        label="k9s:",
                        name="k9s-enabled",
                        switch_value=self.cfg['k9s']['enabled'],
                        tooltip="launch k9s, a k8s TUI dashboard when cluster is up"
                        )

            with Grid(classes="accessibility-row"):
                accessibility = self.cfg['accessibility']
                yield bool_option(
                        label="bell:",
                        name="bell-enabled",
                        switch_value=accessibility['bell'],
                        tooltip="enables the terminal bell when something goes wrong"
                        )
                yield bool_option(
                        label="text to speech:",
                        name="text-to-speech-enabled",
                        switch_value=accessibility['text_to_speech']['enabled'],
                        tooltip="enables text to speech to read aloud elements on "
                                "each screen"
                        )

                yield input_field(
                        label="speech program:",
                        name="speech-program",
                        initial_value=accessibility['text_to_speech']['speech_program'],
                        placeholder="name of program for speech",
                        tooltip="If text to speech is enabled, this is the name of"
                                " the command line interface speech program."
                        )


            with Grid(classes="k9s-input-row"):
                yield input_field(
                        label="k9s command:",
                        name="k9s-command",
                        initial_value=self.cfg['k9s']['command'],
                        placeholder="command to run when k9s starts",
                        tooltip="if k9s is enabled, run this command when it starts"
                        )

    def on_mount(self) -> None:
        """
        box border styling
        """
        tui_title = "🖥️ [i]Configure[/] [#C1FF87]Terminal UI"
        self.get_widget_by_id("tui-config").border_title = tui_title

    @on(Switch.Changed)
    def update_parent_config_for_switch(self, event: Switch.Changed) -> None:
        """
        update the parent app's config file yaml obj
        """
        truthy_value = event.value
        switch_name = event.switch.name

        parent_cfg = self.app.cfg['smol_k8s_lab']['tui']

        if "k9s" in switch_name:
            name = switch_name.replace("k9s-","")
            self.cfg['k9s'][name] = truthy_value
            parent_cfg['k9s'][name] = truthy_value
        else:
            self.cfg[switch_name] = truthy_value
            parent_cfg[switch_name] = truthy_value

        self.app.write_yaml()

    @on(Input.Changed)
    def update_parent_config_for_input(self, event: Input.Changed) -> None:
        input = event.input
        input_name = event.input.name

        if "k9s" in input_name:
            name = input_name.replace("k9s-","")
            self.cfg['k9s'][name] = input.value
            self.app.cfg['smol_k8s_lab']['tui']['k9s'][name] = input.value
        else:
            self.app.cfg['smol_k8s_lab']['tui'][input.name] = input.value

        self.app.write_yaml()
