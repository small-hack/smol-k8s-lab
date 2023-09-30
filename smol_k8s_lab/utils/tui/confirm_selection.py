#!/usr/bin/env python3.11
from .bitwarden.bitwarden_modal_screen import BitwardenCredentials
from smol_k8s_lab.utils.yaml_with_comments import syntax_highlighted_yaml
from smol_k8s_lab.utils.bw_cli import BwCLI, check_env_for_credentials
from textual import on
from textual.binding import Binding
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Grid
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label


class ConfirmConfig(Screen):
    """
    Textual app confirm smol-k8s-lab config
    """
    CSS_PATH = ["./css/confirm.tcss"]

    BINDINGS = [Binding(key="escape,q",
                        key_display="esc,q",
                        action="app.pop_screen",
                        description="↩ Back")]

    def __init__(self, config: dict) -> None:
        """
        takes config: dict, should be the entire smol-k8s-lab config.yaml
        """
        self.cfg = config
        self.apps = self.cfg['apps']
        self.smol_k8s_cfg = self.cfg["smol_k8s_lab"]
        self.show_footer = self.smol_k8s_cfg['interactive']['show_footer']
        self.invalid_apps = {}
        super().__init__()

    def compose(self) -> ComposeResult:
        """
        Compose app with tabbed content.
        """
        # header to be cute
        yield Header()

        # Footer to show keys unless the footer is disabled globally
        footer = Footer()

        if not self.show_footer:
            footer.display = False

        yield footer

        with Grid(id="confirm-container"):
            # warning label if there's invalid apps
            warning_label = Label("Click the app links below to fix the errors.",
                                  id="warning-help")
            warning_box = Grid(warning_label, id="invalid-apps")
            warning_box.display = False
            yield warning_box

            # the actual yaml config in full
            with VerticalScroll(id="pretty-yaml-scroll-container"):
                yield Label("", id="pretty-yaml")

        # final confirmation button before running smol-k8s-lab
        with Grid(id="final-confirm-button-box"):
            confirm = Button("🚊 Let's roll!", id="confirm-button")
            confirm.display = False
            yield confirm

            back = Button("✋Go Back", id="back-button")
            back.display = False
            yield back

    def on_mount(self) -> None:
        """
        screen and box border styling
        """
        self.title = "ʕ ᵔᴥᵔʔ smol k8s lab"
        self.sub_title = "Review your configuration (last step!)"

        # confirm box title styling
        confirm_box = self.get_widget_by_id("pretty-yaml-scroll-container")
        confirm_box.border_title = "[gold3]All Configured Values"

        # display the current user yaml
        rich_highlighted = syntax_highlighted_yaml(self.cfg)
        self.get_widget_by_id("pretty-yaml").update(rich_highlighted)

        # invalid apps error title styling
        invalid_box = self.get_widget_by_id("invalid-apps")
        invalid_box.border_title = "[gold3]⚠️ The following app fields are empty"

        # go check all the app inputs
        self.get_app_inputs()

        at_least_one_missing_field = False
        if self.invalid_apps:
            at_least_one_missing_field = True

        if not at_least_one_missing_field:
            self.get_widget_by_id("invalid-apps").display = False
            self.get_widget_by_id("pretty-yaml-scroll-container").display = True
            self.get_widget_by_id("confirm-button").display = True
            self.get_widget_by_id("back-button").display = True
        else:
            self.get_widget_by_id("pretty-yaml-scroll-container").display = False
            self.get_widget_by_id("confirm-button").display = False
            self.get_widget_by_id("invalid-apps").display = True
            self.build_pretty_nope_table()

    def get_app_inputs(self) -> None:
        """
        processes the entire apps config to check for empty fields
        """
        for app, metadata in self.apps.items():
            empty_fields = check_for_invalid_inputs(metadata)
            if empty_fields:
                self.invalid_apps[app] = empty_fields

    def build_pretty_nope_table(self) -> None:
        """
        No, but with flare ✨

        This is just a grid of apps to update if a user leaves a field blank
        """
        nope_container = self.get_widget_by_id("invalid-apps")

        for app, fields in self.invalid_apps.items():
            app_link = f'app.request_apps_cfg("{app}")'

            label = Label(f"[yellow][@click='{app_link}']{app}[/]:",
                          classes="nope-label nope-link")

            nopes = Label("[magenta]" + "[/], [magenta]".join(fields),
                          classes="nope-fields")

            nope_row = Grid(label, nopes, classes="nope-row")
            nope_container.mount(nope_row)

    def get_bitwarden_credentials_if_needed(self) -> BwCLI:
        """
        check if we need to grab the password or not
        """
        overwrite = self.smol_k8s_cfg['local_password_manager']['overwrite']

        def check_modal_output(credentials: dict):
            if credentials:
                self.app.exit([self.cfg,
                               BwCLI(credentials["BW_PASSWORD"],
                                     credentials["BW_CLIENTID"],
                                     credentials["BW_CLIENTSECRET"],
                                     overwrite)]
                              )

        # this is the official small-hack repo
        repo = "https://github.com/small-hack/argocd-apps"

        # if using a password manager, we check that it's bitwarden
        pw_mngr = self.smol_k8s_cfg['local_password_manager']
        local_bitwarden = pw_mngr['enabled'] and pw_mngr['name'] == "bitwarden"

        # check if bweso is enabled
        bweso = self.apps['bitwarden_eso_provider']
        official_bweso = bweso['enabled'] and bweso['argo']['repo'] == repo

        if local_bitwarden or official_bweso:
            password, client_id, client_secret = check_env_for_credentials()
            if not any([password, client_id, client_secret]):
                self.app.push_screen(BitwardenCredentials(), check_modal_output)
            else:
                self.app.exit([self.cfg,
                               BwCLI(password, client_id, client_secret, overwrite)])
        else:
            self.app.exit([self.cfg, None])

    @on(Button.Pressed)
    def exit_app_and_return_new_config(self, event: Button.Pressed) -> None:
        """
        Checks which button was returned on Button.Pressed events. If it's the
        confirm button, we return the root parent app config to itself and call
        app.exit it, which pops this screen as well as the root, leaving the TUI.

        If the button is the back-button, we just pop the screen, which goes back
        to the main menu screen.
        """
        if event.button.id == "confirm-button":
            # check if we need bitwarden credentials before proceeding
            self.get_bitwarden_credentials_if_needed()

        if event.button.id == "back-button":
            self.app.pop_screen()


def check_for_invalid_inputs(metadata) -> list:
    """
    check each app for any empty init or secret key fields
    """
    if not metadata['enabled']:
        return []

    empty_fields = []

    # check for empty init fields (some apps don't support init at all)
    if metadata.get('init', None):
        init_values = metadata['init'].get('values')
        if init_values:
            for key, value in init_values.items():
                if not value:
                    empty_fields.append(key)

    # check for empty secret key fields (some apps don't have secret keys)
    secret_keys = metadata['argo'].get('secret_keys', None)
    if secret_keys:
        for key, value in secret_keys.items():
            if not value:
                empty_fields.append(key)

    return empty_fields
