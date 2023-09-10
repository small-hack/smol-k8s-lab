#!/usr/bin/env python3.11
from textual.app import App, ComposeResult, Binding
from textual.containers import VerticalScroll
from textual.widgets import Input, Label, Rule, Footer, Header
from smol_k8s_lab.env_config import DEFAULT_CONFIG


DEFAULT_APPS = DEFAULT_CONFIG['apps']


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
        header = Header()
        header.tall = True
        yield header
        with VerticalScroll():
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
        yield Footer()

    def on_mount(self) -> None:
        self.screen.styles.border = ("heavy", "cornflowerblue")
        self.title = "🧸smol k8s lab"
        self.sub_title = "now with more 🦑"


if __name__ == "__main__":
    app = ConfigureApps()
    app.run()
