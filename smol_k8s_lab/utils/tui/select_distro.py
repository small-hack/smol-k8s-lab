#!/usr/bin/env python3.11
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import RadioButton, RadioSet, Button, Footer


class SelectDistro(App[None]):
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
        with RadioSet():
            yield RadioButton("k3s", value=True)
            yield RadioButton("k3d [red](alpha)[/]")
            yield RadioButton("k0s")
            yield RadioButton("kind", id="focus_me")
        yield Button("Next", id="next")
        yield Footer()

    def on_mount(self) -> None:
        self.screen.styles.border = ("heavy", "cornflowerblue")
        self.title = "🧸smol k8s lab"
        self.sub_title = "now with more 🦑"
        self.query_one(RadioSet).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        all_selected = self.query_one(RadioSet).selected
        self.exit(all_selected)


if __name__ == "__main__":
    distro = SelectDistro().run()
    print(distro)
