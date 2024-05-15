# smol-k8s-lab libraries
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.k8s_distros.k3d import delete_k3d_cluster
from smol_k8s_lab.k8s_distros.k3s import uninstall_k3s
from smol_k8s_lab.k8s_distros.kind import delete_kind_cluster
from smol_k8s_lab.utils.run.subproc import subproc

# external libraries
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Label
from textual.widgets.data_table import RowKey


class ClusterModalScreen(ModalScreen):
    """
    A simple textual modal screen for asking a user what they'd like to do with
    their cluster.

    Includes a few buttons for launching apps screen, edit nodes screen, and
    deleting clusters.
    """
    CSS_PATH = ["../css/cluster_modal.tcss"]
    BINDINGS = [
            Binding(key="b,escape,q",
                    key_display="b",
                    action="cancel_button",
                    description="Back"),
            Binding(key="f5",
                    key_display="f5",
                    description="Speak",
                    action="app.speak_element",
                    show=True)
            ]

    def __init__(self, cluster: str, distro: str, row_key: RowKey) -> None:
        self.cluster = cluster
        self.distro = distro
        self.row_key = row_key
        # keep the current context in memory in case the user cancels
        self.start_current_context = subproc(["kubectl config current-context"],
                                             spinner=False, quiet=True)

        # set the context to the current cluster so we can operate on it
        subproc([f"kubectl config use-context {self.cluster}"], spinner=False,
                quiet=True)
        self.k8s_ctx = K8s()

        super().__init__()

    def compose(self) -> ComposeResult:

        question = ('What would you like to do with '
                    f'[#C1FF87]{self.cluster}[/]?')
        # base screen grid
        with Grid(id="cluster-question-modal-screen", classes="modify-delete-size"):
            # grid for cluster question and buttons
            with Grid(id="cluster-question-box"):
                yield Label(question, id="cluster-modal-text")

                with Grid(id="modal-button-box"):
                    # modify button allows user to change apps (and soon distro details)
                    modify_apps_button = Button("✏️  Modify Apps",
                                                id="modify-apps-button")
                    modify_apps_button.tooltip = "Modify the cluster's Applications"
                    yield modify_apps_button

                    if self.distro == "k3s":
                        # modify button allows user to change nodes
                        modify_nodes_button = Button("🖥️ Modify Nodes",
                                                     id="modify-nodes-button")
                        modify_nodes_button.tooltip = "Modify the cluster's nodes"
                        yield modify_nodes_button

                    # delete button deletes the cluster
                    delete_button = Button("🚮 Delete", id="delete-cluster-first-try")
                    delete_button.tooltip = "[#ffaff9]Delete[/] the existing cluster 😱"
                    # we can only delete the following k8s distro types
                    if self.distro not in ["kind", "k3d", "k3s"]:
                        delete_button.disabled = False
                    yield delete_button

    def on_mount(self):
        """
        say the title if that self.app.speak_screen_titles is set to True
        """
        question_box = self.get_widget_by_id("cluster-question-box")
        question_box.border_subtitle = "[@click=screen.cancel_button]cancel[/]"

        self.call_after_refresh(self.app.play_screen_audio, screen="cluster_modal")

    def action_cancel_button(self):
        subproc([f"kubectl config use-context {self.start_current_context}"])
        self.app.pop_screen()

    @on(Button.Pressed)
    def button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "modify-apps-button":
            # call the apps page for this cluster
            self.app.action_request_apps_cfg(app_to_highlight="",
                                             modify_cluster=True)

        elif event.button.id == "modify-nodes-button":
            # call the nodes page for this cluster
            self.app.action_request_nodes_cfg(self.distro, True)

        elif event.button.id == "delete-cluster-first-try":
            # don't display the first delete button or the modify button
            event.button.display = False
            self.get_widget_by_id("modify-apps-button").display = False

            # are you sure, the text
            confirm_txt = ('Are you [b][i]sure[/][/] you want to [#ffaff9]delete[/]'
                           f' [#C1FF87]{self.cluster}[/]?')
            self.get_widget_by_id("cluster-modal-text").update(confirm_txt)
            self.app.play_screen_audio(screen="cluster_modal", alt=True, say_title=False)

            # are you sure, the button
            sure_button = Button("🚮 Yes", id="delete-button-second-try")
            self.get_widget_by_id("modal-button-box").mount(sure_button)

            nope_button = Button("😱 No", id="nope-button")
            self.get_widget_by_id("modal-button-box").mount(nope_button)

        # if the user really wants to delete a cluster, we do it
        elif event.button.id == "delete-button-second-try":
            if self.distro == "k3s":
                res = uninstall_k3s(self.cluster)
                self.app.notify(res)

            if self.distro == "k3d":
                res = delete_k3d_cluster(self.cluster)
                if "Success" in res:
                    self.app.notify("Sucessfully deleted cluster",
                                    severity="information")
                else:
                    if self.app.bell_on_error:
                        self.app.bell()
                    self.app.notify("Something went wrong with deleting the cluster!",
                                    timeout=10,
                                    severity="error")

            if self.distro == "kind":
                delete_kind_cluster(self.cluster.replace("kind-", ""))

            # after deleting pop the screen
            self.dismiss([self.cluster, self.row_key])

        elif event.button.id == "nope-button":
            # resets the modal
            delete_2nd_try = self.get_widget_by_id("delete-button-second-try")
            delete_2nd_try.display = False
            nope = self.get_widget_by_id("nope-button")
            nope.display = False

            self.get_widget_by_id("modify-apps-button").display = True

            question = f'What would you like to do with [#C1FF87]{self.cluster}[/]?'
            self.get_widget_by_id("cluster-modal-text").update(question)
            self.app.play_screen_audio("cluster_modal")

            self.get_widget_by_id("delete-cluster-first-try").display = True
