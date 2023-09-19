#!/usr/bin/env python3.11
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll, Horizontal
from textual.widgets import Label, Static, Switch, Input, Collapsible
from smol_k8s_lab.constants import DEFAULT_APPS


class ArgoCDAppInputs(Static):
    """
    dialog screen to show help text
    """
    def compose(self) -> ComposeResult:
        # this is a vertically scrolling container for all the inputs
        with VerticalScroll(id='app-inputs'):
            for app, metadata in DEFAULT_APPS.items():
                argo_params = metadata['argo']
                secret_keys = argo_params.get('secret_keys', None)
                init = metadata.get('init', False)

                # make a pretty title for the app to configure
                s_class = f"app-init-switch-and-labels-row {app}"
                with Container(classes=s_class):
                    app_title = app.replace('_', ' ').title()
                    yield Label(app_title, classes="app-label")

                    yield Label("Initialize: ",
                                classes="app-init-switch-label")

                    if init:
                        init_enabled = init.get('enabled', False)
                        yield Switch(value=init_enabled,
                                     id=f"{app}-init-switch",
                                     classes="app-init-switch")
                    else:
                        disabled_switch = Switch(animate=False,
                                                 classes="disabled-app-init-switch")
                        yield disabled_switch

                if init and secret_keys:
                    # container for all inputs associated with one app
                    app_inputs_class = f"{app} app-all-inputs-container"
                    inputs_container = Container(id=f"{app}-inputs",
                                                 classes=app_inputs_class)
                    if not init_enabled:
                        inputs_container.display = False

                    with inputs_container:
                        # iterate through the app's secret keys
                        for secret_key, value in secret_keys.items():
                            secret_label = secret_key.replace("_", " ")
                            # create a gramatically corrrect placeholder
                            if secret_key.startswith(('o','a','e')):
                                article = "an"
                            else:
                                article = "a"
                            placeholder = f"enter {article} {secret_label}"

                            # create input variable
                            input_classes = f"app-input {app}"
                            if value:
                                app_input = Input(placeholder=placeholder,
                                                  value=value,
                                                  classes=input_classes)
                            else:
                                app_input = Input(placeholder=placeholder,
                                                  classes=input_classes)

                            # create the input row
                            container_class = f"app-input-row {app}"
                            with Horizontal(classes=container_class):
                                label_class = f"app-input-label {app}"
                                yield Label(f"{secret_label}: ",
                                            classes=label_class)
                                yield app_input

                with Container(classes=f"{app}"):
                    for key in ['repo', 'path', 'ref', 'namespace']:
                        with Horizontal(classes=f"{app} argo-config-row"):
                            yield Label(key, classes=f"{app} argo-config-label")
                            yield Input(placeholder=f"Please enter a {key}",
                                        value=argo_params[key],
                                        classes=f"{app} argo-config-input")


    def on_mount(self) -> None:
        # styling for the select-apps tab - configure apps container - right
        app_config_title = "⚙️ [green]Configure inital parameters for each selected app"
        self.get_widget_by_id("app-inputs").border_title = app_config_title

    @on(Switch.Changed)
    def show_or_hide_init_inputs(self, event: Switch.Changed) -> None:
        truthy_value = event.value
        app = event.switch.id.split("-init-switch")[0]
        app_inputs = self.get_widget_by_id(f"{app}-inputs")
        app_inputs.display = truthy_value
        DEFAULT_APPS[app]['init']['enabled'] = truthy_value
