from smol_k8s_lab.constants import VERSION
from smol_k8s_lab.tui.util import bool_option, input_field
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Switch
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
            # accessibility options config
            yield AccessibilityWidget(self.cfg['accessibility'])

            # tui config for hide_footer, enabled
            yield TuiConfig(self.cfg, id="tui-config")

    def on_mount(self) -> None:
        """
        screen and box border styling and read the screen title aloud
        """
        sub_title = "Configure Terminal UI and Accessibility features"
        self.sub_title = sub_title

        # turn on the footer if it's enabled in the root app cfg
        if self.app.cfg['smol_k8s_lab']['tui']['show_footer']:
            self.query_one(Footer).display = True

        self.app.play_screen_audio("tui_config")


class TuiConfig(Widget):
    def __init__(self, config: dict, id: str = "") -> None:
        self.cfg = config
        super().__init__(id=id)

    def compose(self) -> ComposeResult:
        """
        Compose widget for configuring the tui experience
        """
        with Grid(classes="tui-config-row"):
            yield bool_option(
                    label="tui enabled",
                    name="enabled",
                    switch_value=self.cfg['enabled'],
                    tooltip=("Enable tui mode by default. Otherwise, you"
                             " need to pass in the interactive flag on the "
                             "command line each time")
                    )

            yield bool_option(
                    label="footer",
                    name="show_footer",
                    switch_value=self.cfg['show_footer'],
                    tooltip="show the footer at the bottom of the screen"
                    )

    def on_mount(self) -> None:
        """
        box border styling
        """
        tui_title = "🖥️ [i]Configure[/] [#C1FF87]Terminal UI"
        self.border_title = tui_title

    @on(Switch.Changed)
    def update_parent_config_for_switch(self, event: Switch.Changed) -> None:
        """
        update the parent app's config file yaml obj
        """
        truthy_value = event.value
        switch_name = event.switch.name

        parent_cfg = self.app.cfg['smol_k8s_lab']['tui']

        self.cfg[switch_name] = truthy_value
        parent_cfg[switch_name] = truthy_value

        self.app.write_yaml()

    @on(Input.Changed)
    def update_parent_config_for_input(self, event: Input.Changed) -> None:
        input = event.input
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

            with Grid(id="bell-row", classes="double-switch-row"):

                yield bool_option(
                        label="bell on focus",
                        name="bell-on_focus",
                        switch_value=self.cfg['bell']['on_focus'],
                        tooltip=(
                            "Ring the terminal bell each time your focus "
                            "changes to another element on the screen.")
                        )

                yield bool_option(
                        label="bell on error",
                        name="bell-on_error",
                        switch_value=self.cfg['bell']['on_error'],
                        tooltip=(
                            "Ring the terminal bell anytime there's a warning "
                            "or error"
                            )
                )

            yield input_field(
                    label="speech program",
                    name="text-to-speech-speech_program",
                    initial_value=self.cfg['text_to_speech']['speech_program'],
                    placeholder="name of program for speech",
                    tooltip=(
                        "If text to speech is enabled, this is the name of"
                        " the command line interface speech program. If not "
                        "provided, we use pre-generated audio files"
                        ),
                    extra_row_class="tts-row-title"
                    )

            with Grid(id="tts-row", classes="double-switch-row"):
                yield bool_option(
                        label="on key press",
                        name="text-to-speech-on_key_press",
                        switch_value=self.cfg['text_to_speech']['on_key_press'],
                        tooltip=(
                            "Only read aloud the element if the f5 key is pressed. "
                            "This key will be configurable in the future."
                            )
                        )
                yield bool_option(
                        label="on focus",
                        name="text-to-speech-on_focus",
                        switch_value=self.cfg['text_to_speech']['on_focus'],
                        tooltip=(
                            "On each focus of a new element on the screen, "
                            "read aloud the element id, and value/tooltip if "
                            "available."
                            )
                        )

            with Grid(classes="double-switch-row"):
                yield bool_option(
                        label="screen titles",
                        name="text-to-speech-screen_titles",
                        switch_value=self.cfg['text_to_speech']['screen_titles'],
                        tooltip=(
                            "Read aloud each screen title."
                            )
                        )

                yield bool_option(
                        label="screen descriptions",
                        name="text-to-speech-screen_descriptions",
                        switch_value=self.cfg['text_to_speech']['screen_descriptions'],
                        tooltip=(
                            "Read aloud each screen description."
                            )
                        )

    def on_mount(self) -> None:
        """
        box border styling
        """
        title = "♿️ [i]Configure[/] [#C1FF87]Accessibility Features"
        self.get_widget_by_id("accessibility-config").border_title = title
        self.get_widget_by_id("bell-row").border_title = "Terminal Bell Config"
        self.query_one(".tts-row-title").border_title = "Text to Speech Config"

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
