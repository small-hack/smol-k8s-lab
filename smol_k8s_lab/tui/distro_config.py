#!/usr/bin/env python3.11
# smol-k8s-lab libraries
from smol_k8s_lab.constants import DEFAULT_DISTRO_OPTIONS
from smol_k8s_lab.env_config import process_k8s_distros
from smol_k8s_lab.tui.distro_widgets.k3s_config import K3sConfig
from smol_k8s_lab.tui.distro_widgets.kind_networking import KindNetworkingConfig
from smol_k8s_lab.tui.distro_widgets.kubelet_config import KubeletConfig
from smol_k8s_lab.tui.distro_widgets.node_adjustment import NodeAdjustmentBox

# external libraries
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, Select


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

    BINDINGS = [Binding(key="b,q,esc",
                        key_display="b",
                        action="app.pop_screen",
                        description="Back"),
                Binding(key="n",
                        key_display="n",
                        action="app.request_apps_cfg",
                        description="Next")]

    def __init__(self, config: dict) -> None:
        """
        config dict struct:
            {"distro":
               {"enabled": bool},
               {"k3s_extra_args": []},
               {"kubelet_extra_args": {}}
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

                distro_box = Grid(classes=f"k8s-distro-config {distro}",
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
                    yield NodeAdjustmentBox(distro, control_nodes, worker_nodes)

                    # kubelet config section
                    yield KubeletConfig(distro,
                                        distro_metadata['kubelet_extra_args'])

                    # take extra k3s args if distro is k3s or k3d
                    if distro == 'k3s' or distro == 'k3d':
                        yield K3sConfig(distro,
                                        distro_metadata['extra_k3s_cli_args'])

                    elif distro == 'kind':
                        yield KindNetworkingConfig(distro_metadata['networking_args'])

    def on_mount(self) -> None:
        """
        screen and box border styling
        """
        self.title = "ʕ ᵔᴥᵔʔ smol k8s lab"
        self.sub_title = "k8s distro config"

        top_row = self.get_widget_by_id("top-distro-row")
        top_row.border_title = "🌱 Select a [#C1FF87]k8s distro[/]"
        top_row.border_subtitle = "[i]All boxes below are optional"

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

        self.ancestors[-1].cfg['k8s_distros'][distro]['enabled'] = True
        self.ancestors[-1].cfg['k8s_distros'][self.previous_distro]['enabled'] = False
        self.ancestors[-1].write_yaml()

        self.previous_distro = distro


def format_description(description: str = ""):
    """
    change description to dimmed colors
    links are changed to steel_blue and not dimmed
    """
    description = description.replace("[link", "[/dim][steel_blue][link")
    description = description.replace("[/link]", "[/link][/steel_blue][dim]")

    return f"""[dim]{description}[/dim]"""
