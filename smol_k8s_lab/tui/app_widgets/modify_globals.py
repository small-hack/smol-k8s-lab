# smol-k8s-lab libraries
from smol_k8s_lab.tui.util import placeholder_grammar

# external libraries
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid, VerticalScroll
from textual.screen import ModalScreen
from textual.validation import Length
from textual.widgets import Button, Input, Label, Static


class ModifyAppGlobals(Static):
    """
    tiny widget with a "modify globals" button to launch a modal screen to modify
    globally available templating parameters for argocd that are passed to
    the argocd appset secrets plugin helm chart
    """
    def compose(self) -> ComposeResult:
        with Grid(classes="button-grid"):
            button = Button("✏️  Modify Globals", id="modify-globals-button")
            button.tooltip = (
                    "Modify globally available Argo CD ApplicationSet templating values"
                    )
            yield button

    def on_button_pressed(self):
        self.app.push_screen(ModifyAppGlobalsScreen())


class ModifyAppGlobalsScreen(ModalScreen):
    """
    modal screen with inputs to modify globally available templating parameters
    for argocd that are passed to the argocd appset secrets plugin helm chart
    """
    CSS_PATH = ["../css/base_modal.tcss",
                "../css/modify_globals_modal.tcss"]
    BINDINGS = [
            Binding(key="b,escape,q",
                    key_display="b",
                    action="app.pop_screen",
                    description="Back"),
            Binding(key="f5",
                    key_display="f5",
                    description="Speak",
                    action="app.speak_element",
                    show=True)
            ]

    def __init__(self) -> None:
        self.global_params = self.app.cfg["apps_global_config"]
        super().__init__()

    def compose(self) -> ComposeResult:
        # base screen grid
        question = ("[#ffaff9]Modify[/] [i]globally[/] available Argo CD ApplicationSet"
                    " [#C1FF87]templating values[/].")

        with Grid(id="modify-globals-modal-screen"):
            # grid for app question and buttons
            with Grid(id="modify-globals-question-box"):
                yield Label(question, id="modal-text")

                yield VerticalScroll(id="scroll-container-for-globals")

                key_input = Input(placeholder="new key name",
                                  id="new-secret",
                                  classes="new-secret-input",
                                  validators=Length(minimum=2))

                key_input.tooltip = ("🔒key name to pass to the Argo CD ApplicationSet"
                                     " Secret Plugin Generator for templating non-"
                                     "sensitive values such as hostnames.")

                add_button = Button("➕", id="new-secret-button",
                                    classes="new-secret-button")
                add_button.tooltip = (
                        "After the input to the right is valid, click to add a "
                        "new global parameter for all Argo CD ApplicationSets")
                add_button.disabled = True

                with Grid(classes="app-input-row", id="new-row"):
                    yield add_button
                    yield key_input

    def on_mount(self,):
        if self.global_params:
            scroll_container = self.get_widget_by_id("scroll-container-for-globals")
            # iterate through the app's secret keys
            for secret_key, value in self.global_params.items():
                scroll_container.mount(self.generate_secret_key_row(secret_key, value))

        question_box = self.get_widget_by_id("modify-globals-question-box")
        question_box.border_subtitle = "[@click=app.pop_screen]close[/]"

        self.call_after_refresh(self.app.play_screen_audio, screen="modify_globals")

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
                      "id": secret_key,
                      "validators": [Length(minimum=2)]}

        if value:
            input_keys['value'] = value

        input = Input(**input_keys)
        input.validate(value)

        # create the input row
        secret_label = Label(f"{key_label}:", classes="input-label")

        return Grid(secret_label, input, classes="app-input-row")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        add a new input row for secret stuff
        """
        if event.button.id == "new-secret-button":
            inputs_box = self.get_widget_by_id("scroll-container-for-globals")
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
        if event.input.id == "new-secret":
            if event.validation_result.is_valid:
                self.get_widget_by_id("new-secret-button").disabled = False
            else:
                if self.app.cfg['smol_k8s_lab']['tui']['accessibility']['bell']['on_error']:
                    self.app.bell()
                # if result is not valid, notify the user why
                self.notify("\n".join(event.validation_result.failure_descriptions),
                            severity="warning",
                            title="⚠️ Input Validation Error\n")

                self.get_widget_by_id("new-secret-button").disabled = True
        else:
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
