#!/usr/bin/env python3.11
from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Grid
from textual.suggester import SuggestFromList
from textual.validation import Length
from textual.widget import Widget
from textual.widgets import Input, Button, Label

VALUE_SUGGESTIONS = SuggestFromList(("ingress-ready=true",
                                     "pods-per-core",
                                     "resolv-conf",
                                     "max-pods"))

kubelet_help = (
        "Add key value pairs to pass to your [steel_blue][b][link=https://kubernetes.io/docs/"
        "reference/command-line-tools-reference/kubelet/]kubelet[/][/][/]"
        " [steel_blue][b][link=https://kubernetes.io/docs/reference/config-api/"
        "kubelet-config.v1beta1/]configuration[/][/][/]."
        )

class KubeletConfig(Widget):
    """
    Widget to take Extra Args for kind Kubelet Config
    """

    def __init__(self, distro: str, kubelet_extra_args: list = []) -> None:
        self.distro = distro
        self.kubelet_extra_args = kubelet_extra_args
        super().__init__()

    def compose(self) -> ComposeResult:
        with Grid(id="kubelet-config-container"):
            yield Label(kubelet_help, classes="help-text")
            yield VerticalScroll(id="kubelet-config-scroll")

    def on_mount(self) -> None:
        if self.kubelet_extra_args:
            for key, value in self.kubelet_extra_args.items():
                self.generate_row(key, str(value))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        get pressed button add or delete button and act on it
        """
        # lets you delete a kubelet-arg row
        parent_row = event.button.parent
        input_key = parent_row.children[1].name
        app_yaml = self.app.cfg['k8s_distros'][self.distro]['kubelet_extra_args']
        if input_key and app_yaml.get(input_key, False):
            app_yaml.pop(input_key)
            self.app.write_yaml()
        parent_row.remove()

    @on(Input.Submitted)
    @on(Input.Changed)
    def update_base_yaml(self, event: Input.Changed | Input.Submitted) -> None:
        if event.validation_result.is_valid:
            # grab the user's yaml file from the parent app
            args = self.app.cfg['k8s_distros'][self.distro]['kubelet_extra_args']

            # convert this to an int if its possible
            try:
                int_value = int(event.input.value)
                args[event.input.name] = int_value
            # if value can't an int, just set it normally
            except ValueError:
                args[event.input.name] = event.input.value

            self.app.write_yaml()

    def generate_row(self, param: str = "", value: str = "") -> Grid:
        """
        generate a new input field set
        """
        # label for input field
        label = Label(param + ":", classes="input-label")

        # second input field
        param_value_input_args = {"placeholder": "kubelet parameter value",
                                  "suggester": VALUE_SUGGESTIONS,
                                  "validators": Length(minimum=1),
                                  "id": f"kind-kubelet-{param}-input",
                                  "name": param}

        if value:
            param_value_input_args["value"] = value
        param_value_input = Input(**param_value_input_args)

        # delete button for each row
        del_button = Button("🚮", id=f"kind-kubelet-delete-{param}-button")
        del_button.tooltip = "Delete this kubelet parameter"

        self.get_widget_by_id("kubelet-config-scroll").mount(
                Grid(label, param_value_input, del_button,
                     classes="label-input-delete-row")
                )
