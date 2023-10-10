from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.validation import Length
from textual.widgets import Label, Input, Button


HELP_TXT = ("Requires [u][link=https://bitwarden.com/help/personal-api-key/]"
            "personal API credentials[/][/]. To avoid this prompt, export the "
            "following env vars before running smol-k8s-lab: "
            "BW_PASSWORD, BW_CLIENTID, BW_CLIENTSECRET")


class BitwardenCredentialsScreen(ModalScreen):
    """
    modal screen to ask for bitwarden credentials
    """
    CSS_PATH = "./bitwarden.css"
    BINDINGS = [Binding(key="b,escape,q",
                        key_display="b",
                        action="press_cancel",
                        description="Back")]

    def compose(self) -> ComposeResult:

        # base container for the whole screen
        with Grid(id="bitwarden-modal-container"):

            # container for the actual help, inputs, and confirm button
            with Grid(id="credentials-box"):

                # base help text to start us off
                yield Label(HELP_TXT, id="bitwarden-help-text")

                with Grid(id="all-bitwarden-inputs"):
                    for variable in ['password', 'client_id', 'client_secret']:
                        yield self.generate_credential_row(variable)

                with Grid(id="bitwarden-button-box"):
                    # submit button, to trigger returning the credentials/exiting
                    confirm_button = Button("submit", id="bitwarden-submit")
                    confirm_button.disabled = True
                    confirm_button.tooltip = ("submit your credentials, disabled"
                                              " until all fields are filled out.")
                    yield confirm_button

                    # cancel button, to go back to the script or previous tui screen
                    back_button = Button("cancel", id="bitwarden-cancel")
                    back_button.tooltip = ("Exit Bitwarden credentials input screen "
                                           "without saving")
                    yield back_button

    def on_mount(self,) -> None:
        credentials_box = self.get_widget_by_id("credentials-box")
        credentials_box.border_title = "[green]🛡️ Enter Bitwarden Vault Credentials"

        # we set this at the beginning, so we can still return empty if they cancel
        self.credentials = {}

    def action_press_cancel(self) -> None:
        """
        presses the cancel button
        """
        self.get_widget_by_id("bitwarden-cancel").action_press()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        return bitwarden password, client id, and client secret as a dict
        """
        if event.button.id == "bitwarden-cancel":
            self.dismiss(None)
        else:
            self.dismiss(self.credentials)

    @on(Input.Changed)
    def on_input_changed(self, event: Input.Changed) -> None:
        """
        on any input field change, check all input fields and enable or disable 
        the confirm button
        """
        all_valid = True

        all_inputs = self.query(".bitwarden-inputs")

        # check all the input validations
        for input in all_inputs:
            is_not_valid = input.validate(input.value).failures
            # returns None if input is valid
            if is_not_valid:
                all_valid = False
            # if valid, make sure it's in our final return dict
            else:
                self.credentials[input.name] = input.value

        confirm_button = self.get_widget_by_id("bitwarden-submit")

        # disable button if any inputs are invalid
        if all_valid:
            confirm_button.disabled = False
        else:
            confirm_button.disabled = True

    def generate_credential_row(self, label: str) -> None:
        """
        return a row of a Label and Input in a Grid container
        """
        pretty_label = label.replace("_", " ").replace("id", "ID") + ":"
        input_label = Label(pretty_label, classes="bitwarden-label")

        input = Input(placeholder=label,
                      password=True,
                      validators=Length(minimum=2),
                      classes="bitwarden-inputs",
                      name=label)

        return Grid(input_label, input, classes="bitwarden-input-row")
