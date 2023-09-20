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
    BINDINGS = [Binding(key="h,?,q",
                        key_display="h",
                        action="disable_help",
                        description="Exit Help Screen",
                        show=True)
                ]

    def compose(self) -> ComposeResult:
        link_help = ("open link; terminal dependent, so [gold3]meta"
                     "[/gold3] can be shift, option, windowsKey, command, or "
                     "control )")

        # tips for new/forgetful users (the maintainers are also forgetful <3)
        help_dict = {"left arrow key,right arrow key": "Switch tabs if tabs are selected",
                     "right arrow key": "complete suggestion in input field",
                     "tab": "switch to next box, field, or button",
                     "shift +tab": "switch to previous pane, field, or button",
                     "enter": "press button",
                     "h,?": "toggle help screen",
                     "meta+click": link_help}

        welcome = ("Use your 🐁 to click anything in this UI ✨ Or use "
                   "these key bindings:")

        with Container(id="help-container"):
            yield Label(welcome, id="help-label")
            with Container(id="help-options"):
                # TODO: convert to data table widget
                for help_option, help_text in help_dict.items():
                    with Grid(classes="help-option-row"):
                        key = f"[gold3]{help_option}[/gold3]"
                        key = key.replace(",", "[bright_white],[/]")
                        key = key.replace("+", "[bright_white]+[/]")
                        yield Label(key)
                        yield Label(help_text, classes="help-text")

    def on_mount(self) -> None:
        # styling for the select-apps tab - select apps container - left
        select_apps_title = 'Welcome to [i][link="https://github.com/small-hack/smol-k8s-lab"]smol-k8s-lab[/link][/i]'
        help_container = self.get_widget_by_id("help-container")
        help_container.border_title = select_apps_title
        help_container.border_subtitle = "made with 💙 + 🐍 + [u][link=https://github.com/Textualize/textual]textual[/u]"


    def action_disable_help(self) -> None:
        """
        if user presses '?', 'h', or 'q', we exit the help screen
        """
        self.app.pop_screen()
