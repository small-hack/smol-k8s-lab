#!/usr/bin/env python3.11
from smol_k8s_lab.constants import HOME_DIR
from smol_k8s_lab.tui.util import input_field, drop_down
from smol_k8s_lab.tui.distro_widgets.modify_node_modal import NodeModalScreen

from os.path import join
from rich.text import Text
from textual import on
from textual.app import ComposeResult, Widget
from textual.containers import Grid
from textual.widgets import Label, DataTable, Button

placeholder = """Add a node below for something to appear here...
[grey53]
               _____
              /     \\
              vvvvvvv  /|__/|
                 I   /O,O   |
                 I /_____   |     /|/|
                C|/^ ^ ^ \\  |   /oo  |    _//|
                 |^ ^ ^ ^ |W|  |/^^\\ |   /oo |
                  \\m___m__|_|   \\m_m_|   \\mm_|

                "Totoros" (from "My Neighbor Totoro")
                    --- Duke Lee
[/grey53]
"""

class AddNodesBox(Widget):
    """
    widget for adding new nodes to a local k3s cluster
    """
    def __init__(self, nodes: dict = {}, id: str = "") -> None:
        # this is just to take a few variables for class organizing
        self.nodes = nodes
        super().__init__(id=id)

    def compose(self) -> ComposeResult:
        with Grid(id="add-nodes-box"):
            yield Label(placeholder, id="nodes-placeholder")
            yield Label("🖥️ Add a new node", id="new-node-text")
            yield self.add_node_row()

    def on_mount(self) -> None:
        """
        generate nodes table
        """
        if self.nodes:
            self.get_widget_by_id("nodes-placeholder").display = False
            self.generate_nodes_table()

    def generate_nodes_table(self) -> None:
        """ 
        generate a readable table for all the nodes.

        Each row is has a height of 3 and is centered to make it easier to read
        for people with dyslexia
        """
        data_table = DataTable(zebra_stripes=True,
                               id="nodes-data-table",
                               cursor_type="row")

        # then fill in the cluster table
        data_table.add_column(Text("Node", justify="center"))
        data_table.add_column(Text("Type", justify="center"))
        data_table.add_column(Text("SSH Key", justify="center"))
        data_table.add_column(Text("Labels", justify="center"))
        data_table.add_column(Text("Taints", justify="center"))

        for node, metadata in self.nodes.items():
            # labels can be a list or CommentedSeq, so we convert to str
            labels = metadata.get('node_labels', "")
            if not isinstance(labels, str):
                if labels:
                    if len(labels) == 1:
                        labels = labels[0]
                    else:
                        labels = labels.join(",")
                else:
                    labels = ""

            # taints can be a list or CommentedSeq, so we convert to str
            taints = metadata.get('node_taints', "")
            if not isinstance(taints, str):
                if taints:
                    if len(taints) == 1:
                        taints = taints[0]
                    else:
                        taints = taints.join(",")
                else:
                    taints = ""

            row = [node, metadata['node_type'], metadata['ssh_key'], labels, taints]
            # we use an extra line to center the rows vertically 
            styled_row = [Text(str("\n" + cell), justify="center") for cell in row]

            # we add extra height to make the rows more readable
            data_table.add_row(*styled_row, height=3, key=row[0])

        # grid for the cluster data table
        table_grid = Grid(data_table, id="table-grid")

        # the actual little box in the middle of screen
        main_grid = Grid(table_grid, id="node-table-box-grid")

        # modify clusters box title
        main_grid.border_title = ("Select a row to [#ffaff9]modify[/] or [#ffaff9]"
                                  "delete[/] an [i]existing[/] [#C1FF87]node[/]")

        nodes_container = self.get_widget_by_id("add-nodes-box")
        nodes_container.mount(main_grid, before="#new-node-text")

    @on(DataTable.RowHighlighted)
    def node_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """
        check which row was selected to read it aloud
        """
        if self.app.speak_on_focus:
            self.say_row(event.data_table)

    @on(DataTable.RowSelected)
    def node_row_selected(self, event: DataTable.RowSelected) -> None:
        """
        check which row was selected to launch a modal screen to modify or delete it
        """
        if event.data_table.id == "nodes-data-table":
            def update_nodes(response: list = []):
                """
                check if cluster has been deleted
                """
                node = response[0]
                node_metadata = response[1]

                # make sure we actually got anything, because the user may have
                # hit the cancel button
                if node:
                    data_table = self.get_widget_by_id("nodes-data-table")

                    if not node_metadata:
                        data_table.remove_row(node)

                        if data_table.row_count < 1:
                            data_table.remove()
                            self.get_widget_by_id("nodes-placeholder").display = True

                        self.delete_from_parent_yaml(node)

            row_index = event.cursor_row
            row = event.data_table.get_row_at(row_index)

            # get the row's first column (the name of the node) and remove whitespace
            node = row[0].plain.strip()

            # launch modal UI to ask if they'd like to modify or delete a node
            self.app.push_screen(NodeModalScreen(node, self.nodes[node]), update_nodes)

    def update_parent_yaml(self, node_name: str, node_metadata: dict):
        """
        update the base parent app yaml with new nodes
        """
        distro_cfg = self.app.cfg['k8s_distros']['k3s']['nodes']

        # make sure the taints and labels are written as lists
        for node_list in ['node_taints', 'node_labels']:
            value = node_metadata.get(node_list, [])
            if value:
                node_metadata[node_list] = value.split(',')
            else:
                node_metadata[node_list] = []

        distro_cfg[node_name] = node_metadata
        self.app.write_yaml()

    def delete_from_parent_yaml(self, node_name: str):
        """
        delete an extra node and update the base parent app yaml
        """
        distro_cfg = self.app.cfg['k8s_distros']['k3s']['nodes']
        distro_cfg.pop(node_name, None)
        self.app.write_yaml()

    def add_node_row(self, node: str = "", node_dict: dict = {}) -> None:
        """ 
        add a node input section for k3s
        """
        hostname = node

        # hostname label and input
        host_label_tooltip = (
                "The hostname or ip address of the node you'd like to "
                "join to the cluster"
                )
        host_input = input_field(label="host",
                                 initial_value=hostname,
                                 name="host",
                                 placeholder="hostname or ip address",
                                 tooltip=host_label_tooltip)

        # node type label and input
        node_type_tooltip = ("The type for this Kubernetes node. "
                             "Choose between worker or control_plane.")

        node_type_dropdown = drop_down(
                ['worker', 'control_plane'],
                select_value=node_dict.get('node_type', 'worker'),
                name="node_type",
                tooltip=node_type_tooltip,
                label="node_type"
                )

        # ssh key label and input
        default_ssh_key = join(HOME_DIR, ".ssh/id_rsa")
        ssh_key_label_tooltip = (
                "The SSH key to use to connect to the other node. This "
                f"defaults to {default_ssh_key}"
                )
        ssh_key = node_dict.get('ssh_key', "id_rsa")
        ssh_key_input = input_field(label="ssh_key",
                                    initial_value=ssh_key,
                                    name="ssh_key",
                                    placeholder="SSH key to connect to host",
                                    tooltip=ssh_key_label_tooltip)

        # node labels label and input
        node_labels_label_tooltip = (
                "Any labels you'd like to apply to this node (useful for node "
                "affinity). For multiple labels, use commas to seperate them."
                )
        node_labels = node_dict.get('node_labels', "")
        node_labels_input = input_field(
                label="node_labels",
                initial_value=node_labels,
                name="node_labels",
                placeholder="labels to apply to this node",
                tooltip=node_labels_label_tooltip)

        # taints label and input
        taints_label_tooltip = (
                "Any taints you'd like to apply to this node (useful for pod "
                "tolerations). For multiple labels, use commas to seperate them."
                )
        taints = node_dict.get('node_taints', "")
        taints_input = input_field(
                label="node_taints",
                initial_value=taints,
                name="node_taints",
                placeholder="taints to apply to this node",
                tooltip=taints_label_tooltip)

        # submit button
        submit = Button("➕ new node", id="new-node-button")
        submit.tooltip = "Submit new node to cluster to be joined on cluster creation"

        return Grid(host_input, node_type_dropdown, ssh_key_input, 
                    node_labels_input, taints_input, submit,
                    id=f"{hostname}-row", classes="k3s-node-input-row")

    @on(Button.Pressed)
    def submit_new_node(self, event: Button.Pressed):
        """
        submit new node to cluster
        """
        if event.button.id == "new-node-button":
            host = self.get_widget_by_id("host").value
            node_type = self.get_widget_by_id("node-type").value
            ssh_key = self.get_widget_by_id("ssh-key").value
            node_labels = self.get_widget_by_id("node-labels").value
            taints = self.get_widget_by_id("node-taints").value
            node_metadata = {"node_type": node_type,
                             "ssh_key": ssh_key,
                             "node_labels": node_labels,
                             "node_taints": taints}

            if not self.nodes:
                self.nodes = {host: node_metadata}
                self.generate_nodes_table()
                self.get_widget_by_id("nodes-placeholder").display = False
            else:
                self.nodes[host] = node_metadata
                data_table = self.get_widget_by_id("nodes-data-table")
                row = [host, node_type, ssh_key, node_labels, taints]
                # we use an extra line to center the rows vertically 
                styled_row = [Text(str("\n" + cell), justify="center") for cell in row]
                # we add extra height to make the rows more readable
                data_table.add_row(*styled_row, height=3, key=row[0])

            self.update_parent_yaml(host, node_metadata)
