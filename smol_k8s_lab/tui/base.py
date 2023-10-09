# smol-k8s-lab libraries
from smol_k8s_lab.constants import INITIAL_USR_CONFIG, XDG_CONFIG_FILE
from smol_k8s_lab.k8s_distros import check_all_contexts
from smol_k8s_lab.tui.apps_config import AppsConfig
from smol_k8s_lab.tui.base_cluster_modal import ClusterModalScreen
from smol_k8s_lab.tui.confirm_selection import ConfirmConfig
from smol_k8s_lab.tui.distro_config import DistroConfigScreen
from smol_k8s_lab.tui.help import HelpScreen
from smol_k8s_lab.tui.smol_k8s_config import SmolK8sLabConfig
from smol_k8s_lab.tui.validators.already_exists import CheckIfNameAlreadyInUse

# external libraries
from pyfiglet import Figlet
import random
from rich.text import Text
from ruamel.yaml import YAML
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Grid
from textual.validation import Length
from textual.widgets import Footer, Button, DataTable, Input, Static, Label

# list of approved words for nouns
CUTE_NOUNS = ["bunny", "hoglet", "puppy", "kitten", "knuffel", "friend",
              "egel", "meerkoet", "raccoon", "wasbeertje"]

CUTE_ADJECTIVE = ["lovely", "adorable", "cute", "friendly", "nice", "leuke",
                  "mooie", "vriendelijke", "cool", "soft"]


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
                Binding(key="q,escape",
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
        # Footer to show keys
        footer = Footer()

        if not self.show_footer:
            footer.display = False
        yield footer

        # full screen container
        with Grid(id="base-screen-container"):
            yield Label(Figlet(font="ogre").renderText("smol-k8s-lab"),
                        id="smol-k8s-lab-header")

            with Grid(id="cluster-boxes"):
                # the actual little box in the middle of screen
                with Grid(id="base-new-cluster-input-box-grid"):
                    # container for new cluster buton
                    with Grid(id="cluster-input-row"):
                        yield NewClusterInput()

    def on_mount(self) -> None:
        """
        screen and box border styling
        """
        # main box title
        title = "[#ffaff9]Create[/] a [i]new[/] [#C1FF87]cluster[/] with the name below"
        self.get_widget_by_id("base-new-cluster-input-box-grid").border_title = title

        # get all clusters
        clusters = check_all_contexts()

        if clusters:
            self.generate_cluster_table(clusters)
        else:
            self.get_widget_by_id("cluster-boxes").add_class("no-cluster-table")

    def generate_cluster_table(self, clusters: list) -> None:
        """ 
        generate a readable table for all the clusters.

        Each row is has a height of 3 and is centered to make it easier to read
        for people with dyslexia
        """
        data_table = DataTable(zebra_stripes=True,
                               id="clusters-data-table",
                               cursor_type="row")

        # then fill in the cluster table
        data_table.add_column(Text("Cluster", justify="center"))
        data_table.add_column(Text("Distro", justify="center"))

        for row in clusters:
            # we use an extra line to center the rows vertically 
            styled_row = [Text(str("\n" + cell), justify="center") for cell in row]

            # we add extra height to make the rows more readable
            data_table.add_row(*styled_row, height=3, key=row[0])

            self.cluster_names.append(row[0])

        # grid for the cluster data table
        table_grid = Grid(data_table,
                          id="table-grid")

        # the actual little box in the middle of screen
        main_grid = Grid(table_grid, id="base-cluster-table-box-grid")

        # modify clusters box title
        main_grid.border_title = "Select a row to [#ffaff9]modify[/] or [#ffaff9]delete[/] an [i]existing[/] [#C1FF87]cluster[/]"

        screen_container = self.get_widget_by_id("cluster-boxes")
        screen_container.add_class("with-cluster-table")
        screen_container.mount(main_grid, before="#base-new-cluster-input-box-grid")


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

            # make sure we actually got anything, because the user may have hit
            # the cancel button
            if cluster and row_key:
                data_table = self.query_one(DataTable)
                data_table.remove_row(row_key)

                self.cluster_names.remove(cluster)
                self.current_cluster = ""

                if data_table.row_count < 1:
                    self.get_widget_by_id("base-cluster-table-box-grid").remove()
                    screen = self.get_widget_by_id("cluster-boxes")
                    screen.remove_class("with-cluster-table")
                    screen.add_class("no-cluster-table")

        row_index = event.cursor_row
        row = event.data_table.get_row_at(row_index)

        # get the row's first column (the name of the cluster) and remove whitespace
        cluster_name = row[0].plain.strip()
        distro = row[1].plain.strip()

        # set the current cluster name to return after we've done modifications
        self.current_cluster = cluster_name

        # launch modal UI to ask if they'd like to modify or delete a cluster
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

    def write_yaml(self, config_file: str = XDG_CONFIG_FILE) -> None:
        """
        dump current self.cfg to user's smol-k8s-lab config.yaml
        """
        yaml = YAML()

        with open(config_file, 'w') as smol_k8s_config:
            yaml.dump(self.cfg, smol_k8s_config)


class NewClusterInput(Static):
    """ 
    small widget with an input and button that takes the names of a cluster,
    and changes the 
    """
    def compose(self) -> ComposeResult:
        with Grid(id="new-cluster-button-container"):
            input = Input(validators=[
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

    def on_mount(self) -> None:
        input = self.get_widget_by_id("cluster-name-input")
        input.value = random.choice(CUTE_ADJECTIVE) + '-' + random.choice(CUTE_NOUNS)


    @on(Input.Changed)
    @on(Input.Submitted)
    def input_validation(self, event: Input.Changed | Input.Submitted) -> None:
        """ 
        Takes events matching Input.Changed and Input.Submitted events, and
        checks if input is valid. If the user presses enter (Input.Submitted),
        and the input is valid, we also press the button for them.
        """
        new_cluster_button = self.get_widget_by_id("new-cluster-button")

        if event.validation_result.is_valid:
            # if result is valid, enable the submit button
            new_cluster_button.disabled = False

            # if the user pressed enter, we also press the submit button ✨
            if isinstance(event, Input.Submitted):
                new_cluster_button.action_press()

        else:
            # if result is not valid, notify the user why
            self.notify("\n".join(event.validation_result.failure_descriptions),
                        timeout=8,
                        severity="warning",
                        title="⚠️ Input Validation Error\n")

            # and disable the submit button
            new_cluster_button.disabled = True

    @on(Button.Pressed)
    def button_pressed(self, event: Button.Pressed) -> None:
        """
        get pressed button (Button.Pressed event) and change current screen to
        the k8s distro config screen
        """
        self.app.current_cluster = self.get_widget_by_id("cluster-name-input").value
        self.app.action_request_distro_cfg()


if __name__ == "__main__":
    app = BaseApp()
    app.run()
