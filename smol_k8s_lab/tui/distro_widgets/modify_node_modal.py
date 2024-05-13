# external libraries
from os import system
from textual import on
from textual.app import ComposeResult, NoMatches
from textual.binding import Binding
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class NodeModalScreen(ModalScreen):
    CSS_PATH = ["../css/node_modal.tcss"]
    BINDINGS = [Binding(key="b,escape,q",
                        key_display="b",
                        action="press_cancel",
                        description="Back")]

    def __init__(self, node: str, node_metadata: dict) -> None:
        self.node = node
        self.node_metadata = node_metadata
        super().__init__()

    def compose(self) -> ComposeResult:

        question = ('What would you like to do with '
                    f'[#C1FF87]{self.node}[/]?')
        # base screen grid
        with Grid(id="node-question-modal-screen", classes="modify-delete-size"):
            # grid for node question and buttons
            with Grid(id="node-question-box"):
                yield Label(question, id="node-modal-text")

                with Grid(id="modal-button-box"):
                    # modify button allows user to change apps (and soon distro details)
                    modify_button = Button("✏️  Modify", id="modify-node-button")
                    modify_button.tooltip = "Modify the node's metadata"
                    yield modify_button

                    # delete button deletes the node
                    delete_button = Button("🚮 Delete", id="delete-node-first-try")
                    delete_button.tooltip = "[#ffaff9]Delete[/] the node 😱"
                    yield delete_button

                    cancel = Button("🤷 Cancel", id="cancel")
                    cancel.tooltip = "Return to previous screen"
                    yield cancel

    def on_mount(self):
        """
        say the title if that tui.tts.screen_titles is set to True
        """
        self.call_after_refresh(self.app.play_screen_audio, screen="modify_node_modal")

    def action_press_cancel(self) -> None:
        """
        presses the cancel button
        """
        self.get_widget_by_id("cancel").action_press()

    @on(Button.Pressed)
    def button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "modify-node-button":
            print("ok")

        elif event.button.id == "delete-node-first-try":
            # don't display the first delete button or the modify button
            event.button.display = False
            self.get_widget_by_id("modify-node-button").display = False

            # are you sure, the text
            confirm_txt = ('Are you [b][i]sure[/][/] you want to [#ffaff9]delete[/]'
                           f' [#C1FF87]{self.node}[/]?')
            self.get_widget_by_id("node-modal-text").update(confirm_txt)
            self.app.play_screen_audio(screen="modify_node_modal", alt=True)

            # are you sure, the button
            sure_button = Button("🚮 Yes", id="delete-button-second-try")
            self.get_widget_by_id("modal-button-box").mount(sure_button,
                                                            before="#cancel")

        # if the user really wants to delete a node, we do it
        elif event.button.id == "delete-button-second-try":
            # after deleting pop the screen
            self.dismiss([self.node, None])

        elif event.button.id == "cancel":
            # resets the modal
            try:
                delete_2nd_try = self.get_widget_by_id("delete-button-second-try")

                if not delete_2nd_try.display:
                    self.app.pop_screen()
                else:
                    delete_2nd_try.display = False
                self.get_widget_by_id("modify-node-button").display = True

                question = f'What would you like to do with [#C1FF87]{self.node}[/]?'
                self.get_widget_by_id("node-modal-text").update(question)
                if self.app.bell_on_error:
                    self.app.action_say(
                            f"What would you like to do with {self.node}?"
                            )

                self.get_widget_by_id("delete-node-first-try").display = True
            except NoMatches:
                pass
                self.app.pop_screen()
