from textual import on
from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.validation import Length, Validator, ValidationResult
from textual.widgets import Button, Label, Input


class ClusterNameModalScreen(ModalScreen):
    CSS_PATH = ["./css/cluster_modal.css"]


    def __init__(self, current_names: list = []) -> None:
        self.current_names = current_names
        super().__init__()

    def compose(self) -> ComposeResult:
        question = ("What would you like your cluster's name to be?")
        # base screen grid
        with Grid(id="cluster-question-modal-screen", classes="new-size"):
            # grid for cluster question and buttons
            with Grid(id="cluster-question-box"):
                yield Label(question, id="cluster-modal-text")

                yield Input(value="smol-k8s-lab",
                            validators=[Length(minimum=2),
                                        CheckIfNameAlreadyInUse(self.current_names)],
                            placeholder="Name of your cluster",
                            id="cluster-name-input")

                with Grid(id="modal-button-box"):
                    submit = Button("submit", id="cluster-submit")
                    submit.tooltip = "submit name of cluster"
                    yield submit 

                    cancel = Button("cancel", id="cancel")
                    cancel.tooltip = "return to start page"
                    yield cancel 

    @on(Input.Changed)
    def input_validation(self, event: Input.Changed) -> None:
        if event.validation_result.is_valid:
            # if result is valid, enable the submit button
            self.get_widget_by_id("cluster-submit").disabled = False
        else:
            # if result is not valid, notify the user why
            self.notify("\n".join(event.validation_result.failure_descriptions),
                        timeout=8,
                        severity="warning",
                        title="⚠️ Input Validation Error\n")

            # and disable the submit button
            self.get_widget_by_id("cluster-submit").disabled = True

    @on(Button.Pressed)
    def button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cluster-submit":
            cluster_name = self.query_one(Input).value
            self.dismiss(cluster_name)
        else:
            self.dismiss(None)


# A custom validator to check if the name is already in use
class CheckIfNameAlreadyInUse(Validator):

    def __init__(self, cluster_names: list) -> None:
        super().__init__()
        self.cluster_names = cluster_names

    def validate(self, value: str) -> ValidationResult:
        """Check if a string is already in use as a clustername."""
        if value in self.cluster_names:
            return self.failure("That cluster name is already in use 🫨")
        else:
            return self.success()
