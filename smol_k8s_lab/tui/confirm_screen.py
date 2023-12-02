#!/usr/bin/env python3.11
# smol-k8s-lab libraries
from smol_k8s_lab.bitwarden.tui.bitwarden_credentials_modal_screen import (
        BitwardenCredentialsScreen)
from smol_k8s_lab.utils.yaml_with_comments import syntax_highlighted_yaml

# external libraries
from os import environ as env
from textual import on
from textual.binding import Binding
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Grid
from textual.screen import Screen
from textual.widgets import (Button, Footer, Header, Label, TabbedContent,
                             TabPane)


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
        self.show_footer = self.smol_k8s_cfg['tui']['show_footer']
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
            yield confirm

            back = Button("✋Go Back", id="back-button")
            yield back

    def on_mount(self) -> None:
        """
        screen and box border styling
        """
        self.title = "ʕ ᵔᴥᵔʔ smol k8s lab"
        sub_title = "Review your configuration (last step!)"
        self.sub_title = sub_title

        if self.app.speak_screen_titles:
            # if text to speech is on, read screen title
            self.app.action_say("Screen title: Review your configuration last step")

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
            tab.add_class("header-tab")

    def action_show_tab(self, tab: str) -> None:
        """Switch to a new tab."""
        self.get_child_by_type(TabbedContent).active = tab

    def get_bitwarden_credentials(self) -> None:
        """
        check if we need to grab the bitwarden password & client_secret/id
        """

        def process_modal_output(credentials: dict):
            """
            Exit with credentials
            """
            if credentials:
                self.append_sensitive_values()
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
            self.append_sensitive_values()
            self.app.exit([self.app.current_cluster,
                           self.cfg,
                           {'password': password,
                            'client_id': client_id,
                            'client_secret': client_secret}])

    def append_sensitive_values(self) -> None:
        """
        if this app has SENSITIVE values, append them before we dismiss
        """
        for app, values in self.app.sensitive_values.items():
            if values:
                if self.cfg['apps'][app]['enabled']:
                    for key, value in values.items():
                        self.cfg['apps'][app]['init']['values'][key] = value

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
            pw_mngr = self.smol_k8s_cfg['local_password_manager']
            secrets_provider = self.cfg['apps_global_config']['external_secrets']
            
            # if local_password_manager is enabled, and is bitwarden
            local_bitwarden = pw_mngr['enabled'] and pw_mngr['name'] == "bitwarden"

            # if local password manager is bitwarden/enabled or we're using bweso
            if local_bitwarden or secrets_provider == 'bitwarden':
                self.get_bitwarden_credentials()
            else:
                self.append_sensitive_values()
                self.app.exit([self.app.current_cluster, self.cfg, None])

        if event.button.id == "back-button":
            self.app.pop_screen()
