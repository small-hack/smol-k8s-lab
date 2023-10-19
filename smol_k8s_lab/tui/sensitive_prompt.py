# smol-k8s-lab libraries
from smol_k8s_lab.tui.util import placeholder_grammar

# external libraries
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid, VerticalScroll
from textual.screen import ModalScreen
from textual.validation import Length
from textual.widgets import Button, Input, Label

                    
class PromptForSensitiveInfo(ModalScreen):
    """
    modal screen with inputs to modify globally available templating parameters 
    for argocd that are passed to the argocd appset secrets plugin helm chart
    """
    CSS_PATH = ["../css/base_modal.tcss",
                "../css/prompt_for_sensitive_info.tcss"]

    BINDINGS = [Binding(key="b,escape,q",
                        key_display="b",
                        action="app.pop_screen",
                        description="Back")]

    def __init__(self, app: str) -> None:
        self.app = app
        super().__init__()

    def compose(self) -> ComposeResult:
        # base screen grid
        question = (
                f"[#ffaff9]Enter[/] [i]sensitive[/] info for [#C1FF87]{self.app}[/]."
                )

        with Grid(id="modify-globals-modal-screen"):
            # grid for app question and buttons
            with Grid(id="modify-globals-question-box"):
                yield Label(question, id="modal-text")

                yield VerticalScroll(id="scroll-container")

    def on_mount(self,) -> None:
        if self.global_params:
            scroll_container = self.get_widget_by_id("scroll-container")
            # iterate through the app's secret keys
            for secret_key, value in self.global_params.items():
                scroll_container.mount(self.generate_secret_key_row(secret_key, value))

        question_box = self.get_widget_by_id("modify-globals-question-box")
        question_box.border_subtitle = "[@click=app.pop_screen]close[/]"

        if self.app.speak_screen_titles:
            # if text to speech is on, read screen title
            self.app.action_say(f"Screen title: Enter sensitive data for {self.app}")

    def generate_secret_key_row(self,
                                secret_key: str,
                                value: str = "",
                                new: bool = False) -> Grid:
        """
        add a new row of secret keys to pass to an argocd app
        if new param is set to True, we also write it to the yaml
        """
        if new:
            self.app.cfg['apps_global_config'][secret_key] = value
            self.app.write_yaml()

        key_label = secret_key.replace("_", " ")

        # create input
        input_keys = {"placeholder": placeholder_grammar(key_label),
                      "classes": "app-secret-key-input",
                      "name": secret_key,
                      "validators": [Length(minimum=2)]}

        if value:
            input_keys['value'] = value

        input = Input(**input_keys)
        input.validate(value)

        # create the input row
        secret_label = Label(f"{key_label}:", classes="app-input-label")

        return Grid(secret_label, input, classes="app-input-row")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        add a new input row for secret stuff
        """
        if event.button.id == "new-secret-button":
            inputs_box = self.get_widget_by_id("scroll-container")
            input = self.get_widget_by_id("new-secret")

            # add new secret key row
            inputs_box.mount(
                    self.generate_secret_key_row(input.value, "", True)
                    )
            # clear the input field after we're created the new row and
            # updated the yaml
            input.value = ""

    @on(Input.Changed)
    def input_validation(self, event: Input.Changed) -> None:
        if event.validation_result.is_valid:
            self.app.cfg['apps_global_config'][event.input.name] = event.input.value
            self.app.write_yaml()
        else:
            if self.app.bell_on_error:
                self.app.bell()
            # if result is not valid, notify the user why
            self.notify("\n".join(event.validation_result.failure_descriptions),
                        severity="warning",
                        title="⚠️ Input Validation Error\n")
