#!/usr/bin/env python3.11
# internal library
from smol_k8s_lab.constants import XDG_CACHE_DIR
from smol_k8s_lab.tui.util import create_sanitized_list
from smol_k8s_lab.tui.validators.already_exists import CheckIfNameAlreadyInUse

# external libraries
from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Grid
from textual.screen import ModalScreen
from textual.suggester import SuggestFromList
from textual.validation import Length
from textual.widgets import Input, Button, Label, Static

CFG_FILE = XDG_CACHE_DIR + "/k3s.yaml"

KEY_SUGGESTIONS = SuggestFromList((
       "disable",
       "disable-network-policy",
       "flannel-backend",
       "secrets-encryption",
       "node-label",
       "kubelet-arg",
       "datastore-endpoint",
       "etcd-s3",
       "server",
       "debug",
       "cluster-domain"
       "token",
       "agent-token",
       "bind-address",
       "cluster-dns",
       "https-listen-port",
       "kube-proxy-arg",
       "log",
       "rootless"
       ))

SUGGESTIONS = SuggestFromList((
       "traefik",
       "servicelb",
       "none",
       "wireguard-native",
       "true",
       "max_pods=",
       "podsPerCore=",
       "featureGates=",
       ))

LIST_KEYS = ["disable", "node-label", "kubelet-arg"]


class K3sConfig(Static):
    """
    k3s args config
    """

    def __init__(self, distro: str, k3s_args: list = [], id: str = "") -> None:
        self.k3s_args = k3s_args
        self.distro = distro
        super().__init__(id=id)

    def compose(self) -> ComposeResult:
        # main grid for the whole widget
        with Grid(classes=f"{self.distro} k3s-config-container",
                  id=f"{self.distro}-base-grid"):
            yield Label(
                    "Add extra [steel_blue][b][link=https://docs.k3s.io/cli/server]"
                    "k3s options[/][/][/] to pass to the k3s install script via a "
                    "[steel_blue][b][link=https://docs.k3s.io/installation/configuration#"
                    f"configuration-file]config file[/][/][/] stored in {CFG_FILE}",
                    classes="help-text"
                    )

            # actual input grid
            with VerticalScroll(classes=f"{self.distro} k3s-arg-scroll"):
                yield Grid(id="k3s-grid")

    def on_mount(self) -> None:
        """
        box border styling
        """
        # k3s arg config styling
        k3s_title = ("[i]Add[/] [i]extra[/] options for the [#C1FF87]k3s[/] "
                     "install script")
        k3s_container = self.get_widget_by_id(f"{self.distro}-base-grid")
        k3s_container.border_title = k3s_title
        subtitle = ("[b][@click=screen.launch_new_option_modal()]"
                    "➕ k3s option[/][/]")
        k3s_container.border_subtitle = subtitle

        # if we've been passed k3s args already, generate rows
        if self.k3s_args:
            for arg, value in self.k3s_args.items():
                if arg:
                    self.generate_row(arg, value)

        # don't remember why we needed this, but testing breaks with these errors if it's on:
        # RuntimeWarning: Enable tracemalloc to get the object allocation traceback
        # RuntimeWarning: coroutine 'App.action_focus' was never awaited
        # self.app.action_focus(self.query_one(".k3s-config-container"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        get pressed button and act on it
        """
        # lets you delete a k3s-arg row
        input = event.button.parent.children[1]

        # if the input field is not blank
        if input.value:
            cli_args = self.app.cfg['k8s_distros'][self.distro]["k3s_yaml"]
            if cli_args[input.name]:
                cli_args.pop(input.name)
                self.app.write_yaml()

        # delete the whole row
        event.button.parent.remove()

    @on(Input.Changed)
    def update_base_yaml(self, event: Input.Changed) -> None:
        if event.validation_result.is_valid:
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
            elif ',' in input_value or input_name in LIST_KEYS:
                yaml[input_name] = create_sanitized_list(input_value)

            # else it's a normal string and should be saved like one
            else:
                yaml[input_name] = input_value

            self.app.write_yaml()

    def generate_row(self, key: str, value: str = "") -> Grid:
        """
        create a new input row
        """
        # this is the label 
        key_label = key.replace("-", " ").replace("_", " ") + ":"
        label = Label(key_label, classes="input-label")

        # input values
        row_args = {"placeholder": f"Enter a {key} and press Enter",
                    "classes": f"{self.distro} k3s-arg-input",
                    "suggester": SUGGESTIONS,
                    "name": key,
                    "id": f"{self.distro}-{key}-input",
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
        tooltip = (f"If you want to input more than one {key} option, try using "
                   "a comma seperated list.")

        # we give a bit more info on disabling
        if key == "disable":
            tooltip += (" If [dim][#C1FF87]metallb[/][/] is [i]enabled[/], we add"
                        " servicelb to disabled.")

        input.tooltip = tooltip

        # button to delete the field entirely
        button = Button("🚮",
                        id=f"{self.distro}-{key}-delete-button",
                        classes="k3s-arg-del-button")
        button.tooltip = "Delete the arg to the left of this button"
        
        grid = Grid(label, input, button, classes="label-input-delete-row")
        self.get_widget_by_id("k3s-grid").mount(grid)


class NewK3sOptionModal(ModalScreen):

    CSS_PATH = ["../css/k3s_modal.css"]

    def __init__(self, k3s_args: list = []) -> None:
        self.k3s_args = k3s_args
        super().__init__()

    def compose(self) -> ComposeResult:
        # base screen grid
        question = "[#ffaff9]Add[/] [i]new[/] [#C1FF87]k3s option[/]."
        tooltip = (
                "Start typing an option to show suggestions. Use the right arrow "
                "key to complete the suggestion. Hit enter to submit. Note: If "
                "[dim][#C1FF87]cilium[/][/] is [i]enabled[/], we add flannel-backend: "
                "none and disable-network-policy: true."
                )

        with Grid(id="question-modal-screen"):
            # grid for app question and buttons
            with Grid(id="question-box"):
                yield Label(question, id="modal-text")

                with Grid(id='new-k3s-option-grid'):
                    input = Input(id='new-k3s-option',
                                  placeholder="new k3s option",
                                  suggester=KEY_SUGGESTIONS,
                                  validators=[
                                      Length(minimum=4),
                                      CheckIfNameAlreadyInUse(self.k3s_args.keys())
                                      ]
                                  )
                    input.tooltip = tooltip
                    yield input

                    button = Button("➕ add option", id="add-button")
                    button.disabled = True
                    yield button

    def on_mount(self) -> None:
        box = self.get_widget_by_id("question-box")
        box.border_subtitle = "[@click=app.pop_screen]cancel[/]"

    @on(Input.Changed)
    @on(Input.Submitted)
    def disable_button_or_not(self, event: Input.Changed | Input.Submitted) -> None:
        add_button = self.get_widget_by_id("add-button")

        # disable the button if the input is invalid
        if event.validation_result.is_valid:
            add_button.disabled = False
        else:
            if "already in use" in event.validation_result.failure_descriptions[0]:
                res = ("That option is already defined! If you want to add additional"
                       f"options to {event.input.value}, you can use a comma "
                       "seperated list.")
                self.app.bell()
                self.app.notify(res,
                                title="Input Validation Error", severity="error",
                                timeout=9)
            add_button.disabled = True

        # if button is currently enabled and the user presses enter, press button
        if isinstance(event, Input.Submitted):
            if not add_button.disabled:
                add_button.action_press()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        get pressed button and act on it
        """
        input = self.get_widget_by_id("new-k3s-option")
        self.dismiss(input.value)
