#!/usr/bin/env python3.11
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.events import Mount
from textual.widgets import Footer, Header, Pretty, SelectionList
from textual.widgets.selection_list import Selection
from smol_k8s_lab.env_config import DEFAULT_CONFIG


DEFAULT_APPS = DEFAULT_CONFIG['apps']


class InitialApps(App[None]):
    CSS_PATH = "select_apps.tcss"

    def compose(self) -> ComposeResult:
        """
        initialize app contents
        """
        yield Header()
        with Horizontal():
            full_list = []
            for argocd_app, app_metadata in DEFAULT_APPS.items():
                if argocd_app == 'cilium':
                    full_list.append(
                            Selection("cilium - an app for ebpf stuff",
                                      "cilium",
                                      False)
                                     )
                elif argocd_app != 'cilium' and app_metadata['enabled']:
                    full_list.append(
                            Selection(argocd_app.replace("_","-"), argocd_app, True)
                            )
                else:
                    full_list.append(
                            Selection(argocd_app.replace("_","-"), argocd_app)
                            )

            yield SelectionList[str](*full_list)
            yield Pretty([])
        yield Footer()

    def on_mount(self) -> None:
        self.title = "🧸smol k8s lab"
        self.sub_title = "now with more 🦑"
        self.query_one(SelectionList).border_title = "Shall we install some k8s apps?"
        self.query_one(Pretty).border_title = "Selected Apps"

    @on(Mount)
    @on(SelectionList.SelectedChanged)
    def update_selected_view(self) -> None:
        self.query_one(Pretty).update(self.query_one(SelectionList).selected)


if __name__ == "__main__":
    InitialApps().run()
