from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Container
from textual.widgets import Footer, Header, Button, Label, DataTable
from smol_k8s_lab.k8s_distros import check_all_contexts
from smol_k8s_lab.utils.write_yaml import dump_to_file
from smol_k8s_lab.utils.tui.apps_config import AppConfig
from smol_k8s_lab.utils.tui.confirm_selection import ConfirmConfig
from smol_k8s_lab.utils.tui.distro_config import DistroConfigScreen
from smol_k8s_lab.utils.tui.help import HelpScreen
from smol_k8s_lab.utils.tui.smol_k8s_config import SmolK8sLabConfig
from smol_k8s_lab.constants import INITIAL_USR_CONFIG


class BaseApp(App):
    BINDINGS = [Binding(key="?",
                        key_display="?",
                        action="request_help",
                        description="Help",
                        show=True),
                Binding(key="f",
                        key_display="f",
                        action="toggle_footer",
                        description="toggle footer")
                ]

    CSS_PATH = ["./css/base.tcss",
                "./css/help.tcss"]

    def __init__(self, user_config: dict = INITIAL_USR_CONFIG) -> None:
        self.cfg = user_config
        self.show_footer = self.cfg['smol_k8s_lab']['interactive']['show_footer']
        self.current_screen = 'start'
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

        with Grid(id="base-screen-container"):
            with Grid(id="base-box-grid"):

                with Grid(id="table-grid"):
                    yield DataTable(zebra_stripes=True,
                                    id="clusters-data-table")

                with Container(id="new-cluster-button-container"):
                    new_button = Button("✨ New Cluster", id="new-cluster-button")
                    new_button.tooltip = "Add a new cluster managed by smol-k8s-lab"
                    yield new_button

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        get pressed button add or delete button and act on it
        """
        button_id = event.button.id

        if button_id == "new-cluster-button":
            self.action_request_distro_cfg()

    def on_mount(self) -> None:
        """
        screen and box border styling
        """
        # screen title
        self.title = "ʕ ᵔᴥᵔʔ smol k8s lab"
        self.sub_title = "Getting Started"

        # main box title
        grid_title = "[chartreuse2]Modify or Create clusters"
        self.get_widget_by_id("base-box-grid").border_title = grid_title

        # data table grid container
        main_grid = self.get_widget_by_id("base-box-grid")

        # go check if we have existing clusters
        clusters = check_all_contexts()

        if not clusters:
            oops = Label("No clusters found 🤷 We can fix that though!",
                         id="no-clusters-found-text")
            main_grid.mount(oops, before="#new-cluster-button-container")
        else:
            self.generate_cluster_table(clusters)

    def generate_cluster_table(self, clusters: list):
        """ 
        generate a readable table for all the clusters.

        Each row is has a height of 3 and is centered to make it easier to read
        for people with dyslexia
        """
        datatable = self.query_one(DataTable)

        datatable.add_column(Text("Cluster", justify="center"))
        datatable.add_column(Text("Distro", justify="center"))
        datatable.add_column(Text("Edit", justify="center"))

        for row in clusters:
            # we use an extra line to even the rows and make them more readable
            final_row = (f"\n{row[0]}", f"\n{row[1]}", "\n✏️")

            styled_row = [
                    Text(str(cell), justify="center") for cell in final_row
                    ]
            datatable.add_row(*styled_row, height=3)

    def action_request_apps_cfg(self, app_to_highlight: str = "") -> None:
        """
        launches the argo app config screen
        """
        if app_to_highlight:
            self.app.push_screen(AppConfig(self.cfg['apps'], app_to_highlight))
        else:
            self.app.push_screen(AppConfig(self.cfg['apps'], ""))

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
        dump_to_file(self.cfg)

if __name__ == "__main__":
    app = BaseApp()
    app.run()
