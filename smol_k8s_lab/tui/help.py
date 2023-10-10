#!/usr/bin/env python3.11
from textual.app import ComposeResult
from textual.containers import Container, Grid
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Label


class HelpScreen(ModalScreen):
    """
    dialog screen to show help text
    """
    BINDINGS = [Binding(key="?,q,escape",
                        key_display="h",
                        action="disable_help",
                        description="Exit Help Screen",
                        show=True)
                ]

    def compose(self) -> ComposeResult:
        link_help = ("open link; terminal dependent, so [gold3]meta[/gold3] can"
                     " be shift, option, windowsKey, command, or control")

        # tips for new/forgetful users (the maintainers are also forgetful <3)
        help_dict = {
                "→": "complete suggestion in input field",
                "⬆/⬇": "navigate up and down the app selection list",
                "tab": "go to next input field, switch, selection, or button",
                "shift+tab": "go to previous input field, switch, selection, or button",
                "↩ enter": "save input and/or press button",
                "?": "toggle help screen",
                "spacebar": "select selection option",
                "meta+click": link_help,
                "escape,q": "leave current screen and go home"
                }

        welcome = ("Use your 🐁 to click anything in the UI ✨ Or use these "
                   "key bindings:")

        with Container(id="help-container"):
            yield Label(welcome, id="help-label")
            with Container(id="help-options"):
                # TODO: convert to data table widget
                for help_option, help_text in help_dict.items():
                    with Grid(classes="help-option-row"):
                        key = help_option.replace("/", "[bright_white]/[/]")
                        key = key.replace(",", "[bright_white],[/]")
                        key = key.replace("+", "[bright_white]+[/]")
                        yield Label(f"[gold3]{key}[/gold3]")
                        yield Label(help_text, classes="help-text")

    def on_mount(self) -> None:
        # styling for the select-apps tab - select apps container - left
        select_apps_title = ('[steel_blue1]Welcome to [u]'
                             '[link=https://github.com/small-hack/smol-k8s-lab]'
                             'smol-k8s-lab[/link]')
        help_container = self.get_widget_by_id("help-container")
        help_container.border_title = select_apps_title
        help_container.border_subtitle = "made with 💙 + 🐍 + [u][link=https://github.com/Textualize/textual]textual[/u]"


    def action_disable_help(self) -> None:
        """
        if user presses '?', 'h', or 'q', we exit the help screen
        """
        self.app.pop_screen()
