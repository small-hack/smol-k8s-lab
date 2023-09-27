from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer
from smol_k8s_lab.utils.write_yaml import dump_to_file
from smol_k8s_lab.utils.tui.help import HelpScreen
from smol_k8s_lab.utils.tui.smol_k8s_config import SmolK8sLabConfig
from smol_k8s_lab.utils.tui.distro_config import DistroConfig
from smol_k8s_lab.utils.tui.apps_config import AppConfig
from smol_k8s_lab.constants import INITIAL_USR_CONFIG


class BaseApp(App):
    BINDINGS = [Binding(key="h,?",
                        key_display="h",
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
                        description="🐳 Select distros"),
                Binding(key="a",
                        key_display="a",
                        action="request_apps_cfg",
                        description="📱Select Apps")]

    CSS_PATH = ["./css/base.tcss",
                "./css/help.tcss"]

    def __init__(self,
                 user_config: dict = INITIAL_USR_CONFIG,
                 show_footer: bool = True) -> None:
        self.cfg = user_config
        self.show_footer = show_footer
        # self.previous_app = ''
        self.previous_screen = ''
        self.invalid_app_inputs = {}
        super().__init__()

    def compose(self) -> ComposeResult:
        """
        Compose app with screens
        """
        # Footer to show keys
        footer = Footer()
        if not self.show_footer:
            footer.display = False
        yield footer

    def action_request_apps_cfg(self) -> None:
        """
        launches the argo app config screen
        """
        # if there's currently a screen, remove it
        if self.previous_screen:
            self.app.pop_screen(self.previous_screen)

        self.app.push_screen(AppConfig(self.cfg['apps']))

    def action_request_distro_cfg(self) -> None:
        """
        launches the k8s disto (k3s,k3d,kind) config screen
        """
        if self.previous_screen:
            self.app.pop_screen(self.previous_screen)
        self.app.push_screen(DistroConfig(self.cfg['k8s_distros']))

    def action_request_smol_k8s_cfg(self) -> None:
        """
        launches the smol-k8s-lab config for the program itself for things like
        the TUI, but also logging and password management
        """
        if self.previous_screen:
            self.app.pop_screen(self.previous_screen)
        self.app.push_screen(SmolK8sLabConfig(self.cfg['smol_k8s_lab']))

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
