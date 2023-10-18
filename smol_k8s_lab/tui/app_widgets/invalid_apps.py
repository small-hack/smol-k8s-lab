#!/usr/bin/env python3.11
# external libraries
from rich.text import Text
from textual import on
from textual.binding import Binding
from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Label


class InvalidAppsScreen(Screen):
    """
    Textual app to show all invalid apps
    """
    CSS_PATH = ["../css/invalid_apps.tcss"]

    BINDINGS = [Binding(key="b,q,escape",
                        key_display="b",
                        action="app.pop_screen",
                        description="⬅️ Back"),
                Binding(key="n",
                        show=False,
                        action="app.bell")]

    def __init__(self, invalid_apps: dict) -> None:
        """
        takes config: dict, should be the entire smol-k8s-lab config.yaml
        """
        self.show_footer = self.app.cfg['smol_k8s_lab']['tui']['show_footer']
        self.invalid_apps = invalid_apps
        super().__init__()

    def compose(self) -> ComposeResult:
        """
        Compose app with tabbed content.
        """
        # Footer to show keys unless the footer is disabled globally
        footer = Footer()
        if not self.show_footer:
            footer.display = False
        yield footer

        # warning label if there's invalid apps
        warning_label = Label(
                "\nClick the app links below to fix the errors or disable them.",
                classes="help-text"
                )
        yield Grid(warning_label, id="invalid-apps")

    def on_mount(self) -> None:
        # invalid apps error title styling
        invalid_box = self.get_widget_by_id("invalid-apps")
        border_title = "⚠️ The following app fields are empty"
        invalid_box.border_title = border_title

        if self.app.speak_screen_titles:
            self.app.action_say("Screen title: " + border_title)

        self.build_pretty_nope_table()

    def build_pretty_nope_table(self) -> None:
        """
        No, but with flare ✨

        This is just a grid of apps to update if a user leaves a field blank
        """
        nope_container = self.get_widget_by_id("invalid-apps")

        data_table = DataTable(zebra_stripes=True,
                               id="invalid-apps-table",
                               cursor_type="row")

        # then fill in the cluster table
        data_table.add_column(Text("Application", justify="center"))
        data_table.add_column(Text("Invalid Fields"))

        for app, fields in self.invalid_apps.items():
            # we use an extra line to center the rows vertically 
            styled_row = [
                    Text(str("\n" + app)),
                    Text(str("\n" + ", ".join(fields)))
                          ]

            # we add extra height to make the rows more readable
            data_table.add_row(*styled_row, height=3, key=app)

        nope_container.mount(Grid(data_table, id="invalid-apps-table-row"))

    @on(DataTable.RowSelected)
    def app_row_selected(self, event: DataTable.RowSelected) -> None:
        """
        check which row was selected to launch a app config screen for app 
        """
        row_index = event.cursor_row
        row = event.data_table.get_row_at(row_index)

        # get the row's first column (app) and remove whitespace
        app = row[0].plain.strip()

        # try to launch the app screen for the given app again
        self.app.action_request_apps_cfg(app)
