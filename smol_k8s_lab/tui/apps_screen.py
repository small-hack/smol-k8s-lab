#!/usr/bin/env python3.11
# smol-k8s-lab libraries
from smol_k8s_lab.tui.app_widgets.app_inputs_confg import AppInputs
from smol_k8s_lab.tui.app_widgets.new_app_modal import NewAppModalScreen
from smol_k8s_lab.tui.app_widgets.modify_globals import ModifyAppGlobals
from smol_k8s_lab.tui.util import format_description

# external libraries
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll, Container, Grid
from textual.css.query import NoMatches
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, SelectionList
from textual.widgets._toggle_button import ToggleButton
from textual.widgets.selection_list import Selection


class AppsConfig(Screen):
    """
    Textual app to smol-k8s-lab applications
    """
    CSS_PATH = ["./css/apps_config.tcss",
                "./css/apps_init_config.tcss"]

    BINDINGS = [Binding(key="b,escape,q",
                        key_display="b",
                        action="app.pop_screen",
                        description="Back"),
                Binding(key="a",
                        key_display="a",
                        action="screen.launch_new_app_modal",
                        description="New App"),
                Binding(key="n",
                        key_display="n",
                        action="app.request_smol_k8s_cfg",
                        description="Next")]

    ToggleButton.BUTTON_INNER = '♥'

    def __init__(self, config: dict, highlighted_app: str = "") -> None:
        # show the footer at bottom of screen or not
        self.show_footer = self.app.cfg['smol_k8s_lab']['tui']['show_footer']

        # should be the apps section of smol k8s lab config
        self.cfg = config

        # this is state storage
        self.previous_app = ''

        # inital highlight if we got here via a link
        self.initial_app = highlighted_app

        super().__init__()

    def compose(self) -> ComposeResult:
        """
        Compose app with for app input content
        """
        # header to be cute
        yield Header()

        # Footer to show keys
        footer = Footer()
        if not self.show_footer:
            footer.display = False
        yield footer

        full_list = []
        for app, app_meta in self.cfg.items():
            item = Selection(app.replace("_","-"), app, app_meta['enabled'])
            full_list.append(item)

        selection_list = SelectionList[str](*full_list,
                                            id='selection-list-of-apps')

        with Container(id="apps-config-container"):
            # top left: the SelectionList of k8s applications
            with Grid(id="left-apps-container"):
                with VerticalScroll(id="select-add-apps"):
                    yield selection_list

                with Grid(id="left-button-box"):
                    # yield AddAppInput()
                    yield ModifyAppGlobals()

            # top right: vertically scrolling container for all inputs
            yield VerticalScroll(id='app-inputs-pane')

            # Bottom half of the screen for select-apps
            with VerticalScroll(id="app-notes-container"):
                yield Label("", id="app-description")

    def on_mount(self) -> None:
        """
        screen and box border styling
        """
        self.title = "ʕ ᵔᴥᵔʔ smol k8s lab"
        sub_title = "Apps Configuration (now with more 🦑)"
        self.sub_title = sub_title

        # select-apps styling - select apps container - top left 
        select_apps_widget = self.get_widget_by_id("select-add-apps")
        select_apps_widget.border_title = "[#ffaff9]♥[/] [i]select[/] [#C1FF87]apps"
        select_apps_widget.border_subtitle = "[@click=screen.launch_new_app_modal]✨ [i]new[/] [#C1FF87]app[/][/]"

        if self.app.speak_screen_titles:
            # if text to speech is on, read screen title
            self.app.action_say(
                    "Screen title: Apps Configuration, now with more squid. "
                    "Here you can select and configure Argo CD directory-type apps."
                    )

        # scroll down to specific app if requested
        if self.initial_app:
            self.scroll_to_app(self.initial_app)

    def action_launch_new_app_modal(self) -> None:
        def get_new_app(app_response):
            app_name = app_response[0]
            app_description = app_response[1]

            if app_name and app_description:
                self.create_new_app_in_yaml(app_name, app_description)

        self.app.push_screen(NewAppModalScreen(["argo-cd"]), get_new_app)

    def scroll_to_app(self, app_to_highlight: str) -> None:
        """ 
        lets you scroll down to the exact app you need in the app selection list
        """
        # get the apps selection list
        apps = self.query_one(SelectionList)

        # get the app name for the highlighted index
        highlight_app = apps.get_option_at_index(apps.highlighted).value

        # while the highlighted app is not app_to_highlight, keep scrolling
        while highlight_app != app_to_highlight:
            apps.action_cursor_down()
            highlight_app = apps.get_option_at_index(apps.highlighted).value

    @on(SelectionList.SelectionHighlighted)
    def update_highlighted_app_view(self) -> None:
        selection_list = self.query_one(SelectionList)

        # only the highlighted index
        highlighted_idx = selection_list.highlighted

        # the actual highlighted app
        highlighted_app = selection_list.get_option_at_index(highlighted_idx).value

        if self.app.speak_on_focus:
            self.app.action_say(f"highlighted app is {highlighted_app}")

        # update the bottom app description to the highlighted_app's description
        blurb = format_description(self.cfg[highlighted_app]['description'])
        self.get_widget_by_id('app-description').update(blurb)

        # styling for the select-apps - configure apps container - right
        app_title = highlighted_app.replace("_", " ").title()
        app_cfg_title = f"🔧 [i]configure[/] parameters for [#C1FF87]{app_title}"
        self.get_widget_by_id("app-inputs-pane").border_title = app_cfg_title

        if self.previous_app != "":
            app_input = self.get_widget_by_id(f"{self.previous_app}-inputs")
            app_input.display = False

        try:
            app_input = self.get_widget_by_id(f"{highlighted_app}-inputs")
            app_input.display = True
        except NoMatches:
            app_metadata = self.cfg[highlighted_app]
            app_input = VerticalScroll(AppInputs(highlighted_app, app_metadata),
                                       id=f"{highlighted_app}-inputs",
                                       classes="single-app-inputs")
            self.get_widget_by_id("app-inputs-pane").mount(app_input)

        # select-apps styling - bottom
        app_desc = self.get_widget_by_id("app-notes-container")
        app_desc.border_title = f"📓 {app_title} [i]notes[/i]"

        self.previous_app = highlighted_app

    @on(SelectionList.SelectionToggled)
    def update_selected_apps(self, event: SelectionList.SelectionToggled) -> None:
        """ 
        when a selection list item is checked or unchecked, update the base app yaml
        """
        selection_list = self.query_one(SelectionList)
        app = selection_list.get_option_at_index(event.selection_index).value
        if app in selection_list.selected:
            self.app.cfg['apps'][app]['enabled'] = True
        else:
            self.app.cfg['apps'][app]['enabled'] = False

        self.app.write_yaml()

    def create_new_app_in_yaml(self, app_name: str, app_description: str = "") -> None:
        underscore_name = app_name.replace(" ", "_").replace("-", "_")

        # updates the base user yaml
        self.app.cfg['apps'][underscore_name] = {
            "enabled": True,
            "description": app_description,
            "argo": {
                "secret_keys": {},
                "repo": "",
                "path": "",
                "revision": "",
                "namespace": "",
                "directory_recursion": False,
                "project": {
                    "source_repos": [""],
                    "destination": {
                        "namespaces": ["argocd"]
                        }
                    }
                }
            }

        # adds selection to the app selection list
        apps = self.app.get_widget_by_id("selection-list-of-apps")
        apps.add_option(Selection(underscore_name.replace("_", "-"),
                                  underscore_name, True))

        # scroll down to the new app
        apps.action_last()
