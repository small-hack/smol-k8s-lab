#!/usr/bin/env python3.11
# external libraries
from rich.text import Text
from textual import on
from textual.binding import Binding
from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer


class InvalidAppsModalScreen(ModalScreen):
    """
    Textual app to show all invalid apps
    """
    CSS_PATH = ["../css/invalid_apps.tcss"]

    BINDINGS = [Binding(key="b,q,escape",
                        key_display="b",
                        action="app.pop_screen",
                        description="⬅️ Back"),
                Binding(key="f5",
                        key_display="f5",
                        description="Speak",
                        action="app.speak_element",
                        show=True),
                Binding(key="n",
                        show=False,
                        action="app.bell")]

    def __init__(self, invalid_apps: dict) -> None:
        """
        takes invalid apps dict
        """
        self.show_footer = self.app.cfg['smol_k8s_lab']['tui']['show_footer']
        self.invalid_apps = invalid_apps
        super().__init__()

    def compose(self) -> ComposeResult:
        """
        Compose footer and base grid with datatable
        """
        # Footer to show keys unless the footer is disabled globally
        footer = Footer()
        if not self.show_footer:
            footer.display = False
        yield footer

        # table in grid to be used for invalid apps
        data_table = DataTable(zebra_stripes=True,
                               id="invalid-apps-table",
                               cursor_type="row")
        yield Grid(data_table, id="invalid-apps")

    def on_mount(self) -> None:
        # invalid apps error title styling
        invalid_box = self.get_widget_by_id("invalid-apps")
        border_title = "⚠️ The following app fields are empty"
        invalid_box.border_title = border_title
        subtitle = "Click the app links above to fix the errors or disable them"
        invalid_box.border_subtitle = subtitle

        self.call_after_refresh(self.app.play_screen_audio,
                                screen="invalid_apps")

        self.build_pretty_nope_table()

    def build_pretty_nope_table(self) -> None:
        """
        No, but with flare ✨

        This is where we populate the DataTable with all the apps to update.
        If a user leaves a field blank it contains an invalid fields column
        for all the fields you need to fix
        """
        data_table = self.get_widget_by_id("invalid-apps-table")

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

        # immediately set the focus to this data table
        self.app.set_focus(data_table)

    @on(DataTable.RowSelected)
    def app_row_selected(self, event: DataTable.RowSelected) -> None:
        """
        check which row was selected to launch a app config screen for app
        """
        row_index = event.cursor_row
        row = event.data_table.get_row_at(row_index)

        # get the row's first column (app) and remove whitespace, and then
        # do the same for second column, only just grab the first invalid field
        return_app_field = (row[0].plain.strip(),
                            row[1].plain.strip().split(", ")[0])
        # go back to the app screen and scroll to the selected app and field
        self.dismiss(return_app_field)
