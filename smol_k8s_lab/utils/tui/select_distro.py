#!/usr/bin/env python3.11
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.binding import Binding
from textual.widgets import RadioButton, RadioSet, Button, Footer, Header
from smol_k8s_lab.constants import DEFAULT_DISTROS, DEFAULT_DISTRO


class SelectK8sDistro(App[None]):
    """
    Class to assist with selecting a k8s distro
    """
    CSS_PATH = "./css/select_distro.tcss"
    BINDINGS = [
        Binding(key="uparrow",
                key_display="↑",
                action="up",
                description="Scroll up"),
        Binding(key="downarrow",
                key_display="↓",
                action="down",
                description="Scroll down"),
        Binding(key="spacebar",
                key_display="space/enter",
                action="select",
                description="Select"),
        Binding(key="tab",
                action="focus_next",
                description="Focus next",
                show=True),
        Binding(key="q",
                key_display="q",
                action="quit",
                description="Quit smol-k8s-lab")
    ]

    def compose(self) -> ComposeResult:
        """
        draws out the smol-k8s-lab tui for Selecting a Distro
        """
        header = Header()
        header.tall = True
        yield header

        with RadioSet():
            # if k3s is allowed on this OS, set it by default
            if 'k3s' in DEFAULT_DISTROS:
                default_selected = 'k3s'
            # else, set the default selected to kind
            else:
                default_selected = 'kind'

            # create all the radio button choices
            for distro in DEFAULT_DISTROS:
                enabled = False

                if distro == default_selected:
                    enabled = True

                # note that k3s is in alpha testing
                elif distro == 'k3d':
                    distro += ' [magenta](alpha)[/]'

                radio_button = RadioButton(distro, value=enabled)
                # make the radio button cute
                radio_button.BUTTON_INNER = '❤'

                yield radio_button

        yield Button("Next", id="next")
        yield Footer()

    def on_mount(self) -> None:
        """
        Sets the focus to the radio set
        """
        self.screen.styles.border = ("heavy", "cornflowerblue")
        self.title = "🧸smol k8s lab"
        self.sub_title = "now with more 🦑"
        self.distro = DEFAULT_DISTRO
        self.query_one(RadioSet).focus()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """
        keep track of which radio button is being pressed
        """
        self.distro = DEFAULT_DISTROS[event.radio_set.pressed_index]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        when the next button is pressed
        """
        self.exit(self.distro)


if __name__ == "__main__":
    distro = SelectK8sDistro().run()
    print(distro)
