from textual.app import App, ComposeResult, ScreenStackError
from textual.binding import Binding
from textual.containers import Grid, Container
from textual.widgets import Footer, Header, Button
from smol_k8s_lab.utils.write_yaml import dump_to_file
from smol_k8s_lab.utils.tui.apps_config import AppConfig
from smol_k8s_lab.utils.tui.confirm_selection import ConfirmConfig
from smol_k8s_lab.utils.tui.distro_config import DistroConfig
from smol_k8s_lab.utils.tui.help import HelpScreen
from smol_k8s_lab.utils.tui.smol_k8s_config import SmolK8sLabConfig
from smol_k8s_lab.constants import INITIAL_USR_CONFIG


class BaseApp(App):
    BINDINGS = [Binding(key="?",
                        key_display="?",
                        action="request_help",
                        description="Show Help",
                        show=True),
                Binding(key="s",
                        key_display="s",
                        action="request_smol_k8s_cfg",
                        description="⚙️ config"),
                Binding(key="d",
                        key_display="d",
                        action="request_distro_cfg",
                        description="🐳 distros"),
                Binding(key="a",
                        key_display="a",
                        action="request_apps_cfg",
                        description="📱Apps"),
                Binding(key="c",
                        key_display="c",
                        action="request_confirm",
                        description="✅ Confirm")
                ]

    CSS_PATH = ["./css/base.tcss",
                "./css/help.tcss"]

    def __init__(self, user_config: dict = INITIAL_USR_CONFIG) -> None:
        self.cfg = user_config
        self.show_footer = self.cfg['smol_k8s_lab']['interactive']['show_footer']
        self.previous_screen = ''
        self.invalid_app_inputs = {}
        super().__init__()

    def compose(self) -> ComposeResult:
        """
        Compose app with screens
        """
        yield Header()

        # Footer to show keys
        footer = Footer()

        if not self.show_footer:
            footer.display = False
        yield footer

        with Grid(id="base-screen-container"):
            with Grid(id="base-button-grid"):
                # config smol k8s lab button
                smol_cfg_button = Button("🧸smol-k8s-lab", id="smol-cfg")
                smol_cfg_button.tooltip = (
                        "Configure smol-k8s-lab itself from password management, "
                        "to logging, to the terminal UI. Hot key: s"
                        )
                yield smol_cfg_button

                # config distro button
                distro_cfg_button = Button("🐳 k8s distro", id="distro-cfg")
                distro_cfg_button.tooltip = (
                        "Select and configure a kubernetes distribution. "
                        "Hot key: d"
                        )
                yield distro_cfg_button

                # config apps button
                apps_cfg_button = Button("📱k8s apps", id="apps-cfg")
                apps_cfg_button.tooltip = (
                        "Select and configure Kubernetes applications via Argo CD."
                        " Hot key: a"
                        )
                yield apps_cfg_button

            with Container(id="first-confirm-button-row"):
                confirm_button = Button("✅ confirm settings", id="confirm-cfg")
                confirm_button.tooltip = (
                        "Confirm all your settings and run smol-k8s-lab"
                        " Hot key: c"
                        )
                yield confirm_button

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        get pressed button add or delete button and act on it
        """
        button_id = event.button.id

        if button_id == "smol-cfg":
            self.action_request_smol_k8s_cfg()
        elif button_id == "distro-cfg":
            self.action_request_distro_cfg()
        elif button_id == "apps-cfg":
            self.action_request_apps_cfg()
        elif button_id == "confirm-cfg":
            self.action_request_confirm()

    def on_mount(self) -> None:
        """
        screen and box border styling
        """
        self.title = "ʕ ᵔᴥᵔʔ smol k8s lab"
        self.sub_title = "Getting Started"

        grid_title = "[green]Let's get started configuring a new cluster 🪛"
        self.get_widget_by_id("base-button-grid").border_title = grid_title


    def action_request_apps_cfg(self, app_to_highlight: str = "") -> None:
        """
        launches the argo app config screen
        """
        try:
            self.app.pop_screen()
        # this error happens if there's not already a screen on the stack
        except ScreenStackError:
            pass

        if app_to_highlight:
            self.app.push_screen(AppConfig(self.cfg['apps'],
                                           app_to_highlight,
                                           self.show_footer))
        else:
            self.app.push_screen(AppConfig(self.cfg['apps'], "", self.show_footer))

    def action_request_distro_cfg(self) -> None:
        """
        launches the k8s disto (k3s,k3d,kind) config screen
        """
        try:
            self.app.pop_screen()
        # this error happens if there's not already a screen on the stack
        except ScreenStackError:
            pass

        self.app.push_screen(DistroConfig(self.cfg['k8s_distros'], self.show_footer))

    def action_request_smol_k8s_cfg(self) -> None:
        """
        launches the smol-k8s-lab config for the program itself for things like
        the TUI, but also logging and password management
        """
        try:
            self.app.pop_screen()
        # this error happens if there's not already a screen on the stack
        except ScreenStackError:
            pass

        self.app.push_screen(SmolK8sLabConfig(self.cfg['smol_k8s_lab'],
                                              self.show_footer))

    def action_request_confirm(self) -> None:
        """
        show confirmation screen
        """
        try:
            self.app.pop_screen()
        # this error happens if there's not already a screen on the stack
        except ScreenStackError:
            pass

        self.app.push_screen(ConfirmConfig(self.cfg, self.show_footer))

    def action_request_help(self) -> None:
        """
        if the user presses 'h' or '?', show the help modal screen
        """
        self.push_screen(HelpScreen())

    def write_yaml(self) -> None:
        dump_to_file(self.cfg)

if __name__ == "__main__":
    app = BaseApp()
    app.run()
