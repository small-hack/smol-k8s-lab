from smol_k8s_lab.utils.tui.bitwarden.bitwarden_modal_screen import BitwardenCredentials
from smol_k8s_lab.utils.bw_cli import BwCLI
from textual.app import App, ComposeResult
from textual.widgets import Label


class ReturnBitwardenObj(App[None]):
    CSS = """
        Screen {
           align: center middle;
        }
        """

    def __init__(self, overwrite: bool = False) -> None:
        """
        just take the overwrite boolean
        """
        self.overwrite = overwrite
        super().__init__()

    def compose(self) -> ComposeResult:
        """
        check if we need to grab the password or not
        """
        yield Label("")
        self.get_credentials()

    def get_credentials(self,) -> None:
        def check_modal_output(credentials: dict):
            if credentials:
                self.app.exit(BwCLI(credentials["BW_PASSWORD"],
                                     credentials["BW_CLIENTID"],
                                     credentials["BW_CLIENTSECRET"],
                                     self.overwrite))

        self.app.push_screen(BitwardenCredentials(), check_modal_output)

if __name__ == "__main__":
    app = ReturnBitwardenObj()
    app.run()
