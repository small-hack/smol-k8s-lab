from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Grid
from textual.validation import Length
from textual.widgets import Footer, Header, Button, Label, DataTable, Input, Static
from smol_k8s_lab.constants import INITIAL_USR_CONFIG
from smol_k8s_lab.k8s_distros import check_all_contexts
from smol_k8s_lab.utils.tui.validators.already_exists import CheckIfNameAlreadyInUse
from smol_k8s_lab.utils.tui.base_cluster_modal import ClusterModalScreen
from smol_k8s_lab.utils.tui.apps_config import AppsConfig
from smol_k8s_lab.utils.tui.confirm_selection import ConfirmConfig
from smol_k8s_lab.utils.tui.distro_config import DistroConfigScreen
from smol_k8s_lab.utils.tui.help import HelpScreen
from smol_k8s_lab.utils.tui.smol_k8s_config import SmolK8sLabConfig
from smol_k8s_lab.utils.write_yaml import dump_to_file


class BaseApp(App):
    BINDINGS = [Binding(key="?",
                        key_display="?",
                        action="request_help",
                        description="Help",
                        show=True),
                Binding(key="f",
                        key_display="f",
                        action="toggle_footer",
                        description="toggle footer"),
                Binding(key="q",
                        action="quit",
                        show=False)
                ]

    CSS_PATH = ["./css/base.tcss",
                "./css/help.tcss"]

    def __init__(self, user_config: dict = INITIAL_USR_CONFIG) -> None:
        self.cfg = user_config
        self.show_footer = self.cfg['smol_k8s_lab']['interactive']['show_footer']
        self.cluster_names = []
        self.current_cluster = ""
        super().__init__()

    def compose(self) -> ComposeResult:
        """
        Compose app with screens
        """
        yield Header()

        # Footer to show keys
        footer = Footer()

        if not self.show_footer:
            footer.display = False
        yield footer

        # full screen container
        with Grid(id="base-screen-container"):

            # the actual little box in the middle of screen
            with Grid(id="base-box-grid"):

                # help text that changes based on if we have clusters
                yield Label(id="clusters-text")

                # grid for the cluster data table
                with Grid(id="table-grid"):
                    yield DataTable(zebra_stripes=True,
                                    id="clusters-data-table",
                                    cursor_type="row")

                # container for new cluster buton
                yield NewClusterInput()

    def on_mount(self) -> None:
        """
        screen and box border styling
        """
        # screen title
        self.title = "ʕ ᵔᴥᵔʔ smol k8s lab"
        self.sub_title = "Getting Started"

        # main box title
        grid_title = "Modify or Create clusters"
        self.get_widget_by_id("base-box-grid").border_title = grid_title

        # get all clusters
        clusters = check_all_contexts()

        if not clusters:
            self.add_no_clusters_found_text()
        else:
            self.generate_cluster_table(clusters)

    def add_no_clusters_found_text(self,) -> None:
        """ 
        don't display the table and add text that says we found no clusters
        """
        self.get_widget_by_id("table-grid").display = False
        self.get_widget_by_id("base-box-grid").remove_class("larger-grid")
        self.get_widget_by_id("base-box-grid").add_class("smaller-grid")
        cluster_help = self.query_one("#clusters-text")
        cluster_help.update("No clusters found 🤷 We can fix that though!")

    def generate_cluster_table(self, clusters: list) -> None:
        """ 
        generate a readable table for all the clusters.

        Each row is has a height of 3 and is centered to make it easier to read
        for people with dyslexia
        """
        self.get_widget_by_id("base-box-grid").add_class("larger-grid")

        data_table = self.query_one(DataTable)

        # first, update the header text to let user know we've found clusters
        cluster_help = self.query_one("#clusters-text")
        cluster_help.update(
                "We found the following clusters. Select a row to modify the cluster's"
                " apps or even delete the cluster. You can also create a new cluster "
                "using button below.")

        # then fill in the cluster table
        data_table.add_column(Text("Cluster", justify="center"))
        data_table.add_column(Text("Distro", justify="center"))

        for row in clusters:
            # we use an extra line to center the rows vertically 
            styled_row = [Text(str("\n" + cell), justify="center") for cell in row]

            # we add extra height to make the rows more readable
            data_table.add_row(*styled_row, height=3, key=row[0])

            self.cluster_names.append(row[0])

    @on(DataTable.RowSelected)
    def cluster_row_highlighted(self, event: DataTable.RowSelected) -> None:
        """
        check which row was selected to launch a modal screen
        """
        def check_if_cluster_deleted(response: list = []):
            """
            check if cluster has been deleted
            """
            cluster = response[0]
            row_key = response[1]

            if cluster and row_key:
                data_table = self.query_one(DataTable)
                data_table.remove_row(row_key)

                self.cluster_names.remove(cluster)
                self.current_cluster = ""

                if data_table.row_count < 1:
                    self.add_no_clusters_found_text()

        row_index = event.cursor_row
        row = event.data_table.get_row_at(row_index)

        # get the row's first column (the name of the cluster) and remove whitespace
        cluster_name = row[0].plain.strip()
        distro = row[1].plain.strip()

        # set the current cluster name to return after we've done modifications
        self.current_cluster = cluster_name

        self.app.push_screen(ClusterModalScreen(cluster_name, distro, event.row_key),
                             check_if_cluster_deleted)

    def action_request_apps_cfg(self, app_to_highlight: str = "") -> None:
        """
        launches the argo app config screen
        """
        if app_to_highlight:
            self.app.push_screen(AppsConfig(self.cfg['apps'], app_to_highlight))
        else:
            self.app.push_screen(AppsConfig(self.cfg['apps'], ""))

    def action_request_distro_cfg(self) -> None:
        """
        launches the k8s disto (k3s,k3d,kind) config screen
        """
        self.app.push_screen(DistroConfigScreen(self.cfg['k8s_distros']))

    def action_request_smol_k8s_cfg(self) -> None:
        """
        launches the smol-k8s-lab config for the program itself for things like
        the TUI, but also logging and password management
        """
        self.app.push_screen(SmolK8sLabConfig(self.cfg['smol_k8s_lab']))

    def action_request_confirm(self) -> None:
        """
        show confirmation screen
        """
        self.app.push_screen(ConfirmConfig(self.cfg))

    def action_request_help(self) -> None:
        """
        if the user presses 'h' or '?', show the help modal screen
        """
        self.push_screen(HelpScreen())

    def action_toggle_footer(self) -> None:
        """
        don't display the footer, or do 🤷
        """
        footer = self.query_one(Footer)

        if footer.display:
            footer.display = False
            self.notify(
                "\n✨ Press [gold3]f[/] to re-enable the footer",
                timeout=9,
                title="Footer disabled"
            )
        else:
            footer.display = True

    def write_yaml(self) -> None:
        """
        dump current self.cfg to user's smol-k8s-lab config.yaml
        """
        dump_to_file(self.cfg)


class NewClusterInput(Static):
    def compose(self) -> ComposeResult:
        with Grid(id="new-cluster-button-container"):
            input = Input(value="smol-k8s-lab",
                          validators=[
                              Length(minimum=2),
                              CheckIfNameAlreadyInUse(self.app.cluster_names)
                              ],
                          placeholder="Name of your new cluster",
                          id="cluster-name-input")
            input.tooltip = "Name of your ✨ [i]new[/i] cluster"
            yield input

            new_button = Button("✨ New Cluster", id="new-cluster-button")
            new_button.tooltip = "Add a new cluster managed by smol-k8s-lab"
            yield new_button

    @on(Input.Changed)
    def input_validation(self, event: Input.Changed) -> None:
        if event.validation_result.is_valid:
            # if result is valid, enable the submit button
            self.get_widget_by_id("new-cluster-button").disabled = False
        else:
            # if result is not valid, notify the user why
            self.notify("\n".join(event.validation_result.failure_descriptions),
                        timeout=8,
                        severity="warning",
                        title="⚠️ Input Validation Error\n")

            # and disable the submit button
            self.get_widget_by_id("new-cluster-button").disabled = True

    @on(Button.Pressed)
    def button_pressed(self, event: Button.Pressed) -> None:
        """
        get pressed button and act on it
        """
        self.current_cluster = self.get_widget_by_id("cluster-name-input").value
        self.app.action_request_distro_cfg()


if __name__ == "__main__":
    app = BaseApp()
    app.run()
