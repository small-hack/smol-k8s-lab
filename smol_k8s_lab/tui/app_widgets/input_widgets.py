# smol-k8s-lab libraries
from smol_k8s_lab.tui.util import (placeholder_grammar,
                                   check_for_required_env_vars,
                                   create_sanitized_list)

# external libraries
from ruamel.yaml import CommentedSeq
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid
from textual.validation import Length
from textual.widgets import Input, Label, Static, Collapsible, Button


class SmolK8sLabCollapsibleInputsWidget(Static):
    """
    modal screen with sensitive inputs
    for argocd that are passed to the argocd appset secrets plugin helm chart
    """
    BINDINGS = [Binding(key="b,escape,q",
                        key_display="b",
                        action="app.pop_screen",
                        description="Back")]

    def __init__(self,
                 app_name: str,
                 title: str,
                 collapsible_id: str,
                 inputs: dict = {},
                 tooltips: dict = {},
                 sensitive_inputs: bool = False,
                 check_env_for_input: bool = False,
                 add_fields_button: bool = False) -> None:

        self.app_name = app_name
        self.title = title
        self.inputs = inputs
        self.sensitive = sensitive_inputs
        self.check_env_for_input = check_env_for_input
        # iterate through the values to create inputs for sensitive values
        if self.sensitive and self.check_env_for_input:
            self.inputs, _ = check_for_required_env_vars(
                    self.app_name,
                    self.app.cfg['apps'][self.app_name]
                    )
        self.tooltips = tooltips
        self.add_fields_button = add_fields_button
        self.collapsible_id = collapsible_id

        super().__init__()

    def compose(self) -> ComposeResult:
        with Collapsible(collapsed=False, title=self.title, id=self.collapsible_id):
            with Grid(classes="collapsible-updateable-grid"):
                if self.inputs:
                    for key, value in self.inputs.items():
                        yield self.generate_row(key, value)

    def on_mount(self) -> None:
        """
        update the grid for all new inputs
        """
        if self.add_fields_button:
            self.query_one(".collapsible-updateable-grid").mount(
                    Button("➕ new field"))


    def generate_row(self, key: str, value: str = "") -> Grid:
        """
        add a new row of keys to pass to an argocd app
        """
        key_label = key.replace("_", " ")

        # create input
        input_keys = {"placeholder": placeholder_grammar(key_label),
                      "name": key,
                      "password": self.sensitive,
                      "id": "-".join([self.app_name, key, "input"]),
                      "validators": [Length(minimum=2)]}

        # only give an initial value if one was found in the yaml or env var
        if value:
            # handle ruamel commented sequence (dict from yaml with comments)
            if isinstance(value, CommentedSeq) or isinstance(value, list):
                if isinstance(value[0], str):
                    sequence_value = ", ".join(value)

                elif isinstance(value[0], list):
                    # we grab value[0] because ruamel.yaml's CommentedSeq is weird
                    sequence_value = ", ".join(value[0])

                # reassign value if this is a CommentedSeq for validation later on
                value = sequence_value

            input_keys["value"] = value

        # add all the input_keys dictionary as args to Input widget
        input = Input(**input_keys)

        # make sure Input widget has a tooltip
        tooltip = self.tooltips.get(key, None)
        if not tooltip:
            if self.sensitive:
                tooltip = (f"To avoid needing to fill {key} in manually, "
                           "you can export an env var")
            else:
                tooltip = (f"Enter a {key} for {self.app_name}.")

        # special metallb tooltip
        if self.app_name == "metallb":
            tooltip += (" Be sure the ip addresses you enter already have DNS "
                        "entries for any apps you'd like to deploy.")

        input.tooltip = tooltip

        # immediately validate to get a pink border if input value is invalid
        input.validate(value)

        # create and return the Label + Input row
        return Grid(Label(f"{key_label}:", classes="input-label"),
                    input,
                    classes="app-input-row")

    @on(Input.Changed)
    def input_validation(self, event: Input.Changed) -> None:
        if event.validation_result.is_valid:
            input = event.input
            if self.sensitive and self.check_env_for_input:
                self.app.sensitive_values[self.app_name][input.name] = input.value
            else:
                parent_yaml = self.app.cfg['apps'][self.app_name]['init']['values']

                if event.validation_result.is_valid:
                    if self.app_name == "metallb" or "," in input.value:
                        parent_yaml[input.name] = create_sanitized_list(input.value)
                    else:
                        parent_yaml[input.name] = input.value

                    self.app.write_yaml()
        else:
            if self.app.bell_on_error:
                self.app.bell()
            # if result is not valid, notify the user why
            self.notify("\n".join(event.validation_result.failure_descriptions),
                        severity="warning",
                        title="⚠️ Input Validation Error\n")
