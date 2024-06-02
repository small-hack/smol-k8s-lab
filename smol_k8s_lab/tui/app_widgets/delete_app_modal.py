from textual import on
from textual.binding import Binding
from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox


class DeleteAppModalScreen(ModalScreen):
    CSS_PATH = ["../css/app_delete_modal.tcss"]
    BINDINGS = [Binding(key="b,escape,q",
                        key_display="b",
                        action="app.pop_screen",
                        description="Back"),
            Binding(key="f5",
                    key_display="f5",
                    description="Speak",
                    action="app.speak_element",
                    show=True)]

    def __init__(self, app_name: str) -> None:
        self.app_name = app_name
        self.force_delete = False
        super().__init__()

    def compose(self) -> ComposeResult:
        # base screen grid
        with Grid(id="app-delete-question-modal-screen"):
            # grid for app question and buttons
            with Grid(id="app-delete-question-box"):
                with Grid(classes="modal-button-box"):
                    yield Checkbox("🔨 [i]Force[/i]",
                                   value=False,
                                   id="force-delete")

                    submit = Button("🚮 Delete", id="app-delete")
                    submit.tooltip = f"Confirm deletion of {self.app_name}"
                    yield submit

    def on_mount(self) -> None:
        """
        do screen audio if needed
        """
        self.call_after_refresh(self.app.play_screen_audio, screen="delete_app")
        modal_box = self.get_widget_by_id("app-delete-question-box")
        question = (
                "Are you [i]sure[/i] you want to [#ffaff9]delete[/] the [#C1FF87]"
                f"{self.app_name}[/] Application?"
                )
        modal_box.border_title = question
        modal_box.border_subtitle = "[@click=screen.close_window]cancel[/]"

    @on(Button.Pressed)
    def button_pressed(self, event: Button.Pressed) -> None:
        """
        if button is pressed, we tell the next screen to proceed with the delete
        """
        if event.button.id == "app-delete":
            # returns True for delete_confirm and checks the checkbox for force_delete
            self.dismiss((True,False))

    @on(Checkbox.Changed)
    def record_checkbox_change(self, event: Checkbox.Changed) -> None:
        """
        change self.force_delete to True if checkbox is checked, or false if not
        """
        self.force_delete = event.checkbox.value

    def action_close_window(self, event: Button.Pressed) -> None:
        # returns False for both delete_confirm and force_delete
        self.dismiss((False,False))
