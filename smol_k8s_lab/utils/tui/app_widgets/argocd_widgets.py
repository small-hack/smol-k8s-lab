#!/usr/bin/env python3.11
from . import placeholder_grammar
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.validation import Length
from textual.widget import Widget
from textual.widgets import Input, Label, Button


ARGO_TOOLTIPS = {'repo': 'URL to a git repository where you have k8s manifests ' + \
                         '(including Argo resources) to deploy',
                 'path': 'path in repo to resources you want to deploy',
                 'ref': 'branch or tag to point to in the repo',
                 'namespace': 'k8s namespace to deploy the Argo CD App in'}

class ArgoCDAppProjInputs(Widget):
    """
    Display inputs for given smol-k8s-lab supported application
    """
    def __init__(self, app_name: str, argo: dict) -> None:
        self.app_name = app_name
        self.argo_params = argo
        super().__init__()

    def compose(self) -> ComposeResult:
        argo_inputs = VerticalScroll(id=f"{self.app_name}-inputs",
                                     classes="single-app-inputs")
        argo_inputs.display = False
        with argo_inputs:
            secret_keys = self.argo_params.get('secret_keys', None)

            # standard values to source an argo cd app from an external repo
            with Container(classes=f"{self.app_name} argo-config-container"):
                yield Label("Advanced Argo CD App Configuration",
                            classes=f"{self.app_name} argo-config-header")

                for key, value in ARGO_TOOLTIPS.items():
                    input = Input(placeholder=f"Please enter a {key}",
                                  value=self.argo_params[key],
                                  name=key,
                                  validators=[Length(minimum=2)],
                                  id=f"{self.app_name}-{key}",
                                  classes=f"{self.app_name} argo-config-input")
                    input.tooltip = value

                    if input.validate(self.argo_params[key]):
                        invalid_inputs = self.ancestors[-1].invalid_app_inputs
                        app_inputs = invalid_inputs.get(self.app_name, None)
                        if app_inputs:
                            app_inputs.append(key)
                        else:
                            invalid_inputs[self.app_name] = [key]

                    yield Horizontal(
                            Label(f"{key}:",
                                  classes=f"{self.app_name} argo-config-label"),
                                  input,
                                  classes=f"{self.app_name} argo-config-row")

                # secret keys
                label =  Label("Template values to pass to Argo CD ApplicationSet ",
                               classes="secret-key-divider")
                label.tooltip = ("🔒Added to k8s secret for the Argo CD "
                                 "ApplicationSet Secret Plugin Generator")
                yield label
                if secret_keys:
                    # iterate through the app's secret keys
                    for secret_key, value in secret_keys.items():
                        yield self.generate_secret_key_row(secret_key, value)
                else:
                    help = ("smol-k8s-lab doesn't include any templated values for"
                            " this app, but you can add some below if you're using "
                            "a custom Argo CD App repo.")
                    yield Label(help, classes="app-help-label")

                key_input = Input(placeholder="new key name",
                                  id=f"{self.app_name}-new-secret",
                                  classes="new-secret-input")

                key_input.tooltip = ("🔒key name to pass to the Argo CD ApplicationSet"
                                     " Secret Plugin Generator for templating non-"
                                     "sensitive values such as hostnames.")

                yield Horizontal(Button("➕",
                                        id=f"{self.app_name}-new-secret-button",
                                        classes="new-secret-button"),
                                 key_input,
                                 classes="app-input-row")

                # argocd project configuration
                yield Label("Advanced Argo CD App Project Configuration",
                            classes=f"{self.app_name} argo-config-header")

                # row for project destination namespaces
                with Horizontal(classes=f"{self.app_name} argo-config-row"):
                    label = Label("namespaces:",
                                  classes=f"{self.app_name} argo-config-label")
                    label.tooltip = "Comma seperated list of namespaces"
                    yield label

                    n_spaces = self.argo_params["project"]["destination"]["namespaces"]
                    classes = f"{self.app_name} argo-config-input argo-proj-ns"
                    yield Input(placeholder="Enter comma seperated list of namespaces",
                                name="namespaces",
                                value=", ".join(n_spaces),
                                classes=classes)

                # row for project source repos
                with Horizontal(classes=f"{self.app_name} argo-config-row"):
                    label = Label("source_repos:",
                                  classes=f"{self.app_name} argo-config-label")
                    label.tooltip = "Comma seperated list of project source repos"
                    yield label

                    repos = self.argo_params["project"]["source_repos"]
                    classes = f"{self.app_name} argo-config-input argo-proj-repo"
                    yield Input(placeholder="Please enter source_repos",
                                value=", ".join(repos),
                                name="source_repos",
                                classes=classes)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        add a new input row for secret stuff
        """
        if event.button.id == f"{self.app_name}-new-secret-button":
            inputs_box = self.get_widget_by_id(f"{self.app_name}-init-inputs")
            input = self.get_widget_by_id(f"{self.app_name}-new-secret").value

            if input:
                # root app yaml
                apps_yaml = self.app.ancestors[-1].cfg['apps'][self.app_name]
                apps_yaml['argo']['secret_keys'][input] = ""

                # add new secret key row
                inputs_box.mount(self.generate_secret_key_row(input), before=0)

    def generate_secret_key_row(self, secret_key: str, value: str = "") -> None:
        """
        add a new row of secret keys to pass to the argocd app
        """
        key_label = secret_key.replace("_", " ")

        # create input
        input_class = f"app-secret-key-input {self.app_name}"
        input_keys = {"placeholder": placeholder_grammar(key_label),
                      "classes": input_class,
                      "name": secret_key,
                      "validators": [Length(minimum=2)]}
        if value:
            input_keys['value'] = value

        input = Input(**input_keys)

        if input.validate(value):
            invalid_inputs = self.ancestors[-1].invalid_app_inputs
            app_inputs = invalid_inputs.get(self.app_name, None)

            if app_inputs:
                app_inputs.append(secret_key)
            else:
                invalid_inputs[self.app_name] = [secret_key]

        # create the input row
        secret_label = Label(f"{key_label}:",
                             classes=f"app-input-label {self.app_name}")
        return Horizontal(secret_label, input,
                          classes=f"app-input-row {self.app_name}")

    @on(Input.Changed)
    def update_base_yaml(self, event: Input.Changed) -> None:
        input = event.input
        parent_app = input.ancestors[-1]
        parent_app_yaml = parent_app.cfg['apps'][self.app_name]

        # if this is an Argo CD app/project config input
        if "argo-config-input" in input.classes:

            # if this is a project source repo
            if "argo-proj-repo" in input.classes:
                values = input.value.replace(" ","").split(",")
                parent_app_yaml['argo']['project'][input.name] = values

            # if this is a project destination namespace
            elif "argo-proj-ns" in input.classes:
                values = input.value.replace(" ","").split(",")
                parent_app_yaml['argo']['project']['destination'][input.name] = values

            # otherwise it's probably just a normal app input
            else:
                parent_app_yaml['argo'][input.name] = input.value

        # if this is a secret key input
        elif "app-secret-key-input" in input.classes:
            parent_app_yaml['argo']['secret_keys'][input.name] = input.value

        # Updating the main app with k8s app that has validation failed
        if event.validation_result:
            invalid_inputs = parent_app.invalid_app_inputs
            if not event.validation_result.is_valid:
                invalid_inputs[self.app_name].append(input.name)
            else:
                if input.name in invalid_inputs[self.app_name]:
                    invalid_inputs[self.app_name].remove(input.name)

        self.app.write_yaml()
