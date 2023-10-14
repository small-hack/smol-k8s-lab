#!/usr/bin/env python3.11
# smol-k8s-lab libraries
from smol_k8s_lab.bitwarden.tui.bitwarden_modal_screen import (
        BitwardenCredentialsScreen)
from smol_k8s_lab.utils.yaml_with_comments import syntax_highlighted_yaml

# external libraries
from os import environ as env
from textual import on
from textual.binding import Binding
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Grid
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, TabbedContent, TabPane


leaving_notification = ("\n- disable the bitwarden eso provider apps\n"
                        "- turn off local password manager")


class ConfirmConfig(Screen):
    """
    Textual app confirm smol-k8s-lab config
    """
    CSS_PATH = ["./css/confirm.tcss"]

    BINDINGS = [Binding(key="b,q,escape",
                        key_display="b",
                        action="app.pop_screen",
                        description="⬅️ Back"),
                Binding(key="n",
                        show=False,
                        action="app.bell")]

    def __init__(self, config: dict) -> None:
        """
        takes config: dict, should be the entire smol-k8s-lab config.yaml
        """
        self.cfg = config
        self.apps = self.cfg['apps']
        self.smol_k8s_cfg = self.cfg["smol_k8s_lab"]
        self.distros = self.cfg["k8s_distros"]
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

            # Add the TabbedContent widget different config sections
            with TabbedContent(initial="smol-k8s-lab-cfg", id="confirm-tabbed"):
                # tab 1 - smol-k8s-lab
                with TabPane("Core Config", id="smol-k8s-lab-cfg"):
                    with VerticalScroll(classes="pretty-yaml-scroll-container"):
                        yield Label("", id="pretty-yaml-smol-k8s-lab")

                # tab 2 - k8s_distros
                with TabPane("K8s Distro Config", id="k8s-distro-cfg"):
                    with VerticalScroll(classes="pretty-yaml-scroll-container"):
                        yield Label("", id="pretty-yaml-k8s-distro")

                # tab 3 - apps
                with TabPane("Apps Config", id="apps-cfg"):
                    with VerticalScroll(classes="pretty-yaml-scroll-container"):
                        yield Label("", id="pretty-yaml-apps")

                # tab 3 - apps
                with TabPane("Global Parameters Config", id="global-apps-cfg"):
                    with VerticalScroll(classes="pretty-yaml-scroll-container"):
                        yield Label("", id="pretty-yaml-global-apps")

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
        confirm_box = self.query_one(TabbedContent)
        confirm_box.border_title = "[i]Review[/] [i]All[/i] [#C1FF87]Values"

        # display the current user yaml
        smol_highlighted = syntax_highlighted_yaml({'smol_k8s_lab': self.smol_k8s_cfg})
        self.get_widget_by_id("pretty-yaml-smol-k8s-lab").update(smol_highlighted)

        # display the current user yaml
        distros_highlighted = syntax_highlighted_yaml({'k8s_distros': self.distros})
        self.get_widget_by_id("pretty-yaml-k8s-distro").update(distros_highlighted)

        # display the current user yaml
        apps_highlighted = syntax_highlighted_yaml({'apps': self.apps})
        self.get_widget_by_id("pretty-yaml-apps").update(apps_highlighted)

        # display the current user yaml
        g_apps_highlighted = syntax_highlighted_yaml({
            'apps_global_config': self.cfg['apps_global_config']
            })
        self.get_widget_by_id("pretty-yaml-global-apps").update(g_apps_highlighted)

        tabs = self.query("Tab")
        for tab in tabs:
            tab.add_class("confirm-tab-header")

        # invalid apps error title styling
        invalid_box = self.get_widget_by_id("invalid-apps")
        invalid_box.border_title = "⚠️ The following app fields are empty"

        # go check all the app inputs
        self.get_app_inputs()

        at_least_one_missing_field = False
        if self.invalid_apps:
            at_least_one_missing_field = True

        if not at_least_one_missing_field:
            self.get_widget_by_id("invalid-apps").display = False
            self.query_one(TabbedContent).display = True
            self.get_widget_by_id("confirm-button").display = True
            self.get_widget_by_id("back-button").display = True
        else:
            self.query_one(TabbedContent).display = False
            self.get_widget_by_id("confirm-button").display = False
            self.get_widget_by_id("invalid-apps").display = True
            self.build_pretty_nope_table()

    def action_show_tab(self, tab: str) -> None:
        """Switch to a new tab."""
        self.get_child_by_type(TabbedContent).active = tab

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

            nopes = Label("[i]" + "[/], [i]".join(fields),
                          classes="nope-fields")

            nope_row = Grid(label, nopes, classes="nope-row")
            nope_container.mount(nope_row)

    def get_bitwarden_credentials(self) -> None:
        """
        check if we need to grab the password or not
        """

        def process_modal_output(credentials: dict):
            """
            Exit with credentials
            """
            if credentials:
                self.app.exit([self.app.current_cluster, self.cfg, credentials])
            else:
                self.notify(leaving_notification, timeout=8,
                            title="💡To avoid the credentials prompt in the future")

        password = env.get("BW_PASSWORD", None)
        client_id = env.get("BW_CLIENTID", None)
        client_secret = env.get("BW_CLIENTSECRET", None)
        if not any([password, client_id, client_secret]):
            self.app.push_screen(BitwardenCredentialsScreen(), process_modal_output)
        else:
            self.app.exit([self.app.current_cluster,
                           self.cfg,
                           {'password': password,
                            'client_id': client_id,
                            'client_secret': client_secret}])

    @on(Button.Pressed)
    def confirm_or_back_button(self, event: Button.Pressed) -> None:
        """
        Checks which button was returned on Button.Pressed events. If it's the
        confirm button, we exit the TUI with the final confirmed config dict

        If the button is the back-button, we just pop the screen, which goes back
        to the main menu screen.
        """
        if event.button.id == "confirm-button":
            # First, check if we need bitwarden credentials before proceeding

            # this is the official small-hack repo
            repo = "https://github.com/small-hack/argocd-apps"
            pw_mngr = self.smol_k8s_cfg['local_password_manager']
            bweso = self.apps['bitwarden_eso_provider']


            # if local_password_manager is enabled, and is bitwarden
            local_bitwarden = pw_mngr['enabled'] and pw_mngr['name'] == "bitwarden"

            # check if bweso is enabled and we're using the default repo
            official_bweso = bweso['enabled'] and bweso['argo']['repo'] == repo

            # if local password manager is bitwarden/enabled or we're using bweso
            if local_bitwarden or official_bweso:
                self.get_bitwarden_credentials()
            else:
                self.app.exit([self.app.current_cluster, self.cfg, None])

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
