#!/usr/bin/env python3.11
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Input, Button, Static


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
        with Container(classes=f"kubelet-config-container {self.distro}",
                       id=f"{self.distro}-kubelet-config-container"):
            # take extra kubelet config args
            row_class = f"{self.distro} kubelet-arg"
            row_container = Horizontal(classes=f"{row_class}-input-row")

            if self.kubelet_extra_args:
                for key, value in self.kubelet_extra_args.items():
                    with row_container:
                        yield Input(value=key,
                                    placeholder="optional kubelet config key arg",
                                    classes=f"{row_class}-input-key")

                        yield Input(value=str(value),
                                    placeholder=key,
                                    classes=f"{row_class}-input-value")

                        yield Button("🚮",
                                     classes=f"{row_class}-del-button")

            yield Button("➕ Add New Arg", classes=f"{row_class}-add-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        get pressed button add or delete button and act on it
        """
        button_classes = event.button.classes

        # lets you delete a kubelet-arg row
        if "kubelet-arg-del-button" in button_classes:
            parent_row = event.button.parent
            parent_row.remove()

        if "kubelet-arg-add-button" in button_classes:
            parent_container = event.button.parent
            row_class = f"{self.distro} kubelet-arg"

            # add a new row of kubelet arg inputs before the add button
            parent_container.mount(Horizontal(
                Input(placeholder="optional kubelet config key arg",
                      classes=f"{row_class}-input-key"),
                Input(placeholder="optional kubelet config key arg",
                      classes=f"{row_class}-input-value"),
                Button("🚮", classes=f"{row_class}-del-button"),
                       classes=f"{row_class}-input-row"),
                before=event.button)

    def on_mount(self) -> None:
        # screen and header styling
        kubelet_title = "➕ [green]Extra Args for Kubelet Config"
        kubelet_cfg = f"{self.distro}-kubelet-config-container"
        self.get_widget_by_id(kubelet_cfg).border_title = kubelet_title
