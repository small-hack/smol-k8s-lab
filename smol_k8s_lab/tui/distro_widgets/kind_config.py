#!/usr/bin/env python3.11
# smol-k8s-lab libraries
from smol_k8s_lab.constants import DEFAULT_DISTRO_OPTIONS
from smol_k8s_lab.tui.distro_widgets.kubelet_config import KubeletConfig
from smol_k8s_lab.tui.distro_widgets.node_adjustment import NodeAdjustmentBox

# external libraries
from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Grid
from textual.suggester import SuggestFromList
from textual.validation import Length
from textual.widget import Widget
from textual.widgets import Input, Button, Label, TabbedContent, TabPane, Static


VALUE_SUGGESTIONS = SuggestFromList(("true", "ipv4", "ipv6"))
HELP_TEXT = (
        "Add key value pairs to [steel_blue][link="
        "https://kind.sigs.k8s.io/docs/user/configuration/#networking]"
        "kind networking config[/][/]."
        )


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
            nodes = self.metadata.get('nodes',
                                      {'control_plane': 1, 'workers': 0}
                                      )
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

        tabbed_content.border_title = (
                "Add [i]extra[/] options for [#C1FF87]kind[/] config files"
                )

        subtitle = (
                "[b][@click=screen.launch_new_option_modal()] ➕ kind option[/][/]"
                )

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


class KindNetworkingConfig(Widget):
    """
    Container for extra args for kind networking configuration
    """

    def __init__(self, kind_neworking_params: list = []) -> None:
        self.kind_neworking_params = kind_neworking_params
        super().__init__()

    def compose(self) -> ComposeResult:
        with Grid(id="kind-networking-container"):
            yield Label(HELP_TEXT, classes="help-text")
            yield VerticalScroll(id="kind-networking-config-scroll")

    def on_mount(self) -> None:
        if self.kind_neworking_params:
            for key, value in self.kind_neworking_params.items():
                self.generate_row(key, str(value))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        get pressed button add or delete button and act on it
        """
        parent_row = event.button.parent
        input_key = parent_row.children[1].name
        parent_yaml = self.app.cfg['k8s_distros']['kind']['networking_args']
        if input_key and parent_yaml.get(input_key, False):
            parent_yaml.pop(input_key)
            self.app.write_yaml()
        parent_row.remove()

    @on(Input.Submitted)
    @on(Input.Changed)
    def update_base_yaml(self, event: Input.Changed | Input.Submitted) -> None:
        if event.validation_result.is_valid:
            # grab the user's yaml file from the parent app
            extra_args = self.app.cfg['k8s_distros']['kind']['networking_args']

            # if they answer with a boolean, make sure it's written out correctly
            if event.input.value.lower() == 'true':
                extra_args[event.input.name] = True
            elif event.input.value.lower() == 'false':
                extra_args[event.input.name] = False
            else:
                extra_args[event.input.name] = event.input.value

            self.app.write_yaml()

    def generate_row(self, param: str = "", value: str = "") -> Grid:
        """
        generate a new input field set
        """
        # base class for all the below object
        row_class = "kind-networking-input"

        # label for input field
        label = Label(param.replace("_", " ") + ":", classes="input-label")

        # second input field
        param_value_input_args = {"classes": f"{row_class}-value",
                                  "placeholder": "kind networking param value",
                                  "suggester": VALUE_SUGGESTIONS,
                                  "validators": Length(minimum=1),
                                  "id": f"kind-networking-{param}-input",
                                  "name": param}
        if value:
            param_value_input_args["value"] = value
        param_value_input = Input(**param_value_input_args)

        # delete button for each row
        del_button = Button("🚮",
                            id=f"kind-networking-{param}-delete-button",
                            classes=f"{row_class}-del-button")
        del_button.tooltip = "Delete this kind networking parameter"

        self.get_widget_by_id("kind-networking-config-scroll").mount(
                Grid(label, param_value_input, del_button,
                     classes="label-input-delete-row")
                )
