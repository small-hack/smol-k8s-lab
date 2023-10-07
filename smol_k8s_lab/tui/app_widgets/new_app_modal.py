from textual import on
from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.validation import Length, Validator, ValidationResult
from textual.widgets import Button, Input, Label


class NewAppModalScreen(ModalScreen):
    CSS_PATH = ["../css/new_app_modal.css"]


    def __init__(self, current_apps: list = []) -> None:
        self.current_apps = current_apps
        super().__init__()

    def compose(self) -> ComposeResult:
        # base screen grid
        question = ("Please enter a [magenta]name[/] and [magenta]description[/]"
                    " for your [green]Argo CD Application.")

        with Grid(id="question-modal-screen"):
            # grid for app question and buttons
            with Grid(id="question-box"):
                yield Label(question, id="modal-text")

                input = Input(validators=[Length(minimum=2),
                                          CheckIfNameAlreadyInUse(self.current_apps)],
                              placeholder="Name of your Argo CD Application",
                              id="app-name-input")
                input.tooltip = "Name for your application in smol-k8s-lab and Argo CD"
                yield input


                desc_placeholder = "(optional) Description of your Argo CD Application"
                desc_input = Input(placeholder=desc_placeholder,
                                   id="description-input")
                desc_input.tooltip = desc_placeholder + " to be displayed in the UI."
                yield desc_input

                with Grid(id="modal-button-box"):
                    submit = Button("submit", id="app-submit")
                    submit.tooltip = "submit name of new Argo CD Application"
                    submit.disabled = True
                    yield submit 

                    cancel = Button("cancel", id="cancel")
                    cancel.tooltip = "return to start page"
                    yield cancel 

    @on(Input.Changed)
    def input_validation(self, event: Input.Changed) -> None:
        if event.input.id == "app-name-input":
            if event.validation_result.is_valid:
                # if result is valid, enable the submit button
                self.get_widget_by_id("app-submit").disabled = False
            else:
                # if result is not valid, notify the user why
                self.notify("\n".join(event.validation_result.failure_descriptions),
                            severity="warning",
                            title="⚠️ Input Validation Error\n")

                # and disable the submit button
                self.get_widget_by_id("app-submit").disabled = True

    @on(Button.Pressed)
    def button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "app-submit":
            app_name = self.get_widget_by_id("app-name-input").value
            description = self.get_widget_by_id("description-input").value
            self.dismiss([app_name, description])
        else:
            self.dismiss([None, None])


# A custom validator to check if the name is already in use
class CheckIfNameAlreadyInUse(Validator):

    def __init__(self, app_names: list) -> None:
        super().__init__()
        self.app_names = app_names

    def validate(self, value: str) -> ValidationResult:
        """Check if a string is already in use as an app name."""
        if value in self.app_names:
            return self.failure("That app name is already in use 🫨")
        else:
            return self.success()
