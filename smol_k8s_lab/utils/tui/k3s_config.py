#!/usr/bin/env python3.11
from textual import on
from textual.app import ComposeResult, Widget
from textual.containers import Container, VerticalScroll, Grid
from textual.widgets import Input, Button, Label
from textual.suggester import SuggestFromList

SUGGESTIONS = SuggestFromList((
       "--disable=traefik",
       "--disable=servicelb"
       "--secrets-encryption",
       "--flannel-backend=wireguard-native",
       ))


class K3sConfig(Widget):
    """
    k3s args config
    """

    def __init__(self, distro: str, k3s_args: list = []) -> None:
        self.k3s_args = k3s_args
        self.distro = distro
        if self.distro == 'k3s':
            self.yaml_key = 'extra_cli_args'
        else:
            self.yaml_key = 'extra_k3s_cli_args'
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Label("After adding a new argument, hit enter to save it",
                    classes="k3s-help-label")
        with VerticalScroll(classes=f"{self.distro} k3s-arg-scroll"):
            with Grid(classes="k3s-grid"):
                if self.k3s_args:
                    for arg in self.k3s_args:
                        yield self.generate_half_row(arg)
                    # just to make the row even if there's only one arg
                    if len(self.k3s_args) < 2:
                        yield self.generate_half_row()

            yield Button("➕ [blue]New Argument[/blue]",
                         classes=f"{self.distro} k3s-arg-add-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        get pressed button and act on it
        """
        button_classes = event.button.classes

        # lets you delete a k3s-arg row
        if "k3s-arg-del-button" in button_classes:
            parent_row = event.button.parent
            input_key = parent_row.children[0].value

            # if the input field is not blank
            if input_key:
                yaml = event.button.ancestors[-1].usr_cfg['k8s_distros']
                cli_args = yaml[self.distro][self.yaml_key]
                if cli_args:
                    for idx, arg in enumerate(cli_args):
                        if arg == input_key:
                            pop_me = idx
                    cli_args.pop(pop_me)

            # delete the whole row
            parent_row.remove()

        # lets you add a new k3s config row
        if "k3s-arg-add-button" in button_classes:
            input_container = self.query_one(".k3s-grid")
            input_container.mount(self.generate_half_row())

    @on(Input.Submitted)
    def update_base_yaml(self, event: Input.Changed) -> None:
        input = event.input
        yaml = input.ancestors[-1].usr_cfg['k8s_distros'][self.distro][self.yaml_key]
        if input.value not in yaml:
            yaml.append(input.value)

    def generate_half_row(self, value: str = "") -> Container:
        """
        create a new input row
        """
        row_args = {"placeholder": "enter an arg for k3s & press Enter",
                    "classes": f"{self.distro} k3s-arg-input",
                    "suggester": SUGGESTIONS}
        if value:
            row_args["value"] = value
        button = Button("🚮", classes="k3s-arg-del-button")
        button.tooltip = "Delete the arg to the left of this button"
        return Container(Input(**row_args), button, classes="k3s-arg-row")
