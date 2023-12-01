#!/usr/bin/env python3.11
# smol-k8s-lab libraries
from smol_k8s_lab.constants import DEFAULT_DISTRO_OPTIONS
from smol_k8s_lab.env_config import process_k8s_distros
from smol_k8s_lab.tui.distro_widgets.k3s_config import K3sConfig
from smol_k8s_lab.tui.distro_widgets.kind_networking import KindNetworkingConfig
from smol_k8s_lab.tui.distro_widgets.kubelet_config import KubeletConfig
from smol_k8s_lab.tui.distro_widgets.node_adjustment import NodeAdjustmentBox
from smol_k8s_lab.tui.util import NewOptionModal

# external libraries
from textual import on
from textual.app import ComposeResult, NoMatches
from textual.binding import Binding
from textual.containers import Grid
from textual.screen import Screen
from textual.widgets import (Footer, Header, Label, Select, TabbedContent,
                             TabPane, Static)


# the description of the k8s distro
DISTRO_DESC = {
        "k3s": ("K3s, by Rancher Labs, is a minimal Kubernetes distro that fits in "
                "about 70MB. (it's also optomized for ARM) Learn more: "
                "[steel_blue][b][link=https://k3s.io]k3s.io[/][/]."),
        "k3d": ("k3d is a lightweight wrapper to run k3s (Rancher Lab’s minimal "
                "Kubernetes distribution) in Docker containers. Learn more: "
                "[steel_blue][b][link=https://k3d.io]k3d.io[/][/][/]."),
        "kind": ("kind runs k8s clusters using Docker containers as nodes. "
                 "Designed for testing k8s itself. Learn more: [steel_blue]"
                 "[b][link=https://kind.sigs.k8s.io/]kind.sigs.k8s.io[/][/][/]")
        }


DEFAULT_OPTIONS = DEFAULT_DISTRO_OPTIONS.keys()


class DistroConfigScreen(Screen):
    """
    Textual app to configure smol-k8s-lab
    """
    CSS_PATH = ["./css/distro_config.tcss",
                "./css/node_inputs_widget.tcss",
                "./css/k3s.tcss",
                "./css/kind.tcss"]

    BINDINGS = [Binding(key="b,q,escape",
                        key_display="b",
                        action="app.pop_screen",
                        description="Back"),
                Binding(key="n",
                        key_display="n",
                        action="app.request_apps_cfg",
                        description="Next"),
                Binding(key="a",
                        key_display="a",
                        action="screen.launch_new_option_modal",
                        description="add new option")]

    def __init__(self, config: dict) -> None:
        """
        config dict struct:
            {"distro":
               {"enabled": bool},
               {"k3s_yaml": dict},
               {"kubelet_extra_args": dict}
            }
        """
        self.cfg = config
        self.current_distro = process_k8s_distros(self.cfg, False)[1]
        self.show_footer = self.app.cfg['smol_k8s_lab']['tui']['show_footer']
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

        # create all distro selection choices for the top of tabbed content
        my_options = tuple(DEFAULT_OPTIONS)

        with Grid(id="distro-config-screen"):

            # tippy top row with the selection drop down
            with Grid(id="top-distro-row"):
                # container for top drop down and label
                with Grid(id="distro-select-box"):
                    yield Select(((line, line) for line in my_options),
                                 id="distro-drop-down",
                                 allow_blank=False,
                                 value=self.current_distro)
                    yield Label(DISTRO_DESC[self.current_distro],
                                id="distro-description")


    def on_mount(self) -> None:
        """
        screen and box border styling
        """
        self.title = "ʕ ᵔᴥᵔʔ smol k8s lab"
        sub_title = "Kubernetes distro config"
        self.sub_title = sub_title

        top_row = self.get_widget_by_id("top-distro-row")
        top_row.border_title = "🌱 Select a [#C1FF87]k8s distro[/]"
        top_row.border_subtitle = "[i]Inputs below are optional"

        main_box = self.get_widget_by_id("distro-config-screen")

        if self.app.speak_screen_titles:
            # if text to speech is on, read screen title
            self.app.action_say("Screen title: " + sub_title)

        if self.current_distro == 'kind':
            main_box.mount(
                    KindConfigWidget(
                        self.cfg.get('kind', DEFAULT_DISTRO_OPTIONS['kind']),
                        id='kind-pseudo-screen'
                        )
                    )
        else:
            main_box.mount(
                    K3ConfigWidget(
                        self.current_distro,
                        DEFAULT_DISTRO_OPTIONS[self.current_distro],
                        id=self.current_distro + "-pseudo-screen"
                        )
                    )

    @on(Select.Changed)
    def update_k8s_distro(self, event: Select.Changed) -> None:
        distro = str(event.value)

        # disable display on previous distro
        old_distro_obj = self.get_widget_by_id(f"{self.current_distro}-pseudo-screen")
        old_distro_obj.display = False
        self.cfg[self.current_distro]['enabled'] = False

        # change display to True if the distro is selected
        try:
            distro_obj = self.get_widget_by_id(f"{distro}-pseudo-screen")
            distro_obj.display = True
        except NoMatches:
            if distro == 'kind':
                self.get_widget_by_id("distro-config-screen").mount(
                        KindConfigWidget(
                            self.cfg.get('kind', DEFAULT_DISTRO_OPTIONS['kind']),
                            id="kind-pseudo-screen"
                            )
                        )
            else:
                self.get_widget_by_id("distro-config-screen").mount(
                        K3ConfigWidget(
                            distro,
                            DEFAULT_DISTRO_OPTIONS[distro],
                            id=distro + "-pseudo-screen"
                            )
                        )

        self.cfg[distro]['enabled'] = True

        # update the tooltip to be the correct distro's description
        distro_description = DISTRO_DESC[distro]
        self.get_widget_by_id("distro-description").update(distro_description)

        self.app.cfg['k8s_distros'][distro]['enabled'] = True
        self.app.cfg['k8s_distros'][self.current_distro]['enabled'] = False
        self.app.write_yaml()

        self.current_distro = distro

    def action_launch_new_option_modal(self) -> None:
        def add_new_row(option: str):
            if option and self.current_distro != 'kind':
                k3s_widget = self.get_widget_by_id(f"{self.current_distro}-widget")
                k3s_widget.generate_row(option)
            elif option and self.current_distro == 'kind':
                if self.query_one(TabbedContent).active == "kind-networking-tab":
                    kind_widget = self.query_one(KindNetworkingConfig)
                    kind_widget.generate_row(option)
                else:
                    kind_widget = self.query_one(KubeletConfig)
                    kind_widget.generate_row(option)
            else:
                return

        if self.current_distro != 'kind':
            existing_keys = self.cfg[self.current_distro]['k3s_yaml'].keys()
            trigger = "k3s"
        else:
            kind_cfg = self.cfg['kind']
            if self.query_one(TabbedContent).active == "kind-networking-tab":
                existing_keys = kind_cfg['networking_args'].keys()
                trigger = "kind networking"
            else:
                existing_keys = kind_cfg['kubelet_extra_args'].keys()
                trigger = "kind kubelet"

        self.app.push_screen(NewOptionModal(trigger, existing_keys), add_new_row)


class KindConfigWidget(Static):
    """ 
    a widget representing the entire kind configuration
    """
    def __init__(self,
                 metadata: dict = DEFAULT_DISTRO_OPTIONS['kind'],
                 id="kind-pseudo-screen") -> None:
        self.metadata = metadata
        super().__init__(id=id)

    def compose(self) -> ComposeResult:
        with Grid(classes="k8s-distro-config", id="kind-box"):
            # take number of nodes from config and make string
            nodes = self.metadata.get('nodes', {'control_plane': 1,
                                                'workers': 0})
            control_nodes = str(nodes.get('control_plane', '1'))
            worker_nodes = str(nodes.get('workers', '0'))

            # node input row
            yield NodeAdjustmentBox('kind', control_nodes, worker_nodes)

            kubelet_args = self.metadata['kubelet_extra_args']
            networking_args = self.metadata['networking_args']

            # Add the TabbedContent widget for kind config
            with TabbedContent(initial="kind-networking-tab",
                               id="kind-tabbed-content"):
                # tab 1 - networking options
                with TabPane("Networking options",
                             id="kind-networking-tab"):
                    # kind networking section
                    yield KindNetworkingConfig(networking_args)

                # tab 2 - kubelet options
                with TabPane("Kubelet Config Options", 
                             id="kind-kubelet-tab"):
                    # kubelet config section for kind only
                    yield KubeletConfig('kind', kubelet_args)

    def on_mount(self) -> None:
        """
        screen and box border styling
        """
        # update tabbed content box
        tabbed_content = self.query_one(TabbedContent)

        tabbed_content.border_title = ("Add [i]extra[/] options for "
                                       "[#C1FF87]kind[/] config files")

        subtitle = ("[b][@click=screen.launch_new_option_modal()]"
                    "➕ kind option[/][/]")
        tabbed_content.border_subtitle = subtitle

        for tab in self.query("Tab"):
            tab.add_class('header-tab')

    def action_show_tab(self, tab: str) -> None:
        """Switch to a new tab."""
        self.get_child_by_type(TabbedContent).active = tab

    @on(TabbedContent.TabActivated)
    def speak_when_tab_selected(self, event: TabbedContent.TabActivated) -> None:
        if self.app.speak_on_focus:
            self.app.action_say(f"Selected tab is {event.tab.id}")


class K3ConfigWidget(Static):
    """ 
    a widget representing the entire kind configuration
    """
    def __init__(self, distro: str, metadata: dict, id: str = "") -> None:
        self.metadata = metadata
        self.distro = distro
        super().__init__(id=id)

    def compose(self) -> ComposeResult:
        if not self.metadata:
            self.metadata = DEFAULT_DISTRO_OPTIONS[self.distro]

        with Grid(classes="k8s-distro-config", id=f"{self.distro}-box"):

            # take number of nodes from config and make string
            nodes = self.metadata.get('nodes', {'control_plane': 1,
                                                'workers': 0})
            control_nodes = str(nodes.get('control_plane', '1'))
            worker_nodes = str(nodes.get('workers', '0'))

            # node input row
            yield NodeAdjustmentBox(self.distro, control_nodes, worker_nodes)

            # take extra k3s args if self.distro is k3s or k3d
            yield K3sConfig(self.distro, self.metadata['k3s_yaml'],
                            id=f"{self.distro}-widget")
