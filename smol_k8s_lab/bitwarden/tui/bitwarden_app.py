from smol_k8s_lab.bitwarden.tui.bitwarden_credentials_modal_screen import (
        BitwardenCredentialsScreen)
from textual.app import App, ComposeResult
from textual.widgets import Label


class BitwardenCredentialsApp(App[None]):
    """ 
    small app to launch a modal screen for a bitwarden credentials prompt
    """
    CSS = """
        $bluish_white: rgb(189,216,255);
        $lavender: rgb(174,168,248);
        $neon_magenta: rgb(242,137,249);
        $orange: rgb(253,205,54);
        $spacechalk_lime: rgb(168,253,87);
        $light_cornflower: rgb(122,162,247);
        $blue_gray: rgb(86,95,137);
        $dark_gray: rgb(58,58,58);
        $navy: rgb(35,35,54);

        Screen {
           align: center middle;
        }

        Tooltip {
          background: $navy 50%;
          color: $bluish_white 75%;
          border: dashed gray 80%;
          padding-bottom: 0;
          padding-left: 1;
          padding-right: 1;
        }

        Button {
          color: $light_cornflower;
          background: $lavender 10%;
          border-top: tall $blue_gray 60%;
          border-bottom: tall $dark_gray 50%;
        }

        Input {
          background: $bluish_white 8%;
          color: white 75%;
          border: tall black 18%;
        }

        Input.-invalid {
           border: tall $neon_magenta 90%;
        }

        Input.-valid:focus {
           border: tall $spacechalk_lime 70%;
        }
        """

    def compose(self) -> ComposeResult:
        """
        check if we need to grab the password or not
        """
        yield Label("")
        self.get_credentials()

    def get_credentials(self) -> None:
        """
        launch a modal screen wtih inputs for bitwarden credentials
        """
        def check_modal_output(credentials: dict):
            if credentials:
                self.app.exit(credentials)
            else:
                self.app.exit(None)

        self.app.push_screen(BitwardenCredentialsScreen(), check_modal_output)

if __name__ == "__main__":
    app = BitwardenCredentialsApp()
    app.run()
