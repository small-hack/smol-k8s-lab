#!/usr/bin/env python3.11
from rich.syntax import Syntax
from smol_k8s_lab.constants import DEFAULT_DISTRO_OPTIONS
from smol_k8s_lab.env_config import process_k8s_distros
from smol_k8s_lab.utils.tui.help_screen import HelpScreen
from smol_k8s_lab.utils.tui.app_config import ArgoCDAppInputs, ArgoCDNewInput
from smol_k8s_lab.utils.tui.kubelet_config import KubeletConfig
from smol_k8s_lab.utils.tui.k3s_config import K3sConfig
from smol_k8s_lab.utils.tui.node_adjustment import NodeAdjustmentBox
from textual import on
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Container
from textual.binding import Binding
from textual.events import Mount
from textual.widgets import (Button, Footer, Header, Label, Select,
                             SelectionList, TabbedContent, TabPane)
from textual.widgets._toggle_button import ToggleButton
from textual.widgets.selection_list import Selection
from yaml import safe_dump


class SmolK8sLabConfig(App):
    """
    Textual app to configure smol-k8s-lab
    """
    CSS_PATH = "./css/configure_all.tcss"
    BINDINGS = [Binding(key="h,?",
                        key_display="h",
                        action="request_help",
                        description="Show Help",
                        show=True),
                Binding(key="q",
                        key_display="q",
                        action="quit",
                        description="Quit smol-k8s-lab")]
    ToggleButton.BUTTON_INNER = '♥'

    def __init__(self, user_config: dict) -> None:
        self.usr_cfg = user_config
        self.previous_app = ''
        self.distros = self.usr_cfg['k8s_distros']
        self.previous_distro = process_k8s_distros(self.distros, False)[1]
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
        with TabbedContent(initial="select-distro"):
            # tab 1 - select a kubernetes distro
            with TabPane("Select Kubernetes distro", id="select-distro"):
                # create all distro selection choices for the top of tabbed content
                my_options = tuple(DEFAULT_DISTRO_OPTIONS.keys())
                d_select =  Select(((line, line) for line in my_options),
                                        id="distro-drop-down",
                                        allow_blank=False,
                                        value=self.previous_distro)

                d_select.tooltip = self.distros[self.previous_distro]['description']
                yield d_select

                for distro, distro_metadata in DEFAULT_DISTRO_OPTIONS.items():
                    # only display the default distro for this OS
                    if distro == self.previous_distro:
                        display = True
                    else:
                        display = False

                    distro_box = VerticalScroll(classes=f"k8s-distro-config {distro}",
                                                id=f"{distro}-box")
                    distro_box.display = display

                    with distro_box:
                        # take number of nodes from config and make string
                        nodes = distro_metadata.get('nodes', False)
                        if nodes:
                            control_nodes = str(nodes.get('control_plane', 1))
                            worker_nodes = str(nodes.get('workers', 0))
                        else:
                            control_nodes = "1"
                            worker_nodes = "0"

                        # node input row
                        adjust = NodeAdjustmentBox(distro, control_nodes, worker_nodes)
                        yield Container(adjust, classes=f"{distro} nodes-box")

                        # kubelet config section
                        extra_args = distro_metadata['kubelet_extra_args']
                        kubelet_class = f"{distro} kubelet-config-container"
                        yield Container(KubeletConfig(distro, extra_args),
                                        classes=kubelet_class)

                        # take extra k3s args
                        if distro == 'k3s' or distro == 'k3d':
                            if distro == 'k3s':
                                k3s_args = distro_metadata['extra_cli_args']
                            else:
                                k3s_args = distro_metadata['extra_k3s_cli_args']

                            k3s_box_classes = f"{distro} k3s-config-container"
                            yield Container(K3sConfig(distro, k3s_args),
                                            classes=k3s_box_classes)

            # tab 2 - allows selection of different argo cd apps to run in k8s
            with TabPane("Select Applications", id="select-apps"):
                full_list = []
                for app, app_meta in self.usr_cfg['apps'].items():
                    item = Selection(app.replace("_","-"), app, app_meta['enabled'])
                    full_list.append(item)

                selection_list = SelectionList[str](*full_list,
                                                    id='selection-list-of-apps')

                # top of the screen in second tab
                with Container(id="select-apps-container"):
                    # top left: the SelectionList of k8s applications
                    with VerticalScroll(id="select-add-apps"):
                        yield selection_list

                        # this button let's you create a new app
                        with Container(id="new-app-input-box"):
                            yield ArgoCDNewInput()

                    # top right: vertically scrolling container for all inputs
                    with VerticalScroll(id='app-inputs-pane'):
                        for app, metadata in self.usr_cfg['apps'].items():
                            app_inputs = VerticalScroll(id=f"{app}-inputs",
                                                        classes="single-app-inputs")
                            app_inputs.display = False
                            with app_inputs:
                                yield ArgoCDAppInputs(app, metadata)

                    # Bottom half of the screen for select-apps TabPane()
                    with VerticalScroll(id="app-description-container"):
                        yield Label("", id="app-description")

            # tab 3 - confirmation
            with TabPane("Confirm Selections", id="confirm-selection"):
                with Container(id="confirm-tab-container"):
                    with VerticalScroll(id="pretty-yaml-scroll-container"):
                        yield Label("", id="pretty-yaml")
                    yield Button("🚊 Let's roll!", id="confirm-button")

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
        self.query_one(SelectionList).border_title = "[green]Select apps"

        # select-apps tab styling - bottom
        app_desc = self.get_widget_by_id("app-description-container")
        app_desc.border_title = "[white]App Description[/]"

        # styling for the select-distro tab - bottom
        distro_desc_boxes = self.query(".k8s-distro-description-container")
        for distro_desc_box in distro_desc_boxes:
            distro_desc_box.border_title = "[white]Distro Description[/]"

        # kubelet config styling - middle
        kubelet_title = "➕ [green]Extra Parameters for Kubelet"
        kubelet_cfgs = self.query(".kubelet-config-container")
        for box in kubelet_cfgs:
            box.border_title = kubelet_title

        # k3s arg config sytling - middle
        k3s_title = "➕ [green]Extra Args for k3s install script"
        self.query_one(".k3s-config-container").border_title = k3s_title

        # confirm box - last tab
        confirm_box = self.get_widget_by_id("pretty-yaml-scroll-container")
        confirm_box.border_title = "All the configured values"


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
        blurb = format_description(self.usr_cfg['apps'][highlighted_app]['description'])
        self.get_widget_by_id('app-description').update(blurb)

        # styling for the select-apps tab - configure apps container - right
        app_title = highlighted_app.replace("_", "-")
        app_cfg_title = f"⚙️ [green]Configure initial params for [magenta]{app_title}"
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
            self.usr_cfg['apps'][app]['enabled'] = True
        else:
            self.usr_cfg['apps'][app]['enabled'] = False

    @on(Select.Changed)
    def update_k8s_distro(self, event: Select.Changed) -> None:
        distro = str(event.value)

        # disable display on previous distro
        if self.previous_distro:
            distro_obj = self.get_widget_by_id(f"{self.previous_distro}-box")
            distro_obj.display = False
            self.usr_cfg['k8s_distros'][self.previous_distro]['enabled'] = False

        # change display to True if the distro is selected
        distro_obj = self.get_widget_by_id(f"{distro}-box")
        distro_obj.display = True
        self.usr_cfg['k8s_distros'][distro]['enabled'] = True

        event.select.tooltip = self.usr_cfg['k8s_distros'][distro]["description"]

        self.previous_distro = distro

    def action_request_help(self) -> None:
        """
        if the user presses 'h' or '?', show the help modal screen
        """
        self.push_screen(HelpScreen())

    @on(TabbedContent.TabActivated)
    def update_yaml_print(self, event: TabbedContent.TabActivated) -> None:
        if event.tab.id == "confirm-selection":
            rich_highlighted = Syntax(safe_dump(self.usr_cfg),
                                      lexer="yaml",
                                      theme="github-dark",
                                      background_color="black")
            self.get_widget_by_id("pretty-yaml").update(rich_highlighted)


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
    reply = SmolK8sLabConfig(INITIAL_USR_CONFIG).run()
    print(reply)
