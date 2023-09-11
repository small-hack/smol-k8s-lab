#!/usr/bin/env python3.11
from textual.app import App, ComposeResult, Binding
from textual.containers import VerticalScroll
from textual.widgets import Input, Label, Rule, Footer, Header, TabbedContent, TabPane
from smol_k8s_lab.constants import DEFAULT_APPS


class ConfigureApps(App):
    """
    class helps the user configure specific custom values for applications such
    as hostnames and timezones
    """
    CSS_PATH = "./css/configure_apps.tcss"
    BINDINGS = [
        Binding(key="tab",
                action="focus_next",
                description="Focus next",
                show=True),
        Binding(key="q",
                key_display="q",
                action="quit",
                description="Quit smol-k8s-lab")
    ]

    def compose(self) -> ComposeResult:
        """Compose app with tabbed content."""
        header = Header()
        header.tall = True
        yield header
        # Footer to show keys
        yield Footer()

        # Add the TabbedContent widget
        with TabbedContent(initial="pual"):
            # with VerticalScroll():
            with TabPane("Leto", id="leto"):  # First tab
                yield Label(" ")
                for app, metadata in DEFAULT_APPS.items():
                    secret_keys = metadata['argo'].get('secret_keys', None)
                    init = metadata.get('init', None)
                    if init:
                        init_enabled = metadata['init'].get('enabled', False)
                    else:
                        init_enabled = False

                    if metadata['enabled'] and secret_keys and init_enabled:
                        yield Label(app)
                        for secret_key, value in secret_keys.items():
                            if not value:
                                yield Input(placeholder=secret_key)
                            else:
                                yield Input(placeholder=value)
                        yield Rule()

            with TabPane("Paul", id="paul"):
                yield Label("PAUL")

    def action_show_tab(self, tab: str) -> None:
        """Switch to a new tab."""
        self.get_child_by_type(TabbedContent).active = tab

    def on_mount(self) -> None:
        self.screen.styles.border = ("heavy", "cornflowerblue")
        self.title = "🧸smol k8s lab"
        self.sub_title = "now with more 🦑"


if __name__ == "__main__":
    app = ConfigureApps()
    app.run()
