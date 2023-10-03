from textual import on
from textual.app import ComposeResult, NoMatches
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Label
from smol_k8s_lab.k8s_distros.k3d import delete_k3d_cluster
from smol_k8s_lab.k8s_distros.k3s import uninstall_k3s
from smol_k8s_lab.k8s_distros.kind import delete_kind_cluster
from smol_k8s_lab.utils.subproc import subproc


class ClusterModalScreen(ModalScreen):
    CSS_PATH = ["./css/cluster_modal.css"]

    def __init__(self, cluster: str, distro: str) -> None:
        self.cluster = cluster
        self.distro = distro
        super().__init__()

    def compose(self) -> ComposeResult:
        # base screen grid
        with Grid(id="cluster-question-modal-screen"):
            # grid for cluster question and buttons
            with Grid(id="cluster-question-box"):
                yield Label(
                        f'How would you like to proceed with cluster "{self.cluster}"?',
                        id="cluster-modal-text"
                        )

                with Grid(id="modal-button-box"):
                    yield Button("✏️ Modify", id="modify-cluster-button")
                    delete_button = Button("🚮 Delete", id="delete-cluster-first-try")
                    # we can only delete the following k8s distro types
                    if self.distro not in ["kind", "k3d", "k3s"]:
                        delete_button.disabled = False
                    yield delete_button

                    cancel = Button("🤷 Cancel", id="cancel")
                    yield cancel

    @on(Button.Pressed)
    def button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "modify-cluster-button":
            # set the current context to this cluster
            subproc([f"kubectl config use-context {self.cluster}"])
            # call the apps page for this cluster
            self.app.action_request_apps_cfg()

        elif event.button.id == "delete-cluster-first-try":
            # don't display the first delete button or the modify button
            event.button.display = False
            self.get_widget_by_id("modify-cluster-button").display = False

            # are you sure, the text
            are_you_sure = f"Are you sure you want to delete {self.cluster}"
            self.get_widget_by_id("cluster-modal-text").update(are_you_sure)

            # are you sure, the button
            sure_button = Button("Yes", id="delete-button-second-try")
            self.get_widget_by_id("cluster-question-box").mount(sure_button)

        # if the user really wants to delete a cluster, we do it
        elif event.button.id == "delete-button-second-try":
            if self.distro == "k3s":
                uninstall_k3s()

            if self.distro == "k3d":
                delete_k3d_cluster(self.cluster.replace("k3d-", ""))

            if self.distro == "kind":
                delete_kind_cluster(self.cluster.replace("kind-", ""))

            # after deleting pop the screen
            self.app.pop_screen()

        elif event.button.id == "cancel":
            # resets the modal
            try:
                delete_2nd_try = self.get_widget_by_id("delete-button-second-try")

                if not delete_2nd_try.display:
                    self.app.pop_screen()
                else:
                    delete_2nd_try.display = False
                self.get_widget_by_id("modify-cluster-button").display = True

                reset_text = f"How would you like to proceed with {self.cluster}?"
                self.get_widget_by_id("cluster-modal-text").update(reset_text)
            except NoMatches:
                pass
                self.app.pop_screen()
