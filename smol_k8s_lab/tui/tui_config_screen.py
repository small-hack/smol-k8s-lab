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
                        description="Back"),
                Binding(key="n",
                        show=False,
                        action="app.bell")]

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

        with Grid(id="general-config-screen"):
            # tui config for hide_footer, enabled, and k9s
            yield TuiConfig(self.cfg)

            # accessibility options config
            yield AccessibilityWidget(self.cfg['accessibility'])

    def on_mount(self) -> None:
        """
        screen and box border styling and read the screen title aloud
        """
        self.title = "ʕ ᵔᴥᵔʔ smol k8s lab"
        sub_title = (
                "Screen title: Configure Terminal UI and Accessibility features"
                )
        self.sub_title = sub_title

        # turn on the footer if it's enabled in the root app cfg
        if self.app.cfg['smol_k8s_lab']['tui']['show_footer']:
            self.query_one(Footer).display = True

        if self.app.speak_screen_titles:
            self.app.action_say(
                    self.sub_title + ". There are 2 boxes on the screen. Box 1: "
                    "Configure Terminal UI. Box 2: Configure Accessibility. Focus"
                    " starts on Box 1."
                    )


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
                        tooltip=("Enable tui mode by default. Otherwise, you"
                                 " need to pass in the interactive flag on the "
                                 "command line each time")
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


class AccessibilityWidget(Widget):
    def __init__(self, config: dict) -> None:
        """ 
        Accessibility widget to allow for configuring the bell and text to speech
        """
        self.cfg = config
        super().__init__()

    def compose(self) -> ComposeResult:
        """
        Compose widget for configuring the tui experience
        """
        with Grid(id="accessibility-config"):

            yield Label("These parameters are all related to accessibility, "
                        "both in the TUI and CLI.",
                        classes="soft-text")

            with Grid(id="bell-row"):

                yield bool_option(
                        label="bell on focus:",
                        name="bell-on_focus",
                        switch_value=self.cfg['bell']['on_focus'],
                        tooltip=(
                            "Ring the terminal bell each time your focus "
                            "changes to another element on the screen.")
                        )

                yield bool_option(
                        label="bell on error:",
                        name="bell-on_error",
                        switch_value=self.cfg['bell']['on_error'],
                        tooltip=(
                            "Ring the terminal bell anytime there's a warning "
                            "or error"
                            )
                )

            with Grid(id="tts-row"):
                yield bool_option(
                        label="TTS screen titles:",
                        name="text-to-speech-screen_titles",
                        switch_value=self.cfg['text_to_speech']['screen_titles'],
                        tooltip=(
                            "Read aloud each screen title and description aloud."
                            )
                        )

                yield bool_option(
                        label="TTS on key press:",
                        name="text-to-speech-on_key_press",
                        switch_value=self.cfg['text_to_speech']['on_key_press'],
                        tooltip=(
                            "Only read aloud the element if the f5 key is pressed. "
                            "This key will be configurable in the future."
                            )
                        )

                yield bool_option(
                        label="TTS on focus:",
                        name="text-to-speech-on_focus",
                        switch_value=self.cfg['text_to_speech']['on_focus'],
                        tooltip=(
                            "On each focus of a new element on the screen, "
                            "read aloud the element id, and value/tooltip if "
                            "available."
                            )
                        )

            yield input_field(
                    label="speech program:",
                    name="text-to-speech-speech_program",
                    initial_value=self.cfg['text_to_speech']['speech_program'],
                    placeholder="name of program for speech",
                    tooltip=(
                        "If text to speech is enabled, this is the name of"
                        " the command line interface speech program. On "
                        "macOS, we default to 'say'. On Linux we default to espeak"
                        )
                    )

    def on_mount(self) -> None:
        """
        box border styling
        """
        title = "♿️ [i]Configure[/] [#C1FF87]Accessibility"
        self.get_widget_by_id("accessibility-config").border_title = title

    @on(Switch.Changed)
    def update_parent_config_for_switch(self, event: Switch.Changed) -> None:
        """
        update the parent app's config file yaml obj
        """
        truthy_value = event.value
        switch_name = event.switch.name

        parent_cfg = self.app.cfg['smol_k8s_lab']['tui']['accessibility']

        if "text-to-speech" in switch_name:
            name = switch_name.replace("text-to-speech-", "")
            parent_cfg['text_to_speech'][name] = truthy_value
        else:
            name = switch_name.replace("bell-", "")
            parent_cfg['bell'][name] = truthy_value

        self.app.write_yaml()

    @on(Input.Changed)
    def update_parent_config_for_input(self, event: Input.Changed) -> None:
        parent_cfg = self.app.cfg['smol_k8s_lab']['tui']['accessibility']
        parent_cfg['text_to_speech']['speech_program'] = event.input.value

        self.app.write_yaml()
