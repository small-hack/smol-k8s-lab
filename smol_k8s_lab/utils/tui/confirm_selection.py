#!/usr/bin/env python3.11
from smol_k8s_lab.utils.yaml_with_comments import syntax_highlighted_yaml
from smol_k8s_lab.utils.write_yaml import dump_to_file
from smol_k8s_lab.utils.tui.help import HelpScreen
from textual import on
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Container
from textual.binding import Binding
from textual.widgets import Button, Footer, Header, Label, SelectionList


class ConfirmConfig(App):
    """
    Textual app confirm smol-k8s-lab config
    """
    CSS_PATH = ["./css/confirm.tcss",
                "./css/help.tcss"]
    BINDINGS = [Binding(key="h,?",
                        key_display="h",
                        action="request_help",
                        description="Show Help",
                        show=True)]

    def __init__(self, user_config: dict, show_footer: bool = True) -> None:
        self.usr_cfg = user_config
        self.show_footer = show_footer
        self.invalid_app_inputs = {}
        super().__init__()

    def compose(self) -> ComposeResult:
        """
        Compose app with tabbed content.
        """
        # header to be cute
        yield Header()

        # Footer to show keys
        footer = Footer()
        if not self.show_footer:
            footer.display = False
        yield footer

        warning_label = Label("", id="invalid-apps")
        warning_label.display = False
        yield warning_label
        with Container(id="confirm-tab-container"):
            with VerticalScroll(id="pretty-yaml-scroll-container"):
                yield Label("", id="pretty-yaml")
            button = Button("🚊 Let's roll!", id="confirm-button")
            button.display = False
            yield button

    def on_mount(self) -> None:
        """
        screen and box border styling
        """
        self.title = "ʕ ᵔᴥᵔʔ smol k8s lab"
        self.sub_title = "now with more 🦑"

        # confirm box - last tab
        confirm_box = self.get_widget_by_id("pretty-yaml-scroll-container")
        confirm_box.border_title = "All Configured Values"

        rich_highlighted = syntax_highlighted_yaml(self.usr_cfg)
        self.get_widget_by_id("pretty-yaml").update(rich_highlighted)

        # if the app is selected
        selected = self.query_one(SelectionList).selected

        if self.invalid_app_inputs:
            warn = ("[yellow on black]⚠️ The following fields are invalid. "
                    "They either have errors or have not been filled out.[/]\n")
            at_least_one_missing_field = False
            for key, value in self.invalid_app_inputs.items():
                if value and key in selected:
                    at_least_one_missing_field = True
                    missing = "[/], [magenta]".join(value)
                    tabs = "\t"
                    if len(key) < 6:
                        tabs = "\t\t"
                    warn += f"\n [gold3]{key}[/]:{tabs}[magenta]{missing}[/]"
        if not at_least_one_missing_field:
            self.get_widget_by_id("invalid-apps").display = False
            self.get_widget_by_id("confirm-button").display = True
        else:
            self.get_widget_by_id("confirm-button").display = False
            self.get_widget_by_id("invalid-apps").display = True
            self.get_widget_by_id("invalid-apps").update(warn)

    def action_request_help(self) -> None:
        """
        if the user presses 'h' or '?', show the help modal screen
        """
        self.push_screen(HelpScreen())

    @on(Button.Pressed)
    def exit_app_and_return_new_config(self, event: Button.Pressed) -> dict:
        if event.button.id == "confirm-button":
            dump_to_file(self.usr_cfg)
            self.exit(self.usr_cfg)


if __name__ == "__main__":
    # this is temporary during testing
    from smol_k8s_lab.constants import INITIAL_USR_CONFIG
    reply = ConfirmConfig(INITIAL_USR_CONFIG['apps']).run()
    print(reply)
