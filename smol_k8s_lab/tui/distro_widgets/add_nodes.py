#!/usr/bin/env python3.11
from smol_k8s_lab.constants import HOME_DIR

from os.path import join
from textual import on
from textual.app import ComposeResult, Widget
from textual.containers import Grid
from textual.widgets import Label, Input, Select
from textual.widgets.selection_list import Selection


class AddNodesBox(Widget):
    """
    widget for adding new nodes to a local k3s cluster
    """
    def __init__(self, nodes: dict = {}, id: str = "") -> None:
        # this is just to take a few variables for class organizing
        if not nodes:
            self.nodes = {"example": {"ssh_key": "id_rsa",
                                      "node_type": "worker"}}
        else:
            self.nodes = nodes
        super().__init__(id=id)

    def compose(self) -> ComposeResult:
        with Grid(id="add-nodes-box"):
            for host, metadata in self.nodes.items():
                yield self.add_node(host, metadata)

    def on_mount(self) -> None:
        """
        styling for the border
        """
        node_row = self.get_widget_by_id("add-nodes-box")
        node_row.border_title = ("[i]Add[/] additional [#C1FF87]remote nodes[/]"
                                 " to join to local cluster")

    def add_node(self, node: str = "", node_dict: dict = {}) -> None:
        """ 
        add a node input section for k3s
        """
        node_class = "nodes-input"
        hostname = node
        all_disabled = False
        tooltip = "Press [gold3]↩ Enter[/] to save"

        # hostname label and input
        host_label = Label("host:", classes=f"{node_class}-label nodes-input-label")
        host_label.tooltip = (
                "The hostname or ip address of the node you'd like to "
                "join to the cluster"
                )
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

        # node type label and input
        node_type_label = Label("node_type:", classes=f"{node_class}-label nodes-input-label")
        node_type_label.tooltip = ("The type for this Kubernetes node. "
                         "Choose between worker or control_plane.")

        node_type = node_dict.get('node_type', 'worker')
        node_type_input = Select.from_values(
                ['worker', 'control_plane'],
                name="node_type",
                value=node_type,
                classes=f"{hostname}-node-type"
                )

        node_type_input.tooltip = tooltip
        if all_disabled:
            node_type_input.disabled = True

        # ssh key label and input
        ssh_key_label = Label("ssh_key:", classes=f"{node_class}-label nodes-input-label")
        ssh_key_label.tooltip = (
                "The SSH key to use to connect to the other node. This "
                f"defaults to {join(HOME_DIR, ".ssh/id_rsa")}"
                )

        ssh_key = node_dict.get('ssh_key', "id_rsa")
        ssh_key_input = Input(value=ssh_key,
                              name="ssh_key",
                              placeholder='',
                              classes=f"{hostname}-ssh-key",
                              )
        ssh_key_input.tooltip = tooltip
        if all_disabled:
            ssh_key_input.disabled = True

        return Grid(host_label, host_input, node_type_label, node_type_input,
                    ssh_key_label, ssh_key_input, id=f"{hostname}-row",
                    classes="k3s-node-input-row")

    @on(Input.Changed)
    def update_parent_yaml(self, event: Input.Changed):
        """
        update the base parent app yaml with worker/control plane node count
        only if input is valid, and the distro is not k3s
        """
        if event.validation_result:
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
