#!/usr/bin/env python3.11
from textual import on
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Container
from textual.binding import Binding
from textual.events import Mount
from textual.widgets import (Footer, Header, Label, Select, SelectionList,
                             Static, TabbedContent, TabPane)
from textual.widgets._toggle_button import ToggleButton
from textual.widgets.selection_list import Selection
from smol_k8s_lab.constants import (DEFAULT_APPS, DEFAULT_DISTRO,
                                    DEFAULT_DISTRO_OPTIONS)
from smol_k8s_lab.utils.tui.help_screen import HelpScreen
from smol_k8s_lab.utils.tui.app_config_pane import ArgoCDAppInputs
from smol_k8s_lab.utils.tui.kubelet_config import KubeletConfig
from smol_k8s_lab.utils.tui.k3s_config import K3sConfig
from smol_k8s_lab.utils.tui.node_adjustment import NodeAdjustmentBox


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
        self.previous_distro = DEFAULT_DISTRO
        super().__init__()

    def compose(self) -> ComposeResult:
        """
        Compose app with tabbed content.
        """
        header = Header()
        header.tall = True
        yield header
        # Footer to show keys
        yield Footer()

        # Add the TabbedContent widget
        with TabbedContent(initial="select-distro"):
            # tab 1 - select a kubernetes distro
            with TabPane("Select Kubernetes distro", id="select-distro"):
                select_prompt = ("[magenta]Select Kubernetes distro from this "
                                 f"dropdown (default: {DEFAULT_DISTRO})")

                # create all distro selection choices for the top of tabbed content
                my_options = tuple(DEFAULT_DISTRO_OPTIONS.keys())
                yield Select(((line, line) for line in my_options),
                             prompt=select_prompt,
                             id="distro-drop-down",
                             allow_blank=False,
                             value=DEFAULT_DISTRO)

                for distro, distro_metadata in DEFAULT_DISTRO_OPTIONS.items():
                    with VerticalScroll(classes=f"k8s-distro-config {distro}"):
                        if distro == DEFAULT_DISTRO:
                            display = True
                        else:
                            display = False

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
                        node_input_box = Container(adjust, classes=distro)
                        node_input_box.display = display
                        yield node_input_box

                        # kubelet config section
                        extra_args = distro_metadata['kubelet_extra_args']
                        kubelet_class = f"{distro} kubelet-config-container"
                        kubelet_box = Container(KubeletConfig(distro, extra_args),
                                                classes=kubelet_class)
                        kubelet_box.display = display
                        yield kubelet_box

                        # take extra k3s args
                        if distro == 'k3s' or distro == 'k3d':
                            if distro == 'k3s':
                                k3s_args = distro_metadata['extra_cli_args']
                            else:
                                k3s_args = distro_metadata['extra_k3s_cli_args']

                            k3s_box_classes = f"{distro} k3s-config-container"
                            k3s_box = Container(K3sConfig(distro, k3s_args),
                                                classes=k3s_box_classes)
                            k3s_box.display = display

                            yield k3s_box

                        # description box
                        desc = DEFAULT_DISTRO_OPTIONS[distro]['description']
                        desc_class = f"{distro} k8s-distro-description-container"
                        desc_box = Container(classes=desc_class)
                        desc_box.display = display
                        with desc_box:
                            formatted_description = format_description(desc)
                            yield Static(f"{formatted_description}",
                                         classes=f'{distro} k8s-distro-description')

            # tab 2 - allows selection of different argo cd apps to run in k8s
            with TabPane("Select Applications", id="select-apps"):
                full_list = []
                for app, app_meta in DEFAULT_APPS.items():
                    item = Selection(app.replace("_","-"), app, app_meta['enabled'])
                    full_list.append(item)

                selection_list = SelectionList[str](*full_list,
                                                    id='selection-list-of-apps')

                # top of the screen in second tab
                with Container(id="select-apps-container"):
                    # top left: the SelectionList of k8s applications
                    yield selection_list

                    # top right: vertically scrolling container for all inputs
                    with VerticalScroll(id='app-inputs-pane'):
                        for app, metadata in DEFAULT_APPS.items():
                            id_name = app.replace("_", "-") + "-inputs"
                            single_app_inputs_container = Container(id=id_name)
                            single_app_inputs_container.display = False
                            with single_app_inputs_container:
                                yield ArgoCDAppInputs(app, metadata)

                    # Bottom half of the screen for select-apps TabPane()
                    with VerticalScroll(id="app-description-container"):
                        yield Label("", id="app-description")

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
        select_apps_title = "[green]Select apps"
        self.query_one(SelectionList).border_title = select_apps_title

        # select-apps tab styling - bottom
        app_desc = self.get_widget_by_id("app-description-container")
        app_desc.border_title = "[white]App Description[/]"

        # styling for the select-distro tab - bottom
        distro_desc_boxes = self.query(".k8s-distro-description-container")
        for distro_desc_box in distro_desc_boxes:
            distro_desc_box.border_title = "[white]Distro Description[/]"

        # kuebelet config styling - middle
        kubelet_title = "➕ [green]Extra Args for Kubelet Config"
        kubelet_cfgs = self.query(".kubelet-config-container")
        for box in kubelet_cfgs:
            box.border_title = kubelet_title

        # k3s arg config sytling - middle
        k3s_title = "➕ [green]Extra Args for k3s install script"
        k3s_box = self.query_one(".k3s-config-container")
        k3s_box.border_title = k3s_title

    @on(Mount)
    @on(SelectionList.SelectedChanged)
    @on(SelectionList.SelectionHighlighted)
    @on(TabbedContent.TabActivated)
    def update_selected_app_blurb(self) -> None:
        selection_list = self.query_one(SelectionList)

        # only the highlighted index
        highlighted_idx = selection_list.highlighted

        # the actual highlighted app
        highlighted_app = selection_list.get_option_at_index(highlighted_idx).value

        # update the bottom app description to the highlighted_app's description
        blurb = format_description(DEFAULT_APPS[highlighted_app]['description'])
        self.get_widget_by_id('app-description').update(blurb)

        # styling for the select-apps tab - configure apps container - right
        app_title = highlighted_app.replace("_", "-")
        app_cfg_title = f"⚙️ [green]Configure initial params for [magenta]{app_title}"
        self.get_widget_by_id("app-inputs-pane").border_title = app_cfg_title

        if self.previous_app:
            dashed_app = self.previous_app.replace("_","-")
            app_input = self.get_widget_by_id(f"{dashed_app}-inputs")
            app_input.display = False

        dashed_app = highlighted_app.replace("_","-")
        app_input = self.get_widget_by_id(f"{dashed_app}-inputs")
        app_input.display = True

        self.previous_app = highlighted_app

    @on(Select.Changed)
    def update_k8s_distro_tab_view(self, event: Select.Changed) -> None:
        distro = str(event.value)

        if self.previous_distro:
            distro_class_objects = self.query(f".{self.previous_distro}")
            for distro_obj in distro_class_objects:
                distro_obj.display = False

        distro_class_objects = self.query(f".{distro}")

        # change display to True if the distro is selected
        if distro_class_objects:
            for distro_obj in distro_class_objects:
                distro_obj.display = True

        self.previous_distro = distro

    def action_request_help(self) -> None:
        """
        if the user presses 'h' or '?', show the help modal screen
        """
        self.push_screen(HelpScreen())


def format_description(description: str):
    """
    change description to dimmed colors
    links are changed to steel_blue and not dimmed
    """
    description = description.replace("[link", "[/dim][steel_blue][link")
    description = description.replace("[/link]", "[/link][/steel_blue][dim]")

    return f"""[dim]{description}[/dim]"""


if __name__ == "__main__":
    # this is temporary during testing
    from smol_k8s_lab.constants import INITIAL_USR_CONFIG
    reply = SmolK8sLabConfig(INITIAL_USR_CONFIG).run()
    print(reply)
