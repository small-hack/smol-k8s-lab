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
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, Select, TabbedContent, TabPane


# the description of the k8s distro
DISTRO_DESC = {
        "k3s": ("K3s, by Rancher Labs, is a minimal Kubernetes distro that fits in "
                "about 70MB. (it's also optomized for ARM) Learn more: "
                "[steel_blue][u][link=https://k3s.io]k3s.io[/][/]."),
        "k3d": ("k3d is a lightweight wrapper to run k3s (Rancher Lab’s minimal "
                "Kubernetes distribution) in Docker containers. Learn more: "
                "[steel_blue][u][link=https://k3d.io]k3d.io[/][/][/]."),
        "kind": ("kind runs k8s clusters using Docker containers as nodes. "
                 "Designed for testing k8s itself. Learn more: [steel_blue]"
                 "[u][link=https://kind.sigs.k8s.io/]kind.sigs.k8s.io[/][/][/]")
        }


DEFAULT_OPTIONS = DEFAULT_DISTRO_OPTIONS.keys()


class DistroConfigScreen(Screen):
    """
    Textual app to configure smol-k8s-lab
    """
    CSS_PATH = ["./css/distro_config.tcss",
                "./css/node_inputs_widget.tcss",
                "./css/k3s.tcss",
                "./css/kubelet.tcss",
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
        self.previous_distro = process_k8s_distros(self.cfg, False)[1]
        self.show_footer = self.app.cfg['smol_k8s_lab']['interactive']['show_footer']

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
                                 value=self.previous_distro)
                    yield Label(DISTRO_DESC[self.previous_distro],
                                id="distro-description")

            for distro in DEFAULT_OPTIONS:
                distro_metadata = self.cfg.get(distro, None)
                if not distro_metadata:
                    distro_metadata = DEFAULT_DISTRO_OPTIONS[distro]

                # only display the default distro for this OS
                if distro == self.previous_distro:
                    display = True
                else:
                    display = False

                grid_class = f"{distro} k8s-distro-config"

                distro_box = Grid(classes=grid_class, id=f"{distro}-box")
                distro_box.display = display

                with distro_box:
                    # take number of nodes from config and make string
                    nodes = distro_metadata.get('nodes', False)
                    control_nodes = str(nodes.get('control_plane', '1'))
                    worker_nodes = str(nodes.get('workers', '0'))

                    # node input row
                    yield NodeAdjustmentBox(distro, control_nodes, worker_nodes)

                    if distro == 'kind':
                        kubelet_args = distro_metadata['kubelet_extra_args']
                        networking_args = distro_metadata['networking_args']

                        # Add the TabbedContent widget for kind config
                        with TabbedContent(initial="kind-networking-tab"):
                            # tab 1 - networking options
                            with TabPane("Networking options",
                                         id="kind-networking-tab"):
                                # kind networking section
                                yield KindNetworkingConfig(networking_args)

                            # tab 2 - kubelet options
                            with TabPane("Kubelet Config Options",
                                         id="kind-kubelet-tab"):
                                # kubelet config section for kind only
                                yield KubeletConfig(distro, kubelet_args)
                                                    

                    # take extra k3s args if distro is k3s or k3d
                    else:
                        yield K3sConfig(distro, distro_metadata['k3s_yaml'],
                                        id=f"{distro}-widget")

    def on_mount(self) -> None:
        """
        screen and box border styling
        """
        self.title = "ʕ ᵔᴥᵔʔ smol k8s lab"
        self.sub_title = "k8s distro config"

        top_row = self.get_widget_by_id("top-distro-row")
        top_row.border_title = "🌱 Select a [#C1FF87]k8s distro[/]"
        top_row.border_subtitle = "[i]Inputs below are optional"

        # update tabbed content box
        tabbed_content = self.query_one(TabbedContent)

        tabbed_content.border_title = ("Add [i]extra[/] options for "
                                       "[#C1FF87]kind[/] config files")

        subtitle = ("[@click=screen.launch_new_option_modal()]"
                    "➕ kind option[/]")
        tabbed_content.border_subtitle = subtitle

        self.query_one("Tab#kind-networking-tab").add_class('kind-networking-tab')
        self.query_one("Tab#kind-kubelet-tab").add_class('kind-kubelet-tab')

    def action_show_tab(self, tab: str) -> None:
        """Switch to a new tab."""
        self.get_child_by_type(TabbedContent).active = tab

    @on(Select.Changed)
    def update_k8s_distro(self, event: Select.Changed) -> None:
        distro = str(event.value)

        # disable display on previous distro
        if self.previous_distro:
            distro_obj = self.get_widget_by_id(f"{self.previous_distro}-box")
            distro_obj.display = False
            self.cfg[self.previous_distro]['enabled'] = False

        # change display to True if the distro is selected
        distro_obj = self.get_widget_by_id(f"{distro}-box")
        distro_obj.display = True
        self.cfg[distro]['enabled'] = True

        # update the tooltip to be the correct distro's description
        distro_description = DISTRO_DESC[distro]
        self.get_widget_by_id("distro-description").update(distro_description)

        self.app.cfg['k8s_distros'][distro]['enabled'] = True
        self.app.cfg['k8s_distros'][self.previous_distro]['enabled'] = False
        self.app.write_yaml()

        self.previous_distro = distro

    def action_launch_new_option_modal(self) -> None:
        def add_new_row(option: str):
            if option and self.previous_distro != 'kind':
                k3s_widget = self.get_widget_by_id(f"{self.previous_distro}-widget")
                k3s_widget.generate_row(option)
            elif option and self.previous_distro == 'kind':
                if self.query_one(TabbedContent).active == "kind-networking-tab":
                    kind_widget = self.query_one(KindNetworkingConfig)
                    kind_widget.generate_row(option)
                else:
                    kind_widget = self.query_one(KubeletConfig)
                    kind_widget.generate_row(option)
            else:
                return

        if self.previous_distro != 'kind':
            existing_keys = self.cfg[self.previous_distro]['k3s_yaml'].keys()
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


def format_description(description: str = ""):
    """
    change description to dimmed colors
    links are changed to steel_blue and not dimmed
    """
    description = description.replace("[link", "[/dim][steel_blue][link")
    description = description.replace("[/link]", "[/link][/steel_blue][dim]")

    return f"""[dim]{description}[/dim]"""
