#!/usr/bin/env python3.11
from textual import on
from textual.app import ComposeResult, Widget
from textual.containers import Grid
from textual.widgets import Label, Input
from textual.validation import Number


NO_NODE_TXT = (
        "nodes cannot be adjusted for k3s at this time, but it is on our road "
        "map to support extra nodes in the future. In the meantime, you can "
        "still follow the instructions at [link="
        "https://docs.k3s.io/quick-start#install-script]"
        "docs.k3s.io/quick-start#install-script[/link] to add a new node"
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
        with Grid(classes=f"{self.distro} nodes-box"):
            node_class = f"{self.distro} nodes-input"

            with Grid(id="nodes-input-row"):
                if self.distro == 'k3s':
                    disabled = True
                    tooltip = "Field cannot be edited for k3s 😥"
                else:
                    disabled = False
                    tooltip = "Press [gold3]↩ Enter[/] to save"

                # control plane input row
                with Grid(classes="node-input-column"):
                    label = Label("control plane:", classes=f"{node_class}-label")
                    label.tooltip = (
                            "The control plane manages the worker nodes and the "
                            "Pods in the cluster. You have to have at least one."
                            )
                    yield label

                    control_input = Input(value=self.control_plane_nodes,
                                          id=f"{self.distro}-control-plane-nodes-input",
                                          placeholder='1',
                                          classes=f"{node_class}-control-input",
                                          name="control_plane_nodes",
                                          validators=[Number(minimum=1, maximum=50)],
                                          disabled=disabled)
                    control_input.tooltip = tooltip
                    yield control_input

                # workers input row
                with Grid(classes="node-input-column worker-node-row"):
                    worker_label = Label("workers:", classes=f"{node_class}-label")
                    worker_label.tooltip = (
                            "The worker node(s) host the Pods that are the components "
                            "of the application workload. If workers is 0, the "
                            "control plane acts as the worker as well."
                            )
                    yield worker_label

                    worker_input = Input(value=self.worker_nodes,
                                         placeholder='0',
                                         classes=f"{node_class}-worker-input",
                                         name="worker_nodes",
                                         id=f"{self.distro}-worker-nodes-input",
                                         validators=[Number(minimum=0, maximum=100)],
                                         disabled=disabled)
                    worker_input.tooltip = tooltip
                    yield worker_input

    def on_mount(self) -> None:
        """
        styling for the border
        """
        node_row = self.get_widget_by_id("nodes-input-row")
        node_row.border_title = ("[i]Adjust[/] how many of each "
                                 "[#C1FF87]node type[/] to deploy")

    @on(Input.Changed)
    def update_parent_yaml(self, event: Input.Changed):
        """
        update the base parent app yaml with worker/control plane node count
        only if input is valid, and the distro is not k3s
        """
        if event.validation_result.is_valid and self.distro != "k3s":
            distro_cfg = self.app.cfg['k8s_distros'][self.distro]['nodes']

            if event.input.name == "worker_nodes":
                distro_cfg['workers'] = int(event.input.value)
                self.app.write_yaml()

            if event.input.name == "control_plane_nodes":
                distro_cfg['control_plane'] = int(event.input.value)
                self.app.write_yaml()
