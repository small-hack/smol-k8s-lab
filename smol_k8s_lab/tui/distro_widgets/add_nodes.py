from smol_k8s_lab.constants import HOME_DIR, VERSION
from smol_k8s_lab.k8s_distros.k3s import join_k3s_nodes
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.tui.util import input_field, drop_down
from smol_k8s_lab.tui.distro_widgets.modify_node_modal import NodeModalScreen

from os.path import join
from rich.text import Text
from textual import on
from textual.app import ComposeResult, Widget
from textual.binding import Binding
from textual.containers import Grid
from textual.screen import Screen
from textual.widgets import Label, DataTable, Header, Footer

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
    def __init__(self,
                 nodes: dict = {},
                 existing_cluster: bool = False,
                 id: str = "") -> None:
        # this is just to take a few variables for class organizing
        self.nodes = nodes
        self.existing_cluster = existing_cluster
        if existing_cluster:
            self.k8s_ctx = K8s()
            self.existing_nodes = self.k8s_ctx.get_nodes()
        super().__init__(id=id)

    def compose(self) -> ComposeResult:
        # this resizes based on how big the screen realestate we have is
        if self.existing_cluster:
            box_class = "add-nodes-box-full-screen"
            label_class = "new-node-text-full-screen"
        else:
            box_class = "add-nodes-box-widget"
            label_class = "new-node-text-widget"

        with Grid(id="add-nodes-box", classes=box_class):
            yield Label(placeholder, id="nodes-placeholder")
            yield Label(" 🖥️  [#ffaff9]Add[/] a [i]new[/i] [#C1FF87]node[/]",
                        id="new-node-text", classes=label_class)
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
        if self.existing_cluster:
            data_table.add_column(Text("Status", justify="center"))
        data_table.add_column(Text("Type", justify="center"))
        data_table.add_column(Text("SSH Port", justify="center"))
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

            if not self.existing_cluster:
                row = [node,
                       metadata['node_type'],
                       metadata['ssh_port'],
                       metadata['ssh_key'],
                       labels,
                       taints]
            else:
                # if the cluster already exists, get current node data
                node_info = self.k8s_ctx.get_node(node)
                row = [node,
                       node_info.get('status', 'Not Found'),
                       metadata['node_type'],
                       metadata['ssh_port'],
                       metadata['ssh_key'],
                       labels,
                       taints]

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
            self.app.say_row(event.data_table)

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
                                 tooltip=host_label_tooltip,
                                 validate_empty=True,
                                 extra_row_class="input-row-equal")

        # node type label and input
        node_type_tooltip = ("The type for this Kubernetes node. "
                             "Choose between worker or control_plane.")

        node_type_dropdown = drop_down(
                ['worker', 'control_plane'],
                select_value=node_dict.get('node_type', 'worker'),
                name="node_type",
                tooltip=node_type_tooltip,
                label="node_type",
                extra_row_class="input-row-equal")

        # ssh port label and input
        default_ssh_port = "22"
        ssh_port_label_tooltip = (
                "The SSH port to use to connect to the other node. This "
                f"defaults to {default_ssh_port}"
                )
        ssh_port = node_dict.get('ssh_port', default_ssh_port)
        ssh_port_input = input_field(label="ssh_port",
                                     initial_value=ssh_port,
                                     name="ssh_port",
                                     placeholder="SSH port to connect to host",
                                     tooltip=ssh_port_label_tooltip,
                                     extra_row_class="input-row-equal")

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
                                    tooltip=ssh_key_label_tooltip,
                                    extra_row_class="input-row-equal")

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
                tooltip=node_labels_label_tooltip,
                extra_row_class="input-row-equal")

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
                tooltip=taints_label_tooltip,
                extra_row_class="input-row-equal")

        return Grid(host_input, node_type_dropdown,
                    ssh_port_input, ssh_key_input,
                    node_labels_input, taints_input,
                    id=f"{hostname}-row", classes="k3s-node-input-row")

    def action_press_new_node_button(self) -> None:
        """
        this is a hidden "button" if you will that will add a new node
        based on the inputs in the "🖥️Add a new node" section
        """
        host_input = self.get_widget_by_id("host")
        host_value = host_input.value
        host_input.validate(host_value)

        # not much else matters except the hostname
        if not host_value:
            self.app.notify(
                    message="You need at least a hostname to add a new node.",
                    title="⚠️ Missing Hostname",
                    severity="warning"
                    )
            return

        node_type = self.get_widget_by_id("node-type").value
        ssh_key = self.get_widget_by_id("ssh-key").value
        ssh_port = self.get_widget_by_id("ssh-port").value
        node_labels = self.get_widget_by_id("node-labels").value
        taints = self.get_widget_by_id("node-taints").value
        node_metadata = {"node_type": node_type,
                         "ssh_key": ssh_key,
                         "ssh_port": ssh_port,
                         "node_labels": node_labels,
                         "node_taints": taints}

        new_node_dict = {host_value: node_metadata}
        if not self.nodes:
            self.nodes = new_node_dict
            self.generate_nodes_table()
            self.get_widget_by_id("nodes-placeholder").display = False
        else:
            self.nodes[host_value] = node_metadata
            data_table = self.get_widget_by_id("nodes-data-table")
            if not self.existing_cluster:
                row = [host_value, node_type, ssh_port, ssh_key, node_labels, taints]
            else:
                row = [host_value, "pending", node_type, ssh_port, ssh_key, node_labels, taints]
            # we use an extra line to center the rows vertically
            styled_row = [Text(str("\n" + cell), justify="center") for cell in row]
            # we add extra height to make the rows more readable
            data_table.add_row(*styled_row, height=3, key=row[0])

        self.update_parent_yaml(host_value, node_metadata)

        # if this is an existing cluster, go ahead and join the new node right away
        if self.existing_cluster:
            self.notify(f"Joining {host_value} to the cluster. Please hold.")
            join_k3s_nodes(new_node_dict)
            self.notify(f"{host_value} [i]should[/i] be joined now!")


class NodesConfigScreen(Screen):
    """
    Textual screen to configure nodes for an existing cluster
    """
    CSS_PATH = ["../css/distro_config.tcss",
                "../css/add_nodes_widget.tcss",
                "../css/k3s.tcss"]

    BINDINGS = [Binding(key="b,q,escape",
                        key_display="b",
                        action="app.pop_screen",
                        description="Back"),
                Binding(key="ctrl+n",
                        key_display="ctrl+n",
                        action="add_node",
                        description="add new node")]

    def __init__(self,
                 nodes: dict,
                 existing_cluster: bool = False,
                 id: str = "") -> None:
        """.git/
        gather nodes info and if this is an existing_cluster
        """
        self.nodes = nodes
        self.existing_cluster = existing_cluster
        if self.existing_cluster:
            self.node_box_id = "existing-cluster-node-config-box"
        else:
            self.node_box_id = "node-config-box"
        self.show_footer = self.app.cfg['smol_k8s_lab']['tui']['show_footer']
        super().__init__()

    def compose(self) -> ComposeResult:
        """
        Compose app with tabbed content.
        """
        # header to be cute
        yield Header()

        # Footer to show keys
        footer = Footer()
        if not self.show_footer:
            footer.display = False
        yield footer

        with Grid(id="node-config-screen"):
            yield AddNodesBox(nodes=self.nodes,
                              existing_cluster=self.existing_cluster,
                              id=self.node_box_id)

    def on_mount(self) -> None:
        """
        screen and box border styling
        """
        self.title = f"ʕ ᵔᴥᵔʔ smol-k8s-lab {VERSION}"
        sub_title = f"Kubernetes nodes config for {self.app.current_cluster}"
        self.sub_title = sub_title

        self.call_after_refresh(self.app.play_screen_audio, screen="nodes")

    def action_add_node(self) -> None:
        """
        trigger the add new node button
        """
        self.get_widget_by_id(self.node_box_id).action_press_new_node_button()
