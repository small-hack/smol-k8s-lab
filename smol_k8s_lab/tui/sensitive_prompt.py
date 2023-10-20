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


ENV_VARS = {
        "nextcloud": ["RESTIC_REPO_PASSWORD"],

        "mastodon": ["S3_ACCESS_KEY",
                     "S3_ACCESS_ID",
                     "RESTIC_REPO_PASSWORD"],

        "matrix": []
        }


def check_for_required_env_vars(app: str, app_cfg: dict = {}) -> list:
    """ 
    check for required env vars and return list of dict and set:
        values found dict, set of values you need to prompt for 
    """
    # keep track of a list of stuff to prompt for
    prompt_values = []
    # this is the stuff we already have in env vars
    values = {}
    # default smtp env var
    smtp_env_var = "SMTP_PASSWORD"

    env_vars = ENV_VARS.copy()

    if app == "nextcloud":
        access_id_env_var = "S3_ACCESS_ID"
        access_key_env_var = "S3_ACCESS_KEY"
        if app_cfg['argo']['secret_keys']['backup_method'].lower() == 's3':
            # add prompts for s3 access key/id if backup method is s3
            env_vars[app].append(access_id_env_var)
            env_vars[app].append(access_key_env_var)
        else:
            # remove prompts for s3 access key/id
            if access_id_env_var in env_vars[app]:
                env_vars[app].remove(access_id_env_var)
            if access_key_env_var in env_vars[app]:
                env_vars[app].remove(access_key_env_var)

    # only prompt for smtp credentials if mail is enabled
    if 'change me' not in app_cfg['init']['values']['smtp_user']:
        # add prompts if mail is enabled
        env_vars[app].append(smtp_env_var)
    else:
        if smtp_env_var in env_vars[app]:
            env_vars[app].remove(smtp_env_var)
        # HACK: not really sure what to do here and I'm short on time, so 🤷
        values[smtp_env_var] = "mail not enabled"

    if env_vars[app]:
        # iterate through list of env vars to check
        for item in env_vars[app]:
            value = environ.get("_".join([app.upper(), item]), default="")

            # append any missing to prompt_values
            if not value:
                prompt_values.append(item.lower())
            else:
                values[item.lower()] = value

    return values, set(prompt_values)

                    
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

    def __init__(self, app_name: str, sensitive_info_list: list) -> None:
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
        key_label = key.replace("_", " ")

        # create input
        input_keys = {"placeholder": placeholder_grammar(key_label),
                      "name": key,
                      "password": True,
                      "id": "-".join([self.app_name, key, "input"]),
                      "validators": [Length(minimum=2)]}

        input = Input(**input_keys)
        input.validate(value)

        # create the input row
        secret_label = Label(f"{key_label}:", classes="input-label")

        return Grid(secret_label, input, classes="sensitive-input-row")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        add a new input row for secret stuff
        """
        self.dismiss(self.app_name, self.return_dict)

    @on(Input.Changed)
    def input_validation(self, event: Input.Changed) -> None:
        if event.validation_result.is_valid:
            self.return_dict[event.input.name] = event.input.value
            self.query_one(Button).disabled = False
        else:
            if self.app.bell_on_error:
                self.app.bell()
            # if result is not valid, notify the user why
            self.notify("\n".join(event.validation_result.failure_descriptions),
                        severity="warning",
                        title="⚠️ Input Validation Error\n")

            self.query_one(Button).disabled = True