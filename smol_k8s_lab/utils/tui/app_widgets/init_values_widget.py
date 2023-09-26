#!/usr/bin/env python3.11
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.validation import Length
from textual.widget import Widget
from textual.widgets import Input, Label, Switch
from . import placeholder_grammar


class InitValuesWidget(Widget):
    def __init__(self, app_name: str, init: dict) -> None:
        self.app_name = app_name
        self.init = init
        super().__init__()

    def compose(self) -> ComposeResult:
        # container for all inputs associated with one app
        app_inputs_class = f"{self.app_name} app-all-inputs-container"
        inputs_container = Container(id=f"{self.app_name}-init-inputs",
                                     classes=app_inputs_class)

        # make a pretty title with an init switch for the app to configure
        s_class = f"app-init-switch-and-labels-row {self.app_name}"
        with Container(classes=s_class):
            init_lbl = Label("Initialization", classes="initialization-label")
            init_lbl.tooltip = ("if supported, smol-k8s-lab will perform a "
                                "one-time initial setup of this app")
            yield init_lbl

            yield Label("Enabled: ", classes="app-init-switch-label")

            if not self.init:
                switch = Switch(value=False,
                                id=f"{self.app_name}-init-switch",
                                classes="app-init-switch")

                switch.tooltip = ("Initialization for {self.app_name} is [i]not[/]"
                                  " supported by smol-k8s-lab at this time")
                switch.disabled = True
                switch.animate = False
            else:
                init_enabled = self.init.get('enabled', False)

                switch = Switch(value=init_enabled,
                                id=f"{self.app_name}-init-switch",
                                classes="app-init-switch")

                if not init_enabled:
                    inputs_container.display = False

            yield switch

        if self.init:
            with inputs_container:
                # these are special values that are only set up via
                # smol-k8s-lab and do not live in a secret on the k8s cluster
                init_values = self.init.get('values', None)
                if init_values:
                    for init_key, init_value in init_values.items():
                        yield self.generate_init_row(init_key, init_value)

    def generate_init_row(self, init_key: str, init_value: str) -> None:
        # create input
        input_keys = {"placeholder": placeholder_grammar(init_key),
                      "classes": f"app-init-input {self.app_name}",
                      "validators": [Length(minimum=2)],
                      "name": init_key}
        if init_value:
            input_keys['value'] = init_value

        # create the input row
        label_class = f"app-input-label {self.app_name}"
        label = Label(f"{init_key}: ", classes=label_class)
        label.tooltip = (
                "Init value for special one-time setup of this app."
                " This value is [i]not[/i] stored in a secret for "
                "later reference by Argo CD.")

        container_class = f"app-input-row {self.app_name}"

        input = Input(**input_keys)
        if input.validate(init_value):
            invalid_inputs = self.ancestors[-1].invalid_app_inputs
            app_inputs = invalid_inputs.get(self.app_name, None)
            if app_inputs:
                app_inputs.append(init_key)
            else:
                invalid_inputs[self.app_name] = [init_key]

        return Horizontal(label, input, classes=container_class)

    @on(Switch.Changed)
    def show_or_hide_init_inputs(self, event: Switch.Changed) -> None:
        truthy_value = event.value
        # wrapped in a try except as some init apps don't need inputs
        app_inputs = self.get_widget_by_id(f"{self.app_name}-init-inputs")
        app_inputs.display = truthy_value

        parent_app_yaml = event.switch.ancestors[-1].cfg['apps'][self.app_name]
        parent_app_yaml['init']['enabled'] = truthy_value

        event.switch.ancestors[-1].write_yaml()

    @on(Input.Changed)
    def update_base_yaml(self, event: Input.Changed) -> None:
        input = event.input
        parent_app = input.ancestors[-1]
        parent_app_yaml = parent_app.cfg['apps'][self.app_name]
        # if this is an init input
        if "app-init-input" in input.classes:
            parent_app_yaml['init']['values'][input.name] = input.value

        # Updating the main app with k8s app that has validation failed
        if event.validation_result:
            invalid_inputs = parent_app.invalid_app_inputs
            if not event.validation_result.is_valid:
                invalid_inputs[self.app_name].append(input.name)
            else:
                if input.name in invalid_inputs[self.app_name]:
                    invalid_inputs[self.app_name].remove(input.name)

        self.app.write_yaml()
