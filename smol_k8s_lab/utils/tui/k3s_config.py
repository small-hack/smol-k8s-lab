#!/usr/bin/env python3.11
from textual.app import ComposeResult, Widget
from textual.containers import Container, VerticalScroll
from textual.widgets import Input, Button
from textual.suggester import SuggestFromList

SUGGESTIONS = SuggestFromList((
       "--disable=traefik",
       "--secrets-encryption",
       "--flannel-backend=wireguard-native",
       ))


class K3sConfig(Widget):
    """
    k3s args config
    """

    def __init__(self, distro: str, k3s_args: list = []) -> None:
        self.k3s_args = k3s_args
        self.distro = distro
        super().__init__()

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes=f"{self.distro} k3s-arg-scroll"):
            if self.k3s_args:
                for arg in self.k3s_args:
                    yield self.generate_row(arg)

            yield Button("➕ Add New Arg",
                         classes=f"{self.distro} k3s-arg-add-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        get pressed button and act on it
        """
        button_classes = event.button.classes

        # lets you delete a k3s-arg row
        if "k3s-arg-del-button" in button_classes:
            event.button.parent.remove()

        # lets you add a new k3s config row
        if "k3s-arg-add-button" in button_classes:
            event.button.parent.mount(self.generate_row(),
                                      before=event.button)

    def generate_row(self, value: str = ""):
        """
        create a new input row
        """
        row_args = {"placeholder": "enter an extra arg for k3s",
                    "classes": f"{self.distro} k3s-arg-input",
                    "suggester": SUGGESTIONS}
        if value:
            row_args["value"] = value

        return Container(Input(**row_args),
                         Button("🚮", classes="k3s-arg-del-button"),
                         classes="k3s-arg-row")
