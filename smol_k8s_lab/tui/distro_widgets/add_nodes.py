#!/usr/bin/env python3.11
from smol_k8s_lab.constants import HOME_DIR

from os.path import join
from textual import on
from textual.app import ComposeResult, Widget
from textual.containers import Grid
from textual.widgets import Label, Input, Select


class AddNodesBox(Widget):
    """
    widget for node ajustment
    """
    def __init__(self,
                 nodes: list = [{"example": {"ssh_key": "id_rsa",
                                            "node_type": "worker"}}]) -> None:
        # this is just to take a few variables for class organizing
        self.nodes = nodes
        super().__init__()

    def compose(self) -> ComposeResult:
        with Grid(classes="add-nodes-box"):
            for node in self.nodes:
                self.add_node(node)

    def on_mount(self) -> None:
        """
        styling for the border
        """
        node_row = self.get_widget_by_id("nodes-input-row")
        node_row.border_title = ("[i]Add[/] additional nodes "
                                 "[#C1FF87]node type[/] to deploy")

    def add_node(self,
                 node_dict: dict = {"example": {"ssh_key": "id_rsa",
                                                "node_type": "worker"}}) -> None:
        node_class = "nodes-input"
        hostname = node_dict.keys()[0]

        with Grid(id=f"{hostname}-row"):
            all_disabled = False
            tooltip = "Press [gold3]↩ Enter[/] to save"

            # hostname label and input
            label = Label("host:", classes=f"{node_class}-label")
            label.tooltip = (
                    "The hostname or ip address of the node you'd like to "
                    "join to the cluster"
                    )
            yield label

            if hostname != "example":
                host_input = Input(value=hostname,
                                   name="host",
                                   placeholder='hostname or ip address',
                                   classes=f"{hostname}-host",
                                  )
            else:
                host_input = Input(name="host",
                                   placeholder='hostname or ip address',
                                   classes=f"{hostname}-host",
                                  )
                all_disabled = True
            host_input.tooltip = tooltip
            yield host_input

            # node type label and input
            label = Label("node_type:", classes=f"{node_class}-label")
            label.tooltip = ("The type for this Kubernetes node. "
                             "Choose between worker or control_plane.")
            yield label

            node_type = node_dict[hostname].get('node_type', 'worker')
            node_type_input = Select(
                    name="node_type",
                    value=node_type,
                    classes=f"{hostname}-node-type"
                    ).from_values(['worker', 'control_plane'])

            node_type_input.tooltip = tooltip
            if all_disabled:
                node_type_input.disabled = True
            yield node_type_input

            # ssh key label and input
            label = Label("ssh_key:", classes=f"{node_class}-label")
            label.tooltip = (
                    "The SSH key to use to connect to the other node. This "
                    f"defaults to {join(HOME_DIR, ".ssh/id_rsa")}"
                    )
            yield label

            ssh_key = node_dict[hostname]['ssh_key']
            ssh_key_input = Input(value=ssh_key,
                                  name="ssh_key",
                                  placeholder='',
                                  classes=f"{hostname}-ssh-key",
                                  )
            ssh_key_input.tooltip = tooltip
            if all_disabled:
                ssh_key_input.disabled = True
            yield ssh_key_input

    @on(Input.Changed)
    def update_parent_yaml(self, event: Input.Changed):
        """
        update the base parent app yaml with worker/control plane node count
        only if input is valid, and the distro is not k3s
        """
        if event.validation_result.is_valid:
            distro_cfg = self.app.cfg['k8s_distros']['k3s']['nodes']

            if event.input.name == "host":
                try:
                    host_index = distro_cfg.index(event.input.value)
                # if the host doesn't exist in config yet
                except ValueError:
                    distro_cfg.append({event.input.value: {"ssh_key": "id_rsa",
                                                           "node_type": "worker"}})
                # if no error
                else:
                    distro_cfg[host_index] = {
                            event.input.value: {"ssh_key": "id_rsa",
                                                "node_type": "worker"}
                            }

                self.app.write_yaml()
