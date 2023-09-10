#!/usr/bin/env python3.11
from textual.app import App, ComposeResult
from textual.widgets import RadioButton, RadioSet


class SelectDistro(App[None]):
    CSS_PATH = "./css/select_distro.tcss"

    def compose(self) -> ComposeResult:
        with RadioSet():
            yield RadioButton("k3s", value=True)
            yield RadioButton("k3d [red](alpha)[/]")
            yield RadioButton("k0s")
            yield RadioButton("kind", id="focus_me")

    def on_mount(self) -> None:
        self.query_one(RadioSet).focus()


if __name__ == "__main__":
    SelectDistro().run()
