#!/usr/bin/env python3.11
"""
       Name: tui
DESCRIPTION: smol-k8s-lab Terminal User Interface using Textual
             This is currently a work in progress
     AUTHOR: @jessbot on GitHub
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, Static


class clusterDisplay(Static):
    """
    A widget to display a cluster on the current machine
    """



class smolK8sClusterInfo(Static):
    """
    A k8s cluster listing widget
    """
    def compose(self) -> ComposeResult:
        """
        Create child widgets of clusters we've setup
        """
        yield clusterDisplay("default")


class smolK8sLabApp(App):
    """
    A Textual app to manage metal k8s clusters.
    Supports:
      - creating a new config
      - creating your cluster
      - viewing your current clusters at a glance
    """
    CSS_PATH = "smol_k8s_lab_app.css"
    BINDINGS = [("m", "toggle_dark", "Toggle dark mode"),
                ("d", "delete_cluster", "Delete a cluster")]

    def compose(self) -> ComposeResult:
        """
        Create child widgets for the app.
        """
        yield Header()
        yield Footer()
        yield Container(smolK8sClusterInfo())

    def action_toggle_dark(self) -> None:
        """
        An action to toggle dark mode
        """
        self.dark = not self.dark


if __name__ == "__main__":
    app = smolK8sLabApp()
    app.run()
