#!/usr/bin/env python3.11
from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Grid
from textual.widget import Widget
from textual.widgets import Input, Button, Label
from textual.suggester import SuggestFromList

SUGGESTIONS = SuggestFromList((
        "apiServerPort",
        "apiServerAddress",
        "disableDefaultCNI",
        "ipFamily",
        "kubeProxyMode",
        "podSubnet",
        "serviceSubnet"
        ))

VALUE_SUGGESTIONS = SuggestFromList(("true"))


class KindNetworkingConfig(Widget):
    """
    Extra Args for kind networking Config section
    """

    def __init__(self, kind_neworking_params: list = []) -> None:
        self.kind_neworking_params = kind_neworking_params
        super().__init__()

    def compose(self) -> ComposeResult:
        with Grid(id="kind-networking-container"):
            # kind networking config section
            help = ("Add key value pairs to kind networking config. If [dim][#C1FF87]"
                    "cilium[/][/] is enabled, we pass in disableDefaultCNI=true.")
            yield Label(help, classes="help-text")

            with VerticalScroll(classes="kind-networking-config-scroll"):
                if self.kind_neworking_params:
                    for key, value in self.kind_neworking_params.items():
                        yield self.generate_row(key, str(value))
                else:
                    yield self.generate_row()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        get pressed button add or delete button and act on it
        """
        parent_row = event.button.parent
        input_key = parent_row.children[0].value
        if input_key:
            self.app.cfg['k8s_distros']['kind']['networking_args'].pop(input_key)
        parent_row.remove()

    @on(Input.Submitted)
    def update_base_yaml(self, event: Input.Changed) -> None:
        # get the parent row and two input fields
        parent_row = event.input.parent
        input_key = parent_row.children[0].value
        input_value = parent_row.children[1].value

        # grab the user's yaml file from the parent app
        extra_args = self.app.cfg['k8s_distros']['kind']['networking_args']

        if "kind-networking-input-key" in event.input.classes:
            if event.input.value not in extra_args.keys():
                extra_args[event.input.value] = input_value

        elif "kind-networking-input-value" in event.input.classes:
            # if they answer with a boolean, make sure it's written out correctly
            if event.input.value == 'true':
                extra_args[input_key] = True
            elif event.input.value == 'false':
                extra_args[input_key] = False
            else:
                extra_args[input_key] = event.input.value

        self.app.write_yaml()

    def generate_row(self, param: str = "", value: str = "") -> Grid:
        """
        generate a new input field set
        """
        # base class for all the below object
        row_class = "kind-networking-input"

        # label for input field
        label = Label(param.replace("_", " ") + ":", classes="input-label")

        # second input field
        param_value_input_args = {"classes": f"{row_class}-value",
                                  "placeholder": "kind networking param value",
                                  "suggester": VALUE_SUGGESTIONS}
        if value:
            param_value_input_args["value"] = value
        param_value_input = Input(**param_value_input_args)

        # delete button for each row
        del_button = Button("🚮", classes=f"{row_class}-del-button")
        del_button.tooltip = "Delete this kind networking parameter"

        return Grid(label, param_value_input, del_button,
                    classes="label-input-delete-row")
