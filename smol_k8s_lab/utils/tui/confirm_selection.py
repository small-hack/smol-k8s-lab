#!/usr/bin/env python3.11
from smol_k8s_lab.utils.yaml_with_comments import syntax_highlighted_yaml
from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Grid
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label


class ConfirmConfig(Screen):
    """
    Textual app confirm smol-k8s-lab config
    """
    CSS_PATH = ["./css/confirm.tcss"]

    def __init__(self, user_config: dict, show_footer: bool = True) -> None:
        self.usr_cfg = user_config
        self.show_footer = show_footer
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

        # warning label if there's invalid apps
        warning_label = Label("", id="invalid-apps")
        warning_label.display = False
        yield warning_label

        with Grid(id="confirm-container"):
            # the actual yaml config in full
            with VerticalScroll(id="pretty-yaml-scroll-container"):
                yield Label("", id="pretty-yaml")

        # final confirmation button before running smol-k8s-lab
        with Grid(id="final-confirm-button-box"):
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
        confirm_box.border_title = "[gold3]All Configured Values"

        rich_highlighted = syntax_highlighted_yaml(self.usr_cfg)
        self.get_widget_by_id("pretty-yaml").update(rich_highlighted)

        at_least_one_missing_field = False
        invalid_root_app_inputs = self.ancestors[-1].invalid_app_inputs
        if invalid_root_app_inputs:
            warn = ("[yellow on black]⚠️ The following fields are invalid, "
                    "because they are either empty, or have errors.[/]\n")
            for key, value in invalid_root_app_inputs.items():
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

    @on(Button.Pressed)
    def exit_app_and_return_new_config(self, event: Button.Pressed) -> dict:
        if event.button.id == "confirm-button":
            self.exit(self.usr_cfg)
