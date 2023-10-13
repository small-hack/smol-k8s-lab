#!/usr/bin/env python3.11
from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Grid
from textual.widget import Widget
from textual.widgets import Input, Button, Label
from textual.suggester import SuggestFromList

KEY_SUGGESTIONS = SuggestFromList((
        "podsPerCore",
        "maxPods",
        "node-labels",
        "featureGates"
        ))

VALUE_SUGGESTIONS = SuggestFromList(("ingress-ready=true"))

kubelet_help = (
        "Add key value pairs to pass to your [steel_blue][u][link=https://kubernetes.io/docs/"
        "reference/command-line-tools-reference/kubelet/]kubelet[/link][/u][/]"
        " [steel_blue][u][link=https://kubernetes.io/docs/reference/config-api/"
        "kubelet-config.v1beta1/]configuration[/link][/u][/]."
        )

class KubeletConfig(Widget):
    """
    Widget to take Extra Args for Kubelet Config section
    """

    def __init__(self, distro: str, kubelet_extra_args: list = []) -> None:
        self.distro = distro
        self.kubelet_extra_args = kubelet_extra_args
        super().__init__()

    def compose(self) -> ComposeResult:
        with Grid(classes=f"{self.distro} kubelet-config-container"):
            yield Label(kubelet_help,
                        classes="help-text")
            with VerticalScroll(classes=f"kubelet-config-scroll {self.distro}",
                                id=f"{self.distro}-kubelet-config-container"):

                if self.kubelet_extra_args:
                    for key, value in self.kubelet_extra_args.items():
                        yield self.generate_row(key, str(value))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        get pressed button add or delete button and act on it
        """
        # lets you delete a kubelet-arg row
        parent_row = event.button.parent
        input_key = parent_row.children[0].value
        if input_key:
            yaml = self.app.cfg['k8s_distros']
            yaml[self.distro]['kubelet_extra_args'].pop(input_key)
        parent_row.remove()

    @on(Input.Submitted)
    def update_base_yaml(self, event: Input.Changed) -> None:
        # get the parent row and two input fields
        parent_row = event.input.parent
        input_key = parent_row.children[0].value
        input_value = parent_row.children[1].value
        try:
            input_value = int(input_value)
        except ValueError:
            pass

        # grab the user's yaml file from the parent app
        root_yaml = self.app.cfg['k8s_distros'][self.distro]
        extra_args = root_yaml['kubelet_extra_args']

        if "kubelet-arg-input-key" in event.input.classes:
            if event.input.value not in extra_args.keys():
                extra_args[event.input.value] = input_value

        elif "kubelet-arg-input-value" in event.input.classes:
            # convert this to an int if its possible
            try:
                int_value = int(event.input.value)
                extra_args[input_key] = int_value
            # if value can't an int, just set it normally
            except ValueError:
                extra_args[input_key] = event.input.value

        self.app.write_yaml()

    def generate_row(self, param: str = "", value: str = "") -> Grid:
        """
        generate a new input field set
        """
        # base class for all the below object
        row_class = f"{self.distro} kubelet-arg-input"

        # label for input field
        label = Label(param + ":", classes="input-label")

        # second input field
        param_value_input_args = {"classes": f"{row_class}-value",
                                  "placeholder": "kubelet parameter value",
                                  "suggester": VALUE_SUGGESTIONS}
        if value:
            param_value_input_args["value"] = value
        param_value_input = Input(**param_value_input_args)

        # delete button for each row
        del_button = Button("🚮", classes=f"{row_class}-del-button")
        del_button.tooltip = "Delete this kubelet parameter"

        return Grid(label, param_value_input, del_button,
                    classes="label-input-delete-row")
