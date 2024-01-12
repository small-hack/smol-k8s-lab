#!/usr/bin/env python3.11
# smol-k8s-lab libraries
from smol_k8s_lab.constants import DEFAULT_DISTRO_OPTIONS
from smol_k8s_lab.env_config import process_k8s_distros
from smol_k8s_lab.tui.distro_widgets.k3s_config import K3sConfigWidget
from smol_k8s_lab.tui.distro_widgets.kind_config import (KindNetworkingConfig,
                                                         KindConfigWidget)
from smol_k8s_lab.tui.util import NewOptionModal

# external libraries
from textual import on
from textual.app import ComposeResult, NoMatches
from textual.binding import Binding
from textual.containers import Grid
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, Select


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
                    K3sConfigWidget(
                        self.current_distro,
                        self.cfg.get('k3s', DEFAULT_DISTRO_OPTIONS['k3s']),
                        id=self.current_distro + "-pseudo-screen"
                        )
                    )

    @on(Select.Changed)
    def update_k8s_distro(self, event: Select.Changed) -> None:
        """
        changed currently enabled kubernetes distro in the TUI
        """
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
                        K3sConfigWidget(
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
        """
        callable action via link and key binding to display a modal for adding
        a new option to the currently selected tab of the distro's config screen
        """
        def add_new_row(option: str):
            """
            DistroConfigScreen.action_launch_new_option_modal.add_new_row
            called when user's input for a new option validates and is submitted

            Takes option (str) to add new row to the tui for the active tab of
            current distro
            """
            distro = self.current_distro

            if option:
                # if the distro is kind
                if distro == 'kind':
                    # use tab for kind networking, which is the default tab
                    tabbed_content = self.get_widget_by_id("kind-tabbed-content")
                    if tabbed_content.active == "kind-networking-tab":
                        widget = self.query_one(KindNetworkingConfig)

                # if the distro is k3s OR k3d
                elif distro.startswith('k3'):
                    tabbed_content = self.get_widget_by_id("k3s-tabbed-content")
                    # use tab for k3s yaml options, EXCEPT for kubelet config args
                    if tabbed_content.active == "k3s-yaml-tab":
                        if option == "kubelet-arg":
                            self.query_one(K3sConfigWidget).action_show_tab("k3s-kubelet-tab")
                            return
                        else:
                            widget = self.get_widget_by_id(f"{distro}-widget")

                if "kubelet" in tabbed_content.active:
                    widget = self.get_widget_by_id(f"kubelet-config-{distro}")

                widget.generate_row(option)

            else:
                return

        if self.current_distro == 'kind':
            kind_cfg = self.cfg['kind']
            kind_tabbed_content = self.get_widget_by_id("kind-tabbed-content")
            if kind_tabbed_content.active == "kind-networking-tab":
                existing_keys = kind_cfg['networking_args'].keys()
                trigger = "kind networking"
            else:
                existing_keys = kind_cfg['kubelet_extra_args'].keys()
                trigger = "kind kubelet"

        # if the current_distro is k3s or k3d
        else:
            k3s_tabbed_content = self.get_widget_by_id("k3s-tabbed-content")
            if k3s_tabbed_content.active == "k3s-kubelet-tab":
                existing_keys = self.cfg[self.current_distro]['k3s_yaml'].get(
                        "kubelet-arg", []
                        )
                trigger = "k3s kubelet"
            else:
                existing_keys = self.cfg[self.current_distro]['k3s_yaml'].keys()
                trigger = "k3s k3s_yaml"

        self.app.push_screen(NewOptionModal(trigger, existing_keys), add_new_row)
