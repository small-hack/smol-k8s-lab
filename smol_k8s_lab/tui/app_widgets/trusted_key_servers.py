# smol-k8s-lab libraries
from smol_k8s_lab.tui.util import input_field

# external libraries
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Grid
from textual.screen import ModalScreen
from textual.widgets import Label, Button, Static

class TrustedKeyServersWidget(Static):
    """
    widget to take special smol-k8s-lab
    """
    CSS_PATH = "../css/apps_init_config.tcss"

    def __init__(self, app_name: str, trusted_key_servers: dict) -> None:
        self.app_name = app_name
        self.trusted_keys_srvr = trusted_key_servers

        super().__init__()

    def compose(self) -> ComposeResult:
        yield Container(
                id=f"{self.app_name}-trusted-key-widget-grid",
                classes=f"{self.app_name}"
                )

    def on_mount(self):
        container = self.get_widget_by_id(f"{self.app_name}-trusted-key-widget-grid")
        self.generate_trusted_key_server_rows(container)


    def generate_trusted_key_server_rows(self, container: Container):
        """
        generate trusted key servers rows
        """
        container.mount(Label("Trusted Key Servers [dim](Optional)[/dim]",
                              classes="trusted-key-servers-label"))

        for key_server in self.trusted_keys_srvr:
            server_name = key_server['server_name']
            hyphen_srvr_name = server_name.replace(".", "-")
            server_input = input_field(
                    "server name",
                    server_name,
                    "server_name",
                    "Trusted key server hostname",
                    "Trusted key server for federating with synapse (your matrix server)",
                    stacked=True
                              )

            # we mount this all at once later down
            verify_rows = []

            # for security, you can have a key for each
            verify_keys = key_server.get("verify_keys", {})
            if verify_keys:
                for key, value in verify_keys.items():
                    verify_rows.append(self.create_verify_key_row(key, value))

                # verify grid should be to the right to of the trusted key server name
                verify_keys_grid = Grid(
                        *verify_rows,
                        id=f"{hyphen_srvr_name}-verify-keys-container"
                        )
            else:
                # verify grid should be to the right to of the trusted key server name
                verify_keys_grid = Grid(
                        Button("➕ verify key",
                               id=f"{hyphen_srvr_name}-add-verify-key",
                               classes="add-new-verify-key-button"),
                        id=f"{hyphen_srvr_name}-verify-keys-container"
                        )

            # mount the key server row into the main init container
            container.mount(
                    Grid(server_input,
                         verify_keys_grid,
                         id=f"{hyphen_srvr_name}-key-server-row",
                         classes="trusted-key-servers")
                    )

    def create_verify_key_row(self, key: str, value: str):
        """
        create a verified key row for a given trusted key server
        """

        hyphen_key = key.replace(":","-")
        key_field = input_field(
                key,
                value,
                key,
                "Verify key value",
                "Verify key value",
                sensitive=True,
                stacked=True
                          )

        button = Button("🚮",
                        id=f"{hyphen_key}-trash-button",
                        classes="verify-key-row-delete-button")
        verify_key_row = Grid(key_field,
                              button,
                              classes="verify-key-row",
                              id=f"{hyphen_key}-row")
        return verify_key_row

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed):
        """
        handle button presses
        """
        if "trash-button" in event.button.id:
            button_row = event.button.parent
            key_row = button_row.parent
            server_row = key_row.parent
            hyphen_srvr_name = server_row.id.replace("-verify-keys-container","")

            # remove the key row
            button_row.remove()
            # add a new button
            key_row.mount(Button("➕ verify key",
                                 id=f"{hyphen_srvr_name}-add-verify-key",
                                 classes="add-new-verify-key-button"))
            self.notify(
                    "\nThis button doesn't actually work yet, but will soon. "
                    "Right now, it just does UI magic. In the "
                    "meantime, edit your yaml config directly under the "
                    "apps.matrix.init.values section :)",
            title="😼 Nope. (but soon)")
        elif "-add-verify-key" in event.button.id:
            self.notify(
                    "\nThis button doesn't work yet, but will soon. In the "
                    "meantime, edit your yaml config directly under the "
                    "apps.matrix.init.values section :)",
            title="😼 Nope. (but soon)")


class AddModifyTrustedKeysModalScreen(ModalScreen):
    """
    modal screen with inputs to modify
    """
    CSS_PATH = ["../css/base_modal.tcss",
                "../css/modify_globals_modal.tcss"]

    def __init__(self) -> None:
        super().__init__()
