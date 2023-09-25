#!/usr/bin/env python3.11
from smol_k8s_lab.utils.yaml_with_comments import syntax_highlighted_yaml
from smol_k8s_lab.utils.write_yaml import dump_to_file
from smol_k8s_lab.utils.tui.help import HelpScreen
from smol_k8s_lab.utils.tui.app_widgets.app_inputs_confg import (ArgoCDAppInputs,
                                                                 ArgoCDNewInput)
from textual import on
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Container
from textual.binding import Binding
from textual.events import Mount
from textual.widgets import (Button, Footer, Header, Label, SelectionList,
                             TabbedContent, TabPane)
from textual.widgets._toggle_button import ToggleButton
from textual.widgets.selection_list import Selection


class AppConfig(App):
    """
    Textual app to smol-k8s-lab applications
    """
    CSS_PATH = ["./css/apps_config.tcss",
                "./css/help.tcss"]
    BINDINGS = [Binding(key="h,?",
                        key_display="h",
                        action="request_help",
                        description="Show Help",
                        show=True)]
    ToggleButton.BUTTON_INNER = '♥'

    def __init__(self, user_config: dict) -> None:
        self.usr_cfg = user_config
        self.previous_app = ''
        self.invalid_app_inputs = {}
        super().__init__()

    def compose(self) -> ComposeResult:
        """
        Compose app with tabbed content.
        """
        # header to be cute
        yield Header()
        # Footer to show keys
        yield Footer()

        # Add the TabbedContent widget
        with TabbedContent(initial="select-apps"):
            # tab 1 - allows selection of different argo cd apps to run in k8s
            with TabPane("Select Applications", id="select-apps"):
                full_list = []
                for app, app_meta in self.usr_cfg.items():
                    self.invalid_app_inputs[app] = []
                    item = Selection(app.replace("_","-"), app, app_meta['enabled'])
                    full_list.append(item)

                selection_list = SelectionList[str](*full_list,
                                                    id='selection-list-of-apps')

                # top of the screen in second tab
                with Container(id="select-apps-container"):
                    # top left: the SelectionList of k8s applications
                    with Container(id="left-apps-container"):
                        with VerticalScroll(id="select-add-apps"):
                            yield selection_list

                        # this button let's you create a new app
                        with Container(id="new-app-input-box"):
                            yield ArgoCDNewInput()

                    # top right: vertically scrolling container for all inputs
                    with VerticalScroll(id='app-inputs-pane'):
                        for app, metadata in self.usr_cfg.items():
                            app_inputs = VerticalScroll(id=f"{app}-inputs",
                                                        classes="single-app-inputs")
                            app_inputs.display = False
                            with app_inputs:
                                yield ArgoCDAppInputs(app, metadata)

                    # Bottom half of the screen for select-apps TabPane()
                    with VerticalScroll(id="app-description-container"):
                        yield Label("", id="app-description")

            # tab 2 - confirmation
            with TabPane("Confirm Selections", id="confirm-selection"):
                warning_label = Label("", id="invalid-apps")
                warning_label.display = False
                yield warning_label
                with Container(id="confirm-tab-container"):
                    with VerticalScroll(id="pretty-yaml-scroll-container"):
                        yield Label("", id="pretty-yaml")
                    button = Button("🚊 Let's roll!", id="confirm-button")
                    button.display = False
                    yield button

    def action_show_tab(self, tab: str) -> None:
        """Switch to a new tab."""
        self.get_child_by_type(TabbedContent).active = tab

    def on_mount(self) -> None:
        """
        screen and box border styling
        """
        self.title = "ʕ ᵔᴥᵔʔ smol k8s lab"
        self.sub_title = "now with more 🦑"

        # select-apps tab styling - select apps container - top left
        select_apps_widget = self.get_widget_by_id("select-add-apps")
        select_apps_widget.border_title = "[magenta]♥ [/][green]Select apps"

        # select-apps tab styling - bottom
        app_desc = self.get_widget_by_id("app-description-container")
        app_desc.border_title = "[white]App Description[/]"

        # confirm box - last tab
        confirm_box = self.get_widget_by_id("pretty-yaml-scroll-container")
        confirm_box.border_title = "All Configured Values"


    @on(Mount)
    @on(SelectionList.SelectionHighlighted)
    @on(TabbedContent.TabActivated)
    def update_highlighted_app_view(self) -> None:
        selection_list = self.query_one(SelectionList)

        # only the highlighted index
        highlighted_idx = selection_list.highlighted

        # the actual highlighted app
        highlighted_app = selection_list.get_option_at_index(highlighted_idx).value

        # update the bottom app description to the highlighted_app's description
        blurb = format_description(self.usr_cfg[highlighted_app]['description'])
        self.get_widget_by_id('app-description').update(blurb)

        # styling for the select-apps tab - configure apps container - right
        app_title = highlighted_app.replace("_", "-")
        app_cfg_title = f"⚙️ [green]Configure Parameters for [steel_blue1]{app_title}"
        self.get_widget_by_id("app-inputs-pane").border_title = app_cfg_title

        if self.previous_app:
            app_input = self.get_widget_by_id(f"{self.previous_app}-inputs")
            app_input.display = False

        app_input = self.get_widget_by_id(f"{highlighted_app}-inputs")
        app_input.display = True

        self.previous_app = highlighted_app

    @on(SelectionList.SelectionToggled)
    def update_selected_apps(self, event: SelectionList.SelectionToggled) -> None:
        selection_list = self.query_one(SelectionList)
        app = selection_list.get_option_at_index(event.selection_index).value
        if app in selection_list.selected:
            self.usr_cfg[app]['enabled'] = True
        else:
            self.usr_cfg[app]['enabled'] = False

    def action_request_help(self) -> None:
        """
        if the user presses 'h' or '?', show the help modal screen
        """
        self.push_screen(HelpScreen())

    @on(TabbedContent.TabActivated)
    def update_confirm_tab(self, event: TabbedContent.TabActivated) -> None:
        if event.tab.id == "confirm-selection":
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

    @on(Button.Pressed)
    def exit_app_and_return_new_config(self, event: Button.Pressed) -> dict:
        if event.button.id == "confirm-button":
            dump_to_file(self.usr_cfg)
            self.exit(self.usr_cfg)


def format_description(description: str = ""):
    """
    change description to dimmed colors
    links are changed to steel_blue and not dimmed
    """
    if not description:
        description = "No Description provided yet for this user defined application."

    description = description.replace("[link", "[/dim][steel_blue][link")
    description = description.replace("[/link]", "[/link][/steel_blue][dim]")

    return f"""[dim]{description}[/dim]"""


if __name__ == "__main__":
    # this is temporary during testing
    from smol_k8s_lab.constants import INITIAL_USR_CONFIG
    reply = AppConfig(INITIAL_USR_CONFIG['apps']).run()
    print(reply)
