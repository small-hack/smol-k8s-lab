#!/usr/bin/env python3.11
from textual.app import ComposeResult, Widget
from textual.containers import Container, VerticalScroll
from textual.widgets import Input, Button


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
                k3s_class = f'{self.distro} k3s-arg'

                for arg in self.k3s_args:
                    placeholder = "enter an extra arg for k3s"

                    with Container(classes=f'{k3s_class}-row'):
                        yield Input(value=arg,
                                    placeholder=placeholder,
                                    classes=f"{k3s_class}-input")
                        yield Button("🚮",
                                     classes=f"{k3s_class}-del-button")

            yield Button("➕ Add New Arg",
                         classes=f"{k3s_class}-add-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        get pressed button and act on it
        """
        button_classes = event.button.classes

        # lets you delete a k3s-arg row
        if "k3s-arg-del-button" in button_classes:
            parent_row = event.button.parent
            parent_row.remove()

        # lets you add a new k3s config row
        if "k3s-arg-add-button" in button_classes:
            parent_container = event.button.parent
            placeholder = "enter an extra arg for k3s"
            parent_container.mount(Container(
                Input(placeholder=placeholder, classes="k3s-arg-input"),
                Button("🚮", classes="k3s-arg-del-button"),
                classes="k3s-arg-row"
                ), before=event.button)
