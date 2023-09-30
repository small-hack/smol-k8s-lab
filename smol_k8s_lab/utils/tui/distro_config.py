#!/usr/bin/env python3.11
from smol_k8s_lab.constants import DEFAULT_DISTRO_OPTIONS
from smol_k8s_lab.env_config import process_k8s_distros
from smol_k8s_lab.utils.tui.distro_widgets.k3s_config import K3sConfig
from smol_k8s_lab.utils.tui.distro_widgets.kind_networking import KindNetworkingConfig
from smol_k8s_lab.utils.tui.distro_widgets.kubelet_config import KubeletConfig
from smol_k8s_lab.utils.tui.distro_widgets.node_adjustment import NodeAdjustmentBox
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, Select


DEFAULT_OPTIONS = DEFAULT_DISTRO_OPTIONS.keys()


class DistroConfigScreen(Screen):
    """
    Textual app to configure smol-k8s-lab
    """
    CSS_PATH = ["./css/distro_config.tcss",
                "./css/k3s.tcss",
                "./css/kubelet.tcss",
                "./css/kind.tcss"]

    BINDINGS = [Binding(key="escape,q",
                        key_display="esc,q",
                        action="app.pop_screen",
                        description="↩ Back")]

    def __init__(self, config: dict) -> None:
        """
        config dict struct:
            {"distro":
               {"enabled": bool},
               {"k3s_extra_args": []},
               {"kubelet_extra_args": {}},
               {"description": ""}
            }
        """
        self.cfg = config
        self.previous_distro = process_k8s_distros(self.cfg, False)[1]
        self.show_footer = self.cfg['smol_k8s_lab']['interactive']['show_footer']

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

        # this is for selecting distros
        label = Label("🌱 Select a distro to get started:",
                      id="select-distro-label")
        label.tooltip = self.cfg[self.previous_distro]['description']

        # create all distro selection choices for the top of tabbed content
        my_options = tuple(DEFAULT_OPTIONS)

        # container for top drop down
        with Horizontal(id="distro-select-box"):
            yield label
            yield Select(((line, line) for line in my_options),
                         id="distro-drop-down",
                         allow_blank=False,
                         value=self.previous_distro)

        # below is advanced configuration
        advanced_label = Label(
                "⚙️ [i]Advanced Configuration - [dim]Press [gold3]↩ Enter[/]"
                " to save [i]each[/i] input field.",
                id="advanced-config-label")
        yield advanced_label

        with Container(id="distro-config-screen"):

            for distro in DEFAULT_OPTIONS:
                distro_metadata = self.cfg.get(distro, None)
                if not distro_metadata:
                    distro_metadata = DEFAULT_DISTRO_OPTIONS[distro]

                # only display the default distro for this OS
                if distro == self.previous_distro:
                    display = True
                else:
                    display = False

                distro_box = Container(classes=f"k8s-distro-config {distro}",
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

                    # take extra k3s args if distro is k3s or k3d
                    if distro == 'k3s' or distro == 'k3d':
                        k3s_args = distro_metadata['extra_k3s_cli_args']

                        k3s_box_classes = f"{distro} k3s-config-container"

                        yield Container(K3sConfig(distro, k3s_args),
                                        classes=k3s_box_classes)
                    elif distro == 'kind':
                        yield Container(
                                KindNetworkingConfig(distro_metadata['networking_args']),
                                id="kind-networking-container"
                                )

    def on_mount(self) -> None:
        """
        screen and box border styling
        """
        self.title = "ʕ ᵔᴥᵔʔ smol k8s lab"
        self.sub_title = "k8s distro config"

        # kubelet config styling - middle
        kubelet_title = "➕ [green]Extra Parameters for Kubelet"
        kubelet_cfgs = self.query(".kubelet-config-container")
        for box in kubelet_cfgs:
            box.border_title = kubelet_title

        # k3s arg config sytling - middle
        k3s_title = "➕ [green]Extra Args for k3s install script"
        self.query_one(".k3s-config-container").border_title = k3s_title

        # kind networking arg config sytling - bottom
        kind_title = "➕ [green]Extra Args for kind networking config"
        self.get_widget_by_id("kind-networking-container").border_title = kind_title

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
        distro_description = self.cfg[distro]["description"]
        self.get_widget_by_id("select-distro-label").tooltip = distro_description

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
