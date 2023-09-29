#!/usr/bin/env python3.11
from smol_k8s_lab.utils.yaml_with_comments import syntax_highlighted_yaml
from textual import on
from textual.binding import Binding
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Grid
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label


class ConfirmConfig(Screen):
    """
    Textual app confirm smol-k8s-lab config
    """
    CSS_PATH = ["./css/confirm.tcss"]

    BINDINGS = [Binding(key="escape,q",
                        key_display="esc,q",
                        action="app.pop_screen",
                        description="↩ Back")]

    def __init__(self, config: dict, show_footer: bool = True) -> None:
        self.cfg = config
        self.show_footer = show_footer
        self.invalid_apps = {}
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

        with Grid(id="confirm-container"):
            # warning label if there's invalid apps
            warning_label = Label("Click the app links below to fix the errors.",
                                  id="warning-help")
            warning_box = Grid(warning_label, id="invalid-apps")
            warning_box.display = False
            yield warning_box

            # the actual yaml config in full
            with VerticalScroll(id="pretty-yaml-scroll-container"):
                yield Label("", id="pretty-yaml")

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
        self.sub_title = "all configuration confirmation"

        # confirm box title styling
        confirm_box = self.get_widget_by_id("pretty-yaml-scroll-container")
        confirm_box.border_title = "[gold3]All Configured Values"

        # display the current user yaml
        rich_highlighted = syntax_highlighted_yaml(self.cfg)
        self.get_widget_by_id("pretty-yaml").update(rich_highlighted)

        # invalid apps error title styling
        invalid_box = self.get_widget_by_id("invalid-apps")
        invalid_box.border_title = "[gold3]⚠️ The following app fields are empty"

        # go check all the app inputs
        self.get_app_inputs()

        at_least_one_missing_field = False
        if self.invalid_apps:
            at_least_one_missing_field = True

        if not at_least_one_missing_field:
            self.get_widget_by_id("invalid-apps").display = False
            self.get_widget_by_id("pretty-yaml-scroll-container").display = True
            self.get_widget_by_id("confirm-button").display = True
            self.get_widget_by_id("back-button").display = True
        else:
            self.get_widget_by_id("pretty-yaml-scroll-container").display = False
            self.get_widget_by_id("confirm-button").display = False
            self.get_widget_by_id("invalid-apps").display = True
            self.build_pretty_nope()

    def get_app_inputs(self) -> None:
        """
        processes the entire apps config to check for empty fields
        """
        config = self.ancestors[-1].cfg['apps']

        for app, metadata in config.items():
            empty_fields = check_for_invalid_inputs(metadata)
            if empty_fields:
                self.invalid_apps[app] = empty_fields

    def build_pretty_nope(self) -> None:
        """
        No, but with flare ✨
        """
        nope_container = self.get_widget_by_id("invalid-apps")

        for app, fields in self.invalid_apps.items():
            app_link = f'app.request_apps_cfg("{app}")'
            label = Label(f"[yellow][@click='{app_link}']{app}[/]:",
                          classes="nope-label nope-link")
            nopes = Label("[magenta]" + "[/], [magenta]".join(fields),
                          classes="nope-fields")
            nope_row = Grid(label, nopes, classes="nope-row")
            nope_container.mount(nope_row)

    @on(Button.Pressed)
    def exit_app_and_return_new_config(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm-button":
            self.ancestors[-1].exit(self.ancestors[-1].cfg)
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
