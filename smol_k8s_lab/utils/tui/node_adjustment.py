#!/usr/bin/env python3.11
from textual import on
from textual.app import ComposeResult, Widget
from textual.containers import Horizontal
from textual.widgets import Label, Input, Pretty
from textual.validation import Function, Number, ValidationResult, Validator


NO_NODE_TXT = (
        "nodes cannot be adjusted for k3s at this time, but it is on our road "
        "map to support extra nodes in the future. In the meantime, you can "
        "still follow the instructions at [link="
        "https://docs.k3s.io/quick-start#install-script]"
        "docs.k3s.io/quick-start#install-script[/link] to install a new node"
        )


class NodeAdjustmentBox(Widget):
    """
    widget for node ajustment
    """

    def __init__(self,
                 distro: str,
                 control_plane_nodes: int = 1,
                 worker_nodes: int = 0) -> None:
        # this is just to take a few variables for class organizing
        self.distro = distro
        self.control_plane_nodes = control_plane_nodes
        self.worker_nodes = worker_nodes
        super().__init__()

    def compose(self) -> ComposeResult:
        node_class = f"{self.distro} nodes-input"

        node_input_row = Horizontal(classes=f"{node_class}-row")

        if self.distro == "k3s":
            node_input_row.tooltip = NO_NODE_TXT
            disabled = True
        else:
            disabled = False

        with node_input_row:
            yield Label("control plane:", classes=f"{node_class}-label")
            yield Input(value=self.control_plane_nodes,
                        placeholder='1',
                        classes=f"{node_class}-control-input",
                        validators=[Number(minimum=1, maximum=50)],
                        disabled=disabled)

            worker_label = Label("workers:", classes=f"{node_class}-label")
            worker_label.tooltip = ("If workers is 0, the control plane acts "
                                    "as the worker.")
            yield worker_label
            yield Input(value=self.worker_nodes,
                        placeholder='0',
                        classes=f"{node_class}-worker-input",
                        validators=[Number(minimum=0, maximum=100)],
                        disabled=disabled)

    def on_mount(self) -> None:
        node_row = self.query_one(".nodes-input-row")
        node_row.border_title = "[green]🖥️ Adjust how many of each node type to deploy"
