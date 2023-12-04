#!/usr/bin/env python3.11

# smol-k8s-lab libraries
from smol_k8s_lab.tui.app_widgets.argocd_widgets import (ArgoCDApplicationConfig,
                                                         ArgoCDProjectConfig)
from smol_k8s_lab.tui.app_widgets.input_widgets import SmolK8sLabCollapsibleInputsWidget
from smol_k8s_lab.tui.util import placeholder_grammar, create_sanitized_list

# external libraries
from ruamel.yaml import CommentedSeq
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.validation import Length
from textual.widgets import Input, Label, Button, Switch, Static


class AppInputs(Static):
    """
    Display inputs for given smol-k8s-lab supported application
    """
    def __init__(self, app_name: str, config_dict: dict) -> None:
        self.app_name = app_name
        self.argo_params = config_dict['argo']
        self.init = config_dict.get('init', None)
        super().__init__()

    def compose(self) -> ComposeResult:

        # standard values to source an argo cd app from an external repo
        with VerticalScroll(id=f"{self.app_name}-argo-config-container",
                            classes="argo-config-container"):

            if self.init:
                yield InitValues(self.app_name, self.init)

            yield ArgoCDApplicationConfig(self.app_name, self.argo_params)

            secret_keys = self.argo_params.get('secret_keys', False)
            if not secret_keys and isinstance(secret_keys, bool):
                self.app.cfg['apps'][self.app_name]['secret_keys'] = {}
                self.app.write_yaml()

            yield AppsetSecretValues(self.app_name, secret_keys)

            # argocd project configuration
            yield Label("Advanced Argo CD Project Configuration",
                        classes=f"{self.app_name} argo-config-header")

            yield ArgoCDProjectConfig(self.app_name, self.argo_params['project'])


class InitValues(Static):
    """
    widget to take special smol-k8s-lab init values
    """
    CSS_PATH = "../css/apps_init_config.tcss"

    def __init__(self, app_name: str, init_dict: dict) -> None:
        self.app_name = app_name
        self.init_enabled = init_dict['enabled']
        self.init_values = init_dict.get('values', None)
        self.sensitive_values = init_dict.get('sensitive_values', None)

        super().__init__()

    def compose(self) -> ComposeResult:
        # container for all inputs associated with one app
        # make a pretty title with an init switch for the app to configure
        with Container(classes=f"app-init-switch-and-labels-row {self.app_name}"):
            init_lbl = Label("Initialization", classes="initialization-label")
            init_lbl.tooltip = ("if supported, smol-k8s-lab will perform a "
                                "one-time initial setup of this app")
            yield init_lbl

            yield Label("Enabled: ", classes="app-init-switch-label")

            switch = Switch(value=self.init_enabled,
                            id=f"{self.app_name}-init-switch",
                            classes="app-init-switch")
            yield switch

        inputs_container = Container(
                id=f"{self.app_name}-init-inputs",
                classes=f"{self.app_name} init-inputs-container"
                )
        if self.init_values and not self.init_enabled:
            inputs_container.display = False

        if self.init_values or self.sensitive_values:
            with inputs_container:
                cid = f"{self.app_name}"
                if self.init_values:
                    # these are special values that are only set up via
                    # smol-k8s-lab and do not live in a secret on the k8s cluster
                    init_vals =  SmolK8sLabCollapsibleInputsWidget(
                            app_name=self.app_name,
                            title="Init Values",
                            collapsible_id=f"{cid}-init-values-collapsible",
                            inputs=self.init_values,
                            sensitive_inputs=False)

                    init_vals.tooltip = (
                                "Init values for special one-time setup of "
                                f"{self.app_name}. These values are [i]not[/i] "
                                "stored in a secret for later reference  by Argo CD."
                                )
                    yield init_vals

                if self.sensitive_values:
                    self.app.check_for_env_vars(self.app_name,
                                                self.app.cfg['apps'][self.app_name])
                    sensitive_init_vals = SmolK8sLabCollapsibleInputsWidget(
                            app_name=self.app_name,
                            title="Sensitive Init Values",
                            collapsible_id=f"{cid}-sensitive-init-values-collapsible",
                            inputs=self.app.sensitive_values[self.app_name],
                            sensitive_inputs=True)

                    sensitive_init_vals.tooltip = (
                                "Sensitive Init values for special one-time setup of "
                                f"{self.app_name}. These values can also be passed in"
                                " via environment variables."
                                )
                    yield sensitive_init_vals

    @on(Switch.Changed)
    def show_or_hide_init_inputs(self, event: Switch.Changed) -> None:
        """
        if user pressed the init switch, we hide the inputs
        """
        truthy_value = event.value

        if self.init_values and event.switch.id == f"{self.app_name}-init-switch":
           app_inputs = self.get_widget_by_id(f"{self.app_name}-init-inputs")
           app_inputs.display = truthy_value

           self.app.cfg['apps'][self.app_name]['init']['enabled'] = truthy_value
           self.app.write_yaml()


class AppsetSecretValues(Static):
    """
    widget to take secret key values to pass to argocd appset secret plugin helm
    chart. These values are saved to the base yaml in:
    self.app.cfg['apps'][app]['secret_keys']
    """
    def __init__(self, app_name: str, secret_keys: dict = {}) -> None:
        self.app_name = app_name
        self.secret_keys = secret_keys
        super().__init__()

    def compose(self) -> ComposeResult:
        # secret keys
        label =  Label("Template values for Argo CD ApplicationSet ",
                       classes="secret-key-divider",
                       id=f"{self.app_name}-secret-key-divider")
        label.tooltip = ("🔒[i]optional[/]: Added to k8s secret for the Argo CD "
                         "ApplicationSet Secret Plugin Generator.")
        yield label

        if self.secret_keys:
            # iterate through the app's secret keys
            for secret_key, value in self.secret_keys.items():
                yield self.generate_secret_key_row(secret_key, value)
        else:
            help = ("smol-k8s-lab doesn't include any templated values for"
                    " this app, but you can add some below if you're using "
                    "a custom Argo CD App repo.")
            yield Label(help, classes="secret-key-help-text")

        key_input = Input(placeholder="new key name",
                          id=f"{self.app_name}-new-secret",
                          classes="new-secret-input",
                          validators=Length(minimum=2))

        key_input.tooltip = ("🔒key name to pass to the Argo CD ApplicationSet"
                             " Secret Plugin Generator for templating non-"
                             "sensitive values such as hostnames.")

        button = Button("➕", id=f"{self.app_name}-new-secret-button",
                        classes="new-secret-button")
        yield Horizontal(button, key_input, classes="app-input-row")

    def generate_secret_key_row(self, secret_key: str, value: str = "") -> None:
        """
        add a new row of secret keys to pass to the argocd app
        """
        # root app yaml
        apps_yaml = self.app.cfg['apps'][self.app_name]
        apps_yaml['argo']['secret_keys'][secret_key] = value

        key_label = secret_key.replace("_", " ")

        # create input
        input_class = f"app-secret-key-input {self.app_name}"
        input_keys = {"placeholder": placeholder_grammar(key_label),
                      "classes": input_class,
                      "name": secret_key,
                      "validators": [Length(minimum=2)]}

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

        input = Input(**input_keys)
        input.validate(value)

        # create the input row
        secret_label = Label(f"{key_label}:",
                             classes=f"input-label {self.app_name}")

        return Horizontal(secret_label, input,
                          classes=f"app-input-row {self.app_name}")

    @on(Input.Changed)
    def update_base_yaml(self, event: Input.Changed) -> None:
        if event.validation_result.is_valid:
            input = event.input
            if input.id != f"{self.app_name}-new-secret":
                if "," in input.value:
                    value = create_sanitized_list(input.value)
                else:
                    value = input.value

                parent_app_yaml = self.app.cfg['apps'][self.app_name]
                parent_app_yaml['argo']['secret_keys'][input.name] = value

                self.app.write_yaml()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        add a new input row for secret stuff
        """
        inputs_box = self.app.get_widget_by_id(f"{self.app_name}-argo-config-container")
        input = self.get_widget_by_id(f"{self.app_name}-new-secret")

        if len(input.value) > 1:
            # add new secret key row
            inputs_box.mount(
                    self.generate_secret_key_row(input.value),
                    after=self.get_widget_by_id(f"{self.app_name}-secret-key-divider")
                    )
            # clear the input field after we're created the new row and
            # updated the yaml
            input.value = ""
