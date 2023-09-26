#!/usr/bin/env python3.11
from smol_k8s_lab.utils.tui.app_widgets.init_values_widget import InitValuesWidget
from smol_k8s_lab.utils.tui.app_widgets.argocd_widgets import ArgoCDAppProjInputs
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widget import Widget
from textual.widgets import Input, Button
from textual.widgets.selection_list import Selection


class AddAppInput(Widget):
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
        parent_app.cfg['apps'][underscore_app_name] = {
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

        # add this app to the possible invalid inputs
        parent_app.invalid_app_inputs[underscore_app_name] = []

        # creates a new hidden app inputs view for the new application
        inputs = VerticalScroll(
                AppInputs(
                    underscore_app_name,
                    parent_app.cfg['apps'][underscore_app_name]
                    ),
                id=f"{underscore_app_name}-inputs"
                )

        inputs.display = False
        parent_app.app.get_widget_by_id("app-inputs-pane").mount(inputs)

        # adds selection to the app selection list
        selection_list = parent_app.get_widget_by_id("selection-list-of-apps")
        selection_list.add_option(Selection(underscore_app_name.replace("_", "-"),
                                            underscore_app_name,
                                            True))
        input.value = ""


class AppInputs(Widget):
    """
    Display inputs for given smol-k8s-lab supported application
    """
    def __init__(self, app_name: str, metadata: dict) -> None:
        self.app_name = app_name
        self.metadata = metadata
        super().__init__()

    def compose(self) -> ComposeResult:
        yield InitValuesWidget(self.app_name, self.metadata.get('init', None))
        yield ArgoCDAppProjInputs(self.app_name, self.metadata['argo'])
