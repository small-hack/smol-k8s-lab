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
                                     "max-pods",
                                     "system-reserved",
                                     "kube-reserved"))

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
        super().__init__(id=f"kubelet-config-{distro}")

    def compose(self) -> ComposeResult:
        with Grid(id=f"kubelet-config-container-{self.distro}",
                  classes="kubelet-config-container"):
            yield Label(kubelet_help, classes="help-text")
            yield VerticalScroll(id=f"kubelet-config-scroll-{self.distro}",
                                 classes="kubelet-config-scroll")

    def on_mount(self) -> None:
        if self.kubelet_extra_args:
            if self.distro == "kind":
                for key, value in self.kubelet_extra_args.items():
                    self.generate_row(key, str(value))

            if self.distro == "k3s":
                for item in self.kubelet_extra_args:
                    if "kube-reserved" in item:
                        key = "kube-reserved"
                        value = item.replace("kube-reserved=", "")

                    elif "system-reserved" in item:
                        key = "system-reserved"
                        value = item.replace("system-reserved=", "")

                    else:
                        key_value_pair = item.split('=')
                        key = key_value_pair[0]
                        value = key_value_pair[1]

                    self.generate_row(key, str(value))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        get pressed button add or delete button and act on it
        """
        # lets you delete a kubelet-arg row
        parent_row = event.button.parent
        input_key = parent_row.children[1].name

        app_yaml = self.app.cfg['k8s_distros'][self.distro]

        if self.distro == "kind":
            kind_args = app_yaml['kubelet_extra_args']

            if input_key and kind_args.get(input_key, False):
                kind_args.pop(input_key)
                self.app.write_yaml()

            parent_row.remove()

        # this isn't beautiful, but should get the job done
        if self.distro == "k3s":
            k3s_args = app_yaml['k3s_yaml']['kubelet-arg']
            pop_item = None

            if input_key:
                for item in k3s_args:
                    if input_key in item:
                        pop_item = item

                if pop_item:
                    k3s_args.pop[pop_item]
                    self.app.write_yaml()

                parent_row.remove()

    @on(Input.Submitted)
    @on(Input.Changed)
    def update_base_yaml(self, event: Input.Changed | Input.Submitted) -> None:
        if event.validation_result.is_valid:
            # grab the user's yaml file from the parent app
            distro_cfg = self.app.cfg['k8s_distros'][self.distro]

            # kind uses a different schema than k3s for kubelet args. uses dict
            if self.distro == "kind":
                args = distro_cfg['kubelet_extra_args']
                # convert this to an int if its possible
                try:
                    int_value = int(event.input.value)
                    args[event.input.name] = int_value
                # if value can't an int, just set it normally. uses list
                except ValueError:
                    args[event.input.name] = event.input.value

            # k3s uses a list
            if self.distro == "k3s":
                args = distro_cfg["k3s_yaml"]['kubelet-arg']

                kubelet_arg = f"{event.input.name}={event.input.value}"
                if isinstance(args, list) and kubelet_arg not in args:
                    args.append(kubelet_arg)
                elif not isinstance(args, list) and kubelet_arg not in args:
                    args = [f"{event.input.name}={event.input.value}"]

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

        self.get_widget_by_id(f"kubelet-config-scroll-{self.distro}").mount(
                Grid(label, param_value_input, del_button,
                     classes="label-input-delete-row")
                )
