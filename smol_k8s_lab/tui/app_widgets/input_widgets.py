# smol-k8s-lab libraries
from smol_k8s_lab.tui.util import (placeholder_grammar,
                                   check_for_required_env_vars,
                                   create_sanitized_list)

# external libraries
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid
from textual.validation import Length
from textual.widgets import Input, Label, Static, Collapsible


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
                 tooltips: list = [],
                 sensitive_inputs: bool = False,
                 check_env_for_input: bool = False) -> None:

        self.app_name = app_name
        self.title = title
        self.inputs = inputs
        self.sensitive = sensitive_inputs
        self.check_env_for_input = check_env_for_input
        self.tooltips = tooltips
        self.collapsible_id = collapsible_id

        super().__init__()

    def compose(self) -> ComposeResult:
        with Collapsible(collapsed=False, title=self.title, id=self.collapsible_id):
            # iterate through the values to create inputs for sensitive values
            if self.sensitive and self.check_env_for_input:
                self.sensitive_info_dict, _ = check_for_required_env_vars(
                        self.app_name,
                        self.app.cfg['apps'][self.app_name]
                        )
                for key, value in self.sensitive_info_dict.items():
                    yield self.generate_row(key=key, value=value)

            if self.inputs:
                for key, value in self.inputs.items():
                    yield self.generate_row(key=key, value=value)

    def generate_row(self, key: str, value: str = "", tooltip: str = "") -> Grid:
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

        if value:
            input_keys["value"] = value

        input = Input(**input_keys)
        if not tooltip:
            tooltip = (
                    f"To avoid needing to fill {key} in manually, "
                    "you can export an env var"
                    )

        if self.app_name == "metallb":
            tooltip += (" Be sure the ip addresses you enter already have DNS "
                        "entries for any apps you'd like to deploy.")

        input.tooltip = tooltip

        input.validate(value)

        # create the input row
        secret_label = Label(f"{key_label}:", classes="input-label")

        return Grid(secret_label, input, classes="app-input-row")

    @on(Input.Changed)
    def input_validation(self, event: Input.Changed) -> None:
        if event.validation_result.is_valid:
            input = event.input
            if self.sensitive and self.check_env_for_input:
                self.app.sensitive_values[self.app_name][input.name] = input.value
            else:
                parent_yaml = self.app.cfg['apps'][self.app_name]['init']['values']

                if event.validation_result.is_valid:
                    if self.app_name == "metallb":
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
