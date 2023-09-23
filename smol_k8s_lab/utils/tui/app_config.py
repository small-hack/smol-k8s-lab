#!/usr/bin/env python3.11
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.validation import Length
from textual.widgets import Input, Label, Static, Switch, Button, Rule
from textual.widgets.selection_list import Selection


class ArgoCDNewInput(Static):
    """
    Add new inputs for new application
    """

    def compose(self) -> ComposeResult:
        new_button = Button("[blue]♡ Submit New App[/]", id="new-app-button")
        new_button.tooltip = "Click to add your own Argo CD app from an existing repo"
        yield Input(placeholder="Name of New ArgoCD App",
                    classes="new-app-prompt",
                    name="new-app-name",
                    id="new-app-input")
        with Horizontal(id="new-app-button-box"):
            yield new_button

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        get pressed "new app" button
        """
        input = self.get_widget_by_id("new-app-input")
        app_name = input.value
        underscore_app_name = app_name.replace(" ", "_").replace("-", "_")

        # the main config app
        parent_app = event.button.ancestors[-1]

        # updates the base user yaml
        parent_app.usr_cfg['apps'][underscore_app_name] = {
            "enabled": True,
            "description": "",
            "init": {"enabled": True},
            "argo": {
                "secret_keys": {"hostname": ""},
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

        # creates a new hidden app inputs view for the new application
        inputs = VerticalScroll(
                ArgoCDAppInputs(
                    underscore_app_name,
                    parent_app.usr_cfg['apps'][underscore_app_name]
                    ),
                id=f"{underscore_app_name}-inputs",
                classes="single-app-inputs"
                )
        inputs.display = False
        parent_app.app.get_widget_by_id("app-inputs-pane").mount(inputs)

        # adds selection to the app selection list
        selection_list = parent_app.get_widget_by_id("selection-list-of-apps")
        selection_list.add_option(Selection(underscore_app_name.replace("_", "-"),
                                            underscore_app_name,
                                            True))
        input.value = ""


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
        init = self.metadata.get('init', {"enabled": False})

        # make a pretty title with an init switch for the app to configure
        s_class = f"app-init-switch-and-labels-row {self.app_name}"
        with Container(classes=s_class):
            yield Label("Initialization",
                        classes="app-label")

            yield Label("Enabled: ", classes="app-init-switch-label")

            init_enabled = init.get('enabled', False)
            switch = Switch(value=init_enabled,
                            id=f"{self.app_name}-init-switch",
                            classes="app-init-switch")
            yield switch

        # container for all inputs associated with one app
        app_inputs_class = f"{self.app_name} app-all-inputs-container"
        inputs_container = Container(id=f"{self.app_name}-init-inputs",
                                     classes=app_inputs_class)
        if not init_enabled:
            inputs_container.display = False

        with inputs_container:
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
                                 "Secret Plugin Generator for templating non-sensitive"
                                 " values such as hostnames.")
            yield Horizontal(Button("➕",
                                    id=f"{self.app_name}-new-secret-button",
                                    classes="new-secret-button"),
                             key_input,
                             classes="app-input-row")

            # these are special values that are only set up via
            # smol-k8s-lab and do not live in a secret on the k8s cluster
            init_values = init.get('values', None)
            if init_values:
                yield Rule(classes="init-divider")
                for init_key, init_value in init_values.items():
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
                        self.ancestors[-1].invalid_app_inputs[self.app_name].append(init_key)
                    with Horizontal(classes=container_class):
                        yield label
                        yield input

        # standard values to source an argo cd app from an external repo
        with Container(classes=f"{self.app_name} argo-config-container"):
            yield Label("Advanced Argo CD App Configuration",
                        classes=f"{self.app_name} argo-config-header")

            for key in ['repo', 'path', 'ref', 'namespace']:
                input = Input(placeholder=f"Please enter a {key}",
                              value=argo_params[key],
                              name=key,
                              validators=[Length(minimum=2)],
                              id=f"{self.app_name}-{key}",
                              classes=f"{self.app_name} argo-config-input")
                if input.validate(argo_params[key]):
                    self.ancestors[-1].invalid_app_inputs[self.app_name].append(key)
                yield Horizontal(Label(f"{key}:",
                                       classes=f"{self.app_name} argo-config-label"),
                                 input,
                                 classes=f"{self.app_name} argo-config-row")

            # argocd project configuration
            yield Label("Advanced Argo CD App Project Configuration",
                        classes=f"{self.app_name} argo-config-header")

            # row for project destination namespaces
            with Horizontal(classes=f"{self.app_name} argo-config-row"):
                label = Label("namespaces:",
                              classes=f"{self.app_name} argo-config-label")
                label.tooltip = "Comma seperated list of namespaces"
                yield label

                namespaces = argo_params["project"]["destination"]["namespaces"]
                yield Input(placeholder="Enter comma seperated list of namespaces",
                            name="namespaces",
                            value=", ".join(namespaces),
                            classes=f"{self.app_name} argo-config-input argo-proj-ns")

            # row for project source repos
            with Horizontal(classes=f"{self.app_name} argo-config-row"):
                label = Label("source_repos:",
                              classes=f"{self.app_name} argo-config-label")
                label.tooltip = "Comma seperated list of project source repos"
                yield label

                repos = argo_params["project"]["source_repos"]
                yield Input(placeholder="Please enter source_repos",
                            value=", ".join(repos),
                            name="source_repos",
                            classes=f"{self.app_name} argo-config-input argo-proj-repo")

    @on(Switch.Changed)
    def show_or_hide_init_inputs(self, event: Switch.Changed) -> None:
        truthy_value = event.value
        # wrapped in a try except as some init apps don't need inputs
        try:
            app_inputs = self.get_widget_by_id(f"{self.app_name}-init-inputs")
            app_inputs.display = truthy_value
        except Exception as e:
            if "NoMatches" in str(e):
                pass
        parent_app_yaml = event.switch.ancestors[-1].usr_cfg['apps'][self.app_name]
        parent_app_yaml['init']['enabled'] = truthy_value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        add a new input row for secret stuff
        """
        if event.button.id == f"{self.app_name}-new-secret-button":
            inputs_box = self.get_widget_by_id(f"{self.app_name}-init-inputs")
            input = self.get_widget_by_id(f"{self.app_name}-new-secret").value

            if input:
                # root app yaml
                apps_yaml = event.button.ancestors[-1].usr_cfg['apps'][self.app_name]
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
            self.ancestors[-1].invalid_app_inputs[self.app_name].append(secret_key)

        # create the input row
        secret_label = Label(f"{key_label}:",
                             classes=f"app-input-label {self.app_name}")
        secret_label.tooltip = ("🔒Added to k8s secret for the Argo CD "
                                "ApplicationSet Secret Plugin Generator")
        return Horizontal(secret_label, input,
                          classes=f"app-input-row {self.app_name}")

    @on(Input.Changed)
    def update_base_yaml(self, event: Input.Changed) -> None:
        input = event.input
        parent_app = input.ancestors[-1]
        parent_app_yaml = parent_app.usr_cfg['apps'][self.app_name]

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

        # if this is an init input
        elif "app-init-input" in input.classes:
            parent_app_yaml['init']['values'][input.name] = input.value

        # Updating the main app with k8s app that has validation failed
        if event.validation_result:
            invalid_inputs = parent_app.invalid_app_inputs
            if not event.validation_result.is_valid:
                invalid_inputs[self.app_name].append(input.name)
            else:
                if input.name in invalid_inputs[self.app_name]:
                    invalid_inputs[self.app_name].remove(input.name)

def placeholder_grammar(key: str):
    article = ""

    # make sure this isn't a plural key
    plural = key.endswith('s')

    if key == "address_pool":
        plural = True

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
