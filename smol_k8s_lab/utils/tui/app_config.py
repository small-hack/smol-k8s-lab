#!/usr/bin/env python3.11
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Input, Label, Static, Switch, Button
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

        if init or secret_keys:
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
                        key_label = secret_key.replace("_", " ")

                        # create input
                        input_class = f"app-secret-key-input {self.app_name}"
                        input_keys = {"placeholder": placeholder_grammar(key_label),
                                      "classes": input_class,
                                      "name": secret_key}
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
                                      "classes": f"app-init-input {self.app_name}"}
                        if init_value:
                            input_keys['value'] = init_value

                        # create the input row
                        container_class = f"app-input-row {self.app_name}"
                        with Horizontal(classes=container_class):
                            label_class = f"app-input-label {self.app_name}"
                            yield Label(f"{init_key}: ", classes=label_class)
                            yield Input(**input_keys)

        # standard values to source an argo cd app from an external repo
        with Container(classes=f"{self.app_name} argo-config-container"):
            yield Label("Advanced Argo CD App Configuration",
                        classes=f"{self.app_name} argo-config-header")

            for key in ['repo', 'path', 'ref', 'namespace']:
                yield Horizontal(Label(f"{key}:",
                                       classes=f"{self.app_name} argo-config-label"),
                                 Input(placeholder=f"Please enter a {key}",
                                       value=argo_params[key],
                                       name=key,
                                       classes=f"{self.app_name} argo-config-input"),
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
                            value=", ".join(namespaces),
                            classes=f"{self.app_name} argo-config-input")

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
                            classes=f"{self.app_name} argo-config-input")

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

    @on(Input.Changed)
    def update_base_yaml(self, event: Input.Changed) -> None:
        input = event.input
        parent_app_yaml = input.ancestors[-1].usr_cfg['apps'][self.app_name]
        if "argo-config-input" in input.classes:
            if "," in input.value:
                values = input.value.replace(" ","").split(",")
                parent_app_yaml['argo'][input.name] = values
            else:
                parent_app_yaml['argo'][input.name] = input.value
        elif "app-secret-key-input" in input.classes:
            parent_app_yaml['argo']['secret_keys'][input.name] = input.value
        elif "app-init-input" in input.classes:
            parent_app_yaml['init']['values'][input.name] = input.value




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
