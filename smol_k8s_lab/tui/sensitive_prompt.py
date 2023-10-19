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
from os import environ


env_vars = {
        "nextcloud": ["NEXTCLOUD_SMTP_PASSWORD",
                      "NEXTCLOUD_S3_ACCESS_KEY",
                      "NEXTCLOUD_S3_ACCESS_ID",
                      "NEXTCLOUD_RESTIC_REPO_PASSWORD"],
        "mastodon": [
            "MASTODON_SMTP_PASSWORD",
            "MASTODON_S3_ACCESS_KEY",
            "MASTODON_S3_ACCESS_ID",
            "MASTODON_RESTIC_REPO_PASSWORD"],

        "matrix": ["MATRIX_SMTP_PASSWORD"]
        }


def check_for_required_env_vars(env_var_list: list) -> None:
    # keep track of a list of stuff to prompt for
    prompt_values = []
    # this is the stuff we already have in env vars
    values = []

    # iterate through list of env vars to check
    for item in env_var_list:
        value = environ.get(item, default="")

        # append any missing to prompt_values
        if not value:
            prompt_values.append(value)
        else:
            values[item] = value

    return values, prompt_values

                    
class PromptForSensitiveInfoModalScreen(ModalScreen):
    """
    modal screen with sensitive inputs
    for argocd that are passed to the argocd appset secrets plugin helm chart
    """
    CSS_PATH = ["./css/base_modal.tcss",
                "./css/prompt_for_sensitive_info.tcss"]

    BINDINGS = [Binding(key="b,escape,q",
                        key_display="b",
                        action="app.pop_screen",
                        description="Back")]

    def __init__(self,
                 app_name: str = "nextcloud",
                 sensitive_info_list: list = env_vars['nextcloud']) -> None:
        self.app_name = app_name
        self.sensitive_info_list = sensitive_info_list
        self.return_dict = {}
        super().__init__()

    def compose(self) -> ComposeResult:
        # base screen grid
        question = ("[#ffaff9]Enter[/] [i]sensitive[/] info for "
                    f"[#C1FF87]{self.app_name}[/].")

        with Grid(id="sensitive-input-screen"):
            # grid for app question and buttons
            with Grid(id="modify-globals-question-box"):
                yield Label(question, id="modal-text")

                yield VerticalScroll(id="scroll-container")

                with Grid(classes="submit-button-row"):
                    yield Button('✔️ submit', id='submit-button')

    def on_mount(self,) -> None:
        scroll_container = self.get_widget_by_id("scroll-container")

        # iterate through the things to prompt for
        for key in self.sensitive_info_list:
            self.return_dict[key] = ""
            scroll_container.mount(self.generate_row(key))

        question_box = self.get_widget_by_id("modify-globals-question-box")
        question_box.border_subtitle = "[@click=app.pop_screen]cancel[/]"

        if self.app.speak_screen_titles:
            # if text to speech is on, read screen title
            self.app.action_say(
                    f"Screen title: Enter sensitive data for {self.app_name}")

    def generate_row(self, key: str, value: str = "") -> Grid:
        """
        add a new row of keys to pass to an argocd app
        """

        # make lower case, split by _, drop the first word, and join with spaces
        key_label = " ".join(key.lower().split("_")[1:])

        # create input
        input_keys = {"placeholder": placeholder_grammar(key_label),
                      "name": key,
                      "validators": [Length(minimum=2)]}

        if value:
            input_keys['value'] = value

        input = Input(**input_keys)
        input.validate(value)

        # create the input row
        secret_label = Label(f"{key_label}:", classes="input-label")

        return Grid(secret_label, input, classes="sensitive-input-row")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        add a new input row for secret stuff
        """
        self.dismiss(self.return_dict)

    @on(Input.Changed)
    def input_validation(self, event: Input.Changed) -> None:
        if event.validation_result.is_valid:
            self.return_dict[event.input.name] = event.input.value
            self.query(Button).disabled = False
        else:
            if self.app.bell_on_error:
                self.app.bell()
            # if result is not valid, notify the user why
            self.notify("\n".join(event.validation_result.failure_descriptions),
                        severity="warning",
                        title="⚠️ Input Validation Error\n")

            self.query(Button).disabled = True
