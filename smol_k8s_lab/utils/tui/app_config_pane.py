#!/usr/bin/env python3.11
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Label, Static, Switch, Input, TabbedContent


class ArgoCDAppInputs(Static):
    """
    Display inputs for given smol-k8s-lab supported application
    """
    def __init__(self, app_name: str, metadata: dict) -> None:
        self.app_name = app_name
        self.metadata = metadata
        super().__init__()

    def compose(self) -> ComposeResult:
        argo_params = self.metadata['argo']
        secret_keys = argo_params.get('secret_keys', None)
        init = self.metadata.get('init', False)

        # make a pretty title with an init switch for the app to configure
        s_class = f"app-init-switch-and-labels-row {self.app_name}"
        with Container(classes=s_class):
            yield Label(self.app_name.replace('_', ' ').title(),
                        classes="app-label")

            yield Label("Initialize: ", classes="app-init-switch-label")

            if init:
                init_enabled = init.get('enabled', False)
                switch = Switch(value=init_enabled,
                                id=f"{self.app_name}-init-switch",
                                classes="app-init-switch")
            else:
                switch = Switch(animate=False,
                                classes="disabled-app-init-switch")
                switch.tooltip = f"Initialization not supported for {self.app_name}"
            yield switch

        if init and secret_keys:
            # container for all inputs associated with one app
            app_inputs_class = f"{self.app_name} app-all-inputs-container"
            inputs_container = Container(id=f"{self.app_name}-init-inputs",
                                         classes=app_inputs_class)
            if not init_enabled:
                inputs_container.display = False

            with inputs_container:
                # iterate through the app's secret keys
                for secret_key, value in secret_keys.items():
                    key_label = secret_key.replace("_", " ")

                    # create input
                    input_keys = {"placeholder": placeholder_grammar(key_label),
                                  "classes": f"app-input {self.app_name}"}
                    if value:
                        input_keys['value'] = value

                    # create the input row
                    secret_label = Label(f"{key_label}:",
                                         classes=f"app-input-label {self.app_name}")
                    secret_label.tooltip = "added to k8s AppSet Plugin secret"
                    yield Horizontal(secret_label, Input(**input_keys),
                                     classes=f"app-input-row {self.app_name}")

                # these are special values that are only set up via
                # smol-k8s-lab and do not live in a secret on the k8s cluster
                init_values = init.get('values', None)
                if init_values:
                    for init_key, init_value in init_values.items():
                        # create input
                        input_keys = {"placeholder": placeholder_grammar(init_key),
                                      "classes": f"app-input {self.app_name}"}
                        if value:
                            input_keys['value'] = init_value

                        # create the input row
                        container_class = f"app-input-row {self.app_name}"
                        with Horizontal(classes=container_class):
                            label_class = f"app-input-label {self.app_name}"
                            yield Label(f"{init_key}: ", classes=label_class)
                            yield Input(**input_keys)

        # standard values to source an argo cd app from an external repo
        with Container(classes=f"{self.app_name} argo-config-container"):
            yield Label("Advanced Argo CD Parameter Configuration",
                        classes=f"{self.app_name} argo-config-header")

            for key in ['repo', 'path', 'ref', 'namespace']:
                yield Horizontal(Label(f"{key}:",
                                       classes=f"{self.app_name} argo-config-label"),
                                 Input(placeholder=f"Please enter a {key}",
                                       value=argo_params[key],
                                       classes=f"{self.app_name} argo-config-input"),
                                 classes=f"{self.app_name} argo-config-row")

    @on(Switch.Changed)
    @on(TabbedContent.TabActivated)
    def show_or_hide_init_inputs(self, event: Switch.Changed) -> None:
        truthy_value = event.value
        app = event.switch.id.split("-init-switch")[0]
        app_inputs = self.get_widget_by_id(f"{app}-init-inputs")
        app_inputs.display = truthy_value


def placeholder_grammar(key: str):
    article = ""

    # make sure this isn't a plural key
    plural = key.endswith('s')

    # create a gramatically corrrect placeholder
    if key.startswith(('o','a','e')) and not plural:
        article = "an"
    elif not plural:
        article = "a"

    # if this is plural
    if plural:
        return f"enter comma seperated list of {key}"
    else:
        return f"enter {article} {key}"
