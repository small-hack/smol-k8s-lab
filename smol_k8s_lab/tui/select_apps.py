#!/usr/bin/env python3.11
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.events import Mount
from textual.widgets import Footer, Header, Pretty, SelectionList, Button
from textual.widgets.selection_list import Selection
from smol_k8s_lab.env_config import DEFAULT_CONFIG


DEFAULT_APPS = DEFAULT_CONFIG['apps']


class InitialApps(App[None]):
    CSS_PATH = "select_apps.tcss"
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
        initialize app contents
        """
        header = Header()
        header.tall = True
        yield header
        with Horizontal():
            full_list = []
            for argocd_app, app_metadata in DEFAULT_APPS.items():
                if argocd_app == 'cilium':
                    full_list.append(Selection("cilium - an app for ebpf stuff",
                                               "cilium",
                                               False))
                elif argocd_app != 'cilium' and app_metadata['enabled']:
                    full_list.append(Selection(argocd_app.replace("_","-"),
                                               argocd_app,
                                               True))
                else:
                    full_list.append(Selection(argocd_app.replace("_","-"),
                                               argocd_app))

            yield SelectionList[str](*full_list)
            yield Pretty([])
        yield Button("Next", id="next")
        yield Footer()

    def on_mount(self) -> None:
        self.screen.styles.border = ("heavy", "cornflowerblue")
        self.title = "🧸smol k8s lab"
        self.sub_title = "now with more 🦑"
        cute_question = "ʕ ᵔᴥᵔʔ Select which apps to install on k8s"
        self.query_one(SelectionList).border_title = cute_question
        self.query_one(Pretty).border_title = "Selected Apps"

    @on(Mount)
    @on(SelectionList.SelectedChanged)
    def update_selected_view(self) -> None:
        self.query_one(Pretty).update(self.query_one(SelectionList).selected)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.exit(self.query_one(SelectionList).selected)


if __name__ == "__main__":
    reply = InitialApps().run()
    print(reply)
