# smol-k8s-lab libraries
from smol_k8s_lab.tui.validators.already_exists import CheckIfNameAlreadyInUse

# external libraries
import random
from textual import on
from textual.app import ComposeResult
from textual.containers import Grid
from textual.validation import Length
from textual.widgets import Button, Input, Static

# list of approved words for nouns
CUTE_NOUNS = [
        "bunny", "hoglet", "puppy", "kitten", "knuffel", "friend", "egel",
        "meerkoet", "raccoon", "wasbeertje"
        ]

CUTE_ADJECTIVE = [
        "lovely", "adorable", "cute", "friendly", "nice", "leuke", "mooie",
        "vriendelijke", "cool", "soft", "smol", "small", "klein"
        ]


class NewClusterInput(Static):
    """
    small widget with an input and button that takes the names of a cluster,
    and changes the
    """
    def compose(self) -> ComposeResult:
        with Grid(id="new-cluster-button-container"):
            input = Input(validators=[
                              Length(minimum=2),
                              CheckIfNameAlreadyInUse(self.app.cluster_names)
                              ],
                          placeholder="Name of your new cluster",
                          id="cluster-name-input")
            input.tooltip = ("Name of your ✨ [i]new[/] cluster. Note: The k8s distro"
                             " (selected on the next screen) will be pre-pended to the "
                             "name of the cluster by default.")
            yield input

            new_button = Button("✨ New Cluster", id="new-cluster-button")
            new_button.tooltip = "Add a new cluster managed by smol-k8s-lab"
            yield new_button

    def on_mount(self) -> None:
        input = self.get_widget_by_id("cluster-name-input")
        input.value = random.choice(CUTE_ADJECTIVE) + '-' + random.choice(CUTE_NOUNS)

    @on(Input.Changed)
    @on(Input.Submitted)
    def input_validation(self, event: Input.Changed | Input.Submitted) -> None:
        """
        Takes events matching Input.Changed and Input.Submitted events, and
        checks if input is valid. If the user presses enter (Input.Submitted),
        and the input is valid, we also press the button for them.
        """
        new_cluster_button = self.get_widget_by_id("new-cluster-button")

        if event.validation_result.is_valid:
            # if result is valid, enable the submit button
            new_cluster_button.disabled = False

            # if the user pressed enter, we also press the submit button ✨
            if isinstance(event, Input.Submitted):
                new_cluster_button.action_press()
        else:
            # if result is not valid, notify the user why
            self.notify("\n".join(event.validation_result.failure_descriptions),
                        timeout=8,
                        severity="warning",
                        title="⚠️ Input Validation Error\n")

            # and disable the submit button
            new_cluster_button.disabled = True

    @on(Button.Pressed)
    def button_pressed(self, event: Button.Pressed) -> None:
        """
        get pressed button (Button.Pressed event) and change current screen to
        the k8s distro config screen
        """
        self.app.current_cluster = self.get_widget_by_id("cluster-name-input").value
        self.app.action_request_distro_cfg()
