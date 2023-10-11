#!/usr/bin/env python3.11
# internal library
from smol_k8s_lab.tui.util import create_sanitized_list

# external libraries
from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Grid
from textual.suggester import SuggestFromList
from textual.validation import Length
from textual.widgets import Input, Button, Label, Static

KEY_SUGGESTIONS = SuggestFromList((
       "disable",
       "disable-network-policy",
       "flannel-backend",
       "secrets-encryption",
       "node-label"
       ))

SUGGESTIONS = SuggestFromList((
       "traefik",
       "servicelb",
       "none",
       "wireguard-native",
       "true",
       ))

help_txt = (
        "If [dim][#C1FF87]metallb[/][/] is [i]enabled[/], we add servicelb to disabled."
        " If [dim][#C1FF87]cilium[/][/] is [i]enabled[/], we add "
        "flannel-backend: none and disable-network-policy: true."
        )


class K3sConfig(Static):
    """
    k3s args config
    """

    def __init__(self, distro: str, k3s_args: list = []) -> None:
        self.k3s_args = k3s_args
        self.distro = distro
        super().__init__()

    def compose(self) -> ComposeResult:
        # main grid for the whole widget
        with Grid(classes=f"{self.distro} k3s-config-container"):

            # actual input grid
            with VerticalScroll(classes=f"{self.distro} k3s-arg-scroll"):
                yield Grid(id="k3s-grid")

            with Grid(id='new-k3s-option-grid'):
                input = Input(id='new-k3s-option',
                              placeholder="new k3s option",
                              suggester=KEY_SUGGESTIONS,
                              validators=[Length(minimum=4)])
                input.tooltip = help_txt
                yield input

                button = Button("➕ add option", id="add-button")
                button.disabled = True
                yield button

    def on_mount(self) -> None:
        """
        box border styling
        """
        # k3s arg config styling
        k3s_title = ("[i]Add[/] [i]extra[/] parameters for [#C1FF87]k3s[/] "
                     "install script")
        k3s_container = self.query_one(".k3s-config-container")
        k3s_container.border_title = k3s_title

        # if we've been passed k3s args already, generate rows
        if self.k3s_args:
            for arg, value in self.k3s_args.items():
                if arg:
                    self.action_generate_row(arg, value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        get pressed button and act on it
        """
        button_classes = event.button.classes

        # lets you delete a k3s-arg row
        if "k3s-arg-del-button" in button_classes:
            input = event.button.parent.children[1]

            # if the input field is not blank
            if input.value:
                cli_args = self.app.cfg['k8s_distros'][self.distro]["k3s_yaml"]
                if cli_args[input.name]:
                    cli_args.pop(input.name)

            # delete the whole row
            event.button.parent.remove()

    @on(Input.Changed)
    def update_base_yaml(self, event: Input.Changed) -> None:
        if event.validation_result.is_valid:
            if event.input.id != "new-k3s-option":
                # parent app's future yaml config
                yaml = self.app.cfg['k8s_distros'][self.distro]["k3s_yaml"]

                # input that triggered the event
                input_name = event.input.name
                input_value = event.input.value

                # if this is a boolean, we have to save it like one
                if input_value.lower() == 'true':
                    yaml[input_name] = True

                # if this is a boolean, we have to save it like one, part 2
                elif input_value.lower() == 'false':
                    yaml[input_name] = False

                # if there's a comma, it's a list
                elif ',' in input_value or input_name in ["disable", "node-label"]:
                    yaml[input_name] = create_sanitized_list(input_value)

                # else it's a normal string and should be saved like one
                else:
                    yaml[input_name] = input_value

                self.app.write_yaml()
            else:
                self.get_widget_by_id("add-button").disabled = False
        else:
            if event.input.id == "new-k3s-option":
                self.get_widget_by_id("add-button").disabled = True

    def action_generate_row(self, key: str, value: str = "") -> Grid:
        """
        create a new input row
        """
        # this is the label 
        key_label = key.replace("-", " ").replace("_", " ") + ":"
        label = Label(key_label, classes="input-label")

        # input values
        row_args = {"placeholder": f"Please enter a value for {key} and press Enter",
                    "classes": f"{self.distro} k3s-arg-input",
                    "suggester": SUGGESTIONS,
                    "name": key,
                    "validators": Length(minimum=4)}
        if value:
            # if this is a bool, turn it into a string for our current purposes
            if isinstance(value, bool):
                if value:
                    row_args['value'] = 'true'
                elif not value:
                    row_args['value'] = 'false'

            # if this is a list, make a comma seperated list
            if isinstance(value, list):
                row_args['value'] = ", ".join(value)

            # else if this is a string, we just set it to that value outright
            if isinstance(value, str):
                row_args['value'] = value

        # actual input field 
        input = Input(**row_args)
        input.tooltip = (f"If you want to input more than one {key} option, try"
                         " using a comma seperated list")

        # button to delete the field entirely
        button = Button("🚮", classes="k3s-arg-del-button")
        button.tooltip = "Delete the arg to the left of this button"
        
        grid = Grid(label, input, button, classes="k3s-arg-row")
        self.get_widget_by_id("k3s-grid").mount(grid)
