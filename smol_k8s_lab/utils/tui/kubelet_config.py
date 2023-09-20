#!/usr/bin/env python3.11
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Horizontal
from textual.widgets import Input, Button, Static
from textual.suggester import SuggestFromList

SUGGESTIONS = SuggestFromList((
        "podsPerCore",
        "maxPods",
        "node-labels",
        "featureGates"
        ))

VALUE_SUGGESTIONS = SuggestFromList(("ingress-ready=true"))


class KubeletConfig(Static):
    """
    Extra Args for Kubelet Config section
    """

    def __init__(self, distro: str, kubelet_extra_args: list = []) -> None:
        self.distro = distro
        self.kubelet_extra_args = kubelet_extra_args
        super().__init__()

    def compose(self) -> ComposeResult:
        # kubelet config section
        with VerticalScroll(classes=f"kubelet-config-scroll {self.distro}",
                            id=f"{self.distro}-kubelet-config-container"):

            if self.kubelet_extra_args:
                for key, value in self.kubelet_extra_args.items():
                    yield self.generate_row(key, str(value))

            yield Button("➕ Add New Arg",
                         classes=f"{self.distro} kubelet-arg-add-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        get pressed button add or delete button and act on it
        """
        button_classes = event.button.classes

        # lets you delete a kubelet-arg row
        if "kubelet-arg-input-del-button" in button_classes:
            parent_row = event.button.parent
            parent_row.remove()

        # add a new row of kubelet arg inputs before the add button
        if "kubelet-arg-add-button" in button_classes:
            parent_container = event.button.parent
            parent_container.mount(self.generate_row(), before=event.button)

    def generate_row(self, param: str = "", value: str = "") -> None:
        """ 
        generate a new input field set
        """
        # base class for all the below object
        row_class = f"{self.distro} kubelet-arg-input"

        # first input field
        param_input_args = {"placeholder": "optional kubelet parameter",
                            "classes": f"{row_class}-key",
                            "suggester": SUGGESTIONS}
        if param:
            param_input_args["value"] = param
        param_input = Input(**param_input_args)

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

        return Horizontal(param_input, param_value_input, del_button,
                          classes=f"{row_class}-row")
