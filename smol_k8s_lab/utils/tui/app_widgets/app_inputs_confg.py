#!/usr/bin/env python3.11
from . import placeholder_grammar
from .new_app_modal import NewAppModalScreen
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll, Grid
from textual.validation import Length
from textual.widgets import Input, Label, Button, Switch, Static
from textual.widgets.selection_list import Selection


ARGO_TOOLTIPS = {'repo': 'URL to a git repository where you have k8s manifests ' + \
                         '(including Argo resources) to deploy',
                 'path': 'path in repo to resources you want to deploy. ' +
                         'Trailing slash is important.',
                 'ref': 'branch or tag to point to in the repo',
                 'namespace': 'k8s namespace to deploy the Argo CD App to'}


class AddAppInput(Static):
    """
    Button for launching a modal to add new apps
    """

    def compose(self) -> ComposeResult:
        new_button = Button("✨New App", id="new-app-button")
        new_button.tooltip = "Click to add your own Argo CD app from an existing repo"
        with Grid(id="new-app-button-box"):
            yield new_button

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        get pressed "new app" button
        """
        def get_new_app(app_response):
            app_name = app_response[0]
            app_description = app_response[1]

            if app_name and app_description:
                self.create_new_app_in_yaml(app_name, app_description)

        self.app.push_screen(NewAppModalScreen(["argo-cd"]), get_new_app)

    def create_new_app_in_yaml(self, app_name: str, app_description: str = "") -> None:
        underscore_name = app_name.replace(" ", "_").replace("-", "_")

        # updates the base user yaml
        self.app.cfg['apps'][underscore_name] = {
            "enabled": True,
            "description": app_description,
            "argo": {
                "secret_keys": {},
                "repo": "",
                "path": "",
                "ref": "",
                "namespace": "",
                "project": {
                    "source_repos": [""],
                    "destination": {
                        "namespaces": ["argocd"]
                        }
                    }
                }
            }

        # adds selection to the app selection list
        apps = self.app.get_widget_by_id("selection-list-of-apps")
        apps.add_option(Selection(underscore_name.replace("_", "-"),
                                  underscore_name, True))

        # scroll down to the new app
        apps.action_last()

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

            # this has to live here because it is awful
            with Container(classes="init-widget"):
                yield InitValues(self.app_name, self.init)

            yield Label("Advanced Argo CD App Configuration",
                        classes=f"{self.app_name} argo-config-header")

            for key, value in ARGO_TOOLTIPS.items():
                input = Input(placeholder=f"Please enter a {key}",
                              value=self.argo_params[key],
                              name=key,
                              validators=[Length(minimum=2)],
                              id=f"{self.app_name}-{key}",
                              classes=f"{self.app_name} argo-config-input")
                input.validate(self.argo_params[key])

                argo_label = Label(f"{key}:",
                                   classes=f"{self.app_name} argo-config-label")
                argo_label.tooltip = value

                yield Horizontal(argo_label, input,
                                 classes=f"{self.app_name} argo-config-row")

            # secret keys
            label =  Label("Template values to pass to Argo CD ApplicationSet ",
                           classes="secret-key-divider",
                           id=f"{self.app_name}-secret-key-divider")
            label.tooltip = ("🔒Added to k8s secret for the Argo CD "
                             "ApplicationSet Secret Plugin Generator")
            yield label

            secret_keys = self.argo_params.get('secret_keys', None)

            if secret_keys:
                # iterate through the app's secret keys
                for secret_key, value in secret_keys.items():
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
                label = Label("source repos:",
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
            inputs_box = self.get_widget_by_id(f"{self.app_name}-argo-config-container")
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

    def generate_secret_key_row(self, secret_key: str, value: str = "") -> None:
        """
        add a new row of secret keys to pass to the argocd app
        """
        # root app yaml
        apps_yaml = self.ancestors[-1].cfg['apps'][self.app_name]
        apps_yaml['argo']['secret_keys'][secret_key] = ""

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
        input.validate(value)

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

            # if project source repo (that allowed to be used for gitops by apps
            # in project)
            if "argo-proj-repo" in input.classes:
                values = input.value.replace(" ","").split(",")
                parent_app_yaml['argo']['project'][input.name] = values

            # if project destination namespace (that argo app is allowed to use)
            elif "argo-proj-ns" in input.classes:
                values = input.value.replace(" ","").split(",")
                parent_app_yaml['argo']['project']['destination'][input.name] = values

            # otherwise it's probably just a normal app input
            else:
                parent_app_yaml['argo'][input.name] = input.value

        # if this is a secret key input
        elif "app-secret-key-input" in input.classes:
            parent_app_yaml['argo']['secret_keys'][input.name] = input.value

        self.app.write_yaml()


class InitValues(Static):
    CSS_PATH = "../css/apps_init_config.tcss"
    def __init__(self, app_name: str, init_dict: dict) -> None:
        self.app_name = app_name
        self.init = init_dict

        if self.init:
            self.init_values = self.init.get('values', None)
        else:
            self.init_values = None
        super().__init__()

    def compose(self) -> ComposeResult:
        # container for all inputs associated with one app
        app_inputs_class = f"{self.app_name} init-inputs-container"
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

                switch.tooltip = (f"Initialization for {self.app_name} is [i]not[/]"
                                  " supported by smol-k8s-lab at this time")
                switch.disabled = True
                switch.animate = False
            else:
                init_enabled = self.init.get('enabled', False)

                switch = Switch(value=init_enabled,
                                id=f"{self.app_name}-init-switch",
                                classes="app-init-switch")

                if self.init_values and not init_enabled:
                    inputs_container.display = False

            yield switch

        if self.init_values:
            # these are special values that are only set up via
            # smol-k8s-lab and do not live in a secret on the k8s cluster
            with inputs_container:
                for init_key, init_value in self.init_values.items():
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
        label_value = init_key.replace("_"," ") + ":"
        label = Label(label_value, classes=f"app-init-label {self.app_name}")
        label.tooltip = (
                "Init value for special one-time setup of this app."
                " This value is [i]not[/i] stored in a secret for "
                "later reference by Argo CD.")

        container_class = f"app-init-row {self.app_name}"

        input = Input(**input_keys)
        input.validate(init_value)

        return Grid(label, input, classes=container_class)

    @on(Switch.Changed)
    def show_or_hide_init_inputs(self, event: Switch.Changed) -> None:
        truthy_value = event.value

        if self.init_values:
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

        if not event.validation_result:
            # if this is an init input
            if "app-init-input" in input.classes:
                parent_app_yaml['init']['values'][input.name] = input.value

        self.app.write_yaml()
