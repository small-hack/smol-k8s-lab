# smol-k8s-lab libraries
from smol_k8s_lab.k8s_distros.k3d import delete_k3d_cluster
from smol_k8s_lab.k8s_distros.k3s import uninstall_k3s
from smol_k8s_lab.k8s_distros.kind import delete_kind_cluster

# external libraries
from os import system
from textual import on
from textual.app import ComposeResult, NoMatches
from textual.binding import Binding
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Label
from textual.widgets.data_table import RowKey


class ClusterModalScreen(ModalScreen):
    CSS_PATH = ["./css/cluster_modal.tcss"]
    BINDINGS = [Binding(key="b,escape,q",
                        key_display="b",
                        action="press_cancel",
                        description="Back")]

    def __init__(self, cluster: str, distro: str, row_key: RowKey) -> None:
        self.cluster = cluster
        self.distro = distro
        self.row_key = row_key
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
                    modify_button = Button("✏️  Modify", id="modify-cluster-button")
                    modify_button.tooltip = "Modify the cluster's Applications"
                    yield modify_button

                    # delete button deletes the cluster
                    delete_button = Button("🚮 Delete", id="delete-cluster-first-try")
                    delete_button.tooltip = "[magenta]Delete[/] the existing cluster 😱"
                    # we can only delete the following k8s distro types
                    if self.distro not in ["kind", "k3d", "k3s"]:
                        delete_button.disabled = False
                    yield delete_button

                    cancel = Button("🤷 Cancel", id="cancel")
                    cancel.tooltip = "Return to previous screen"
                    yield cancel

    def on_mount(self):
        """ 
        say the title if that self.app.speak_screen_titles is set to True
        """
        if self.app.speak_screen_titles:
            self.app.action_say(
                    f"Screen title: What would you like to do with {self.cluster}?"
                    )

    def action_press_cancel(self) -> None:
        """
        presses the cancel button
        """
        self.get_widget_by_id("cancel").action_press()

    @on(Button.Pressed)
    def button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "modify-cluster-button":
            # set the current context to this cluster
            system(f"kubectl config use-context {self.cluster}")
            # call the apps page for this cluster
            self.app.action_request_apps_cfg()

        elif event.button.id == "delete-cluster-first-try":
            # don't display the first delete button or the modify button
            event.button.display = False
            self.get_widget_by_id("modify-cluster-button").display = False

            # are you sure, the text
            confirm_txt = ('Are you [b][i]sure[/][/] you want to [#ffaff9]delete[/]'
                           f' [#C1FF87]{self.cluster}[/]?')
            self.get_widget_by_id("cluster-modal-text").update(confirm_txt)
            if self.app.speak_screen_titles:
                self.app.action_say(f"Are you sure you want to delete {self.cluster}?")

            # are you sure, the button
            sure_button = Button("🚮 Yes", id="delete-button-second-try")
            self.get_widget_by_id("modal-button-box").mount(sure_button,
                                                            before="#cancel")

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

        elif event.button.id == "cancel":
            # resets the modal
            try:
                delete_2nd_try = self.get_widget_by_id("delete-button-second-try")

                if not delete_2nd_try.display:
                    self.app.pop_screen()
                else:
                    delete_2nd_try.display = False
                self.get_widget_by_id("modify-cluster-button").display = True

                question = f'What would you like to do with [#C1FF87]{self.cluster}[/]?'
                self.get_widget_by_id("cluster-modal-text").update(question)
                if self.app.bell_on_error:
                    self.app.action_say(
                            f"What would you like to do with {self.cluster}?"
                            )

                self.get_widget_by_id("delete-cluster-first-try").display = True
            except NoMatches:
                pass
                self.app.pop_screen()
