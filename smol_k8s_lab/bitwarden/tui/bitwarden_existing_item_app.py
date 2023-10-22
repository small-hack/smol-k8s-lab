from textual.app import App, ComposeResult
from textual.containers import Grid, VerticalScroll, Container
from textual.widgets import Label, Pretty, Checkbox, Button, RadioSet, RadioButton


class AskUserForDuplicateStrategy(App[None]):
    """ 
    ask user how to handle creating an item when duplicate[s] found
    """

    CSS_PATH = ["./bitwarden_existing_item.tcss"]

    def __init__(self, duplicate_item: dict | list, item_searched: str) -> None:
        self.duplicate_item = duplicate_item
        self.item_searched = item_searched
        self.always_do = False
        super().__init__()

    def compose(self) -> ComposeResult:
        """
        check if we need to grab the password or not
        """
        with Grid(id="main-screen-grid"):
            with Container(id="all-duplicates-view"):
                if isinstance(self.duplicate_item, list):
                    with RadioSet():
                        for item in self.duplicate_item:
                            button = RadioButton(item['id'])
                            # set the radio button to be a heart :3
                            button.BUTTON_INNER = "♥"
                            yield button
                with VerticalScroll(id="pretty-scroll"):
                    yield Pretty("Select an item above to preview")


            with Grid(id="question-box"):
                yield Label("How would you like to proceed?")
                check_box = Checkbox("Always perform this action",
                                     id="always-checkbox")
                yield check_box

                with Grid(id="button-grid"):
                    edit_button = Button("✏️ Edit", id="edit-button")
                    edit_button.tooltip = "Edit the existing Vault item with new info"
                    yield edit_button

                    duplicate_button = Button("👥 Duplicate", id="duplicate-button")
                    duplicate_button.tooltip = "Create an additional Vault item"
                    yield duplicate_button

                    no_action_button = Button("⛔️ No Action", id="no-action-button")
                    no_action_button.tooltip = "Use the existing Vault item"
                    yield no_action_button

    def on_mount(self) -> None:
        """
        border styling and enabling of the edit button
        """
        pretty_scroll = self.get_widget_by_id("pretty-scroll")
        pretty_scroll.border_title = "Bitarden Vault Item [#C1FF87]Preview[/]"
        if isinstance(self.duplicate_item, list):
            box_title = ('[#ffaff9][i]duplicate[/i] items[/] found for '
                         f'[#C2FF87]{self.item_searched}[/] in your vault')

            # disable the edit button till a user has selected an item
            edit_button = self.get_widget_by_id("edit-button")
            edit_button.disabled = True
            edit_button.tooltip = ("Select an item above to have smol-k8s-lab "
                                   "edit the existing item in your Vault.")

            self.query_one(RadioSet).border_title = (
                    "[#ffaff9]♥[/] [i]select[/] an item to view/edit")
        else:
            self.query_one(Pretty).update(self.duplicate_item)
            box_title = (
                    "An [#ffaff9][i]existing[/i] item[/] for "
                    f"[#C1FF87]{self.item_searched}[/] found in your vault"
                    )

        self.get_widget_by_id("main-screen-grid").border_title = box_title

    def on_check_box_ticked(self, event: Checkbox.Changed) -> None:
        """ 
        if the checkbox is selected, we update the self.always_do variable
        """
        self.always_do = event.checkbox.value

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """ 
        if any radio set button is selected, update the Pretty widget and
        make sure the edit button is enabled again
        """
        pressed_index = event.radio_set.pressed_index
        self.query_one(Pretty).update(self.duplicate_item[pressed_index])
        self.get_widget_by_id("edit-button").disabled = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        if any button is pressed, take action and exit
        """
        if isinstance(self.duplicate_item, list):
            item = self.duplicate_item[self.query_one(RadioSet).pressed_index]
        else:
            item = self.duplicate_item

        if event.button.id == "no-action-button":
            self.app.exit(["no_action", self.always_do, item])

        if event.button.id == "edit-button":
            self.app.exit(["edit", self.always_do, item])

        if event.button.id == "duplicate-button":
            self.app.exit(["duplicate", self.always_do, item])

# for testing only
if __name__ == "__main__":
    item = {"creationDate": "2022-03-19T12:22:02.920Z",
            "id": "2222224b-u94j-rv85-8787-y5555555555o",
            "organizationId": None,
            "folderId": "33333333-c5l8-328a-ge49-ve0000000000",
            "name": "www.bol.com",
            "notes": None,
            "favorite":  False,
            "login": {
                "uris": [
                    {"match": None,
                     "uri": "https://www.test.com/"}
                ],
                "username": "test@test.test",
                "password": "passwordthatissupposedtobesecurebutisnot",
                "passwordRevisionDate": None}
            }
    item_list = [
            {"creationDate": "2022-02-19T12:22:02.920Z",
            "id": "2222224b-u94j-rv85-8787-y5555555555o",
            "organizationId": None,
            "folderId": "33333333-c5l8-328a-ge49-ve0000000000",
            "name": "www.bol.com",
            "notes": None,
            "favorite":  False,
            "login": {
                "uris": [
                    {"match": None,
                     "uri": "https://www.test.com/"}
                ],
                "username": "test@test.test",
                "password": "passwordthatissupposedtobesecure",
                "passwordRevisionDate": None}
            },
            {"creationDate": "2023-02-19T12:22:02.920Z",
            "id": "2247q311-b06a-ww85-9532-a00000bb548f",
            "organizationId": None,
            "folderId": "33333333-c5l8-328a-ge49-ve0000000000",
            "name": "www.bol.com",
            "notes": None,
            "favorite":  False,
            "login": {
                "uris": [
                    {"match": None,
                     "uri": "https://www.test.com/"}
                ],
                "username": "test@test.test",
                "password": "supposedtobesecurebutisnot",
                "passwordRevisionDate": None}
            }
                 ]
    app = AskUserForDuplicateStrategy(item,
                                      "argocd-admin-credentials-argo.test.com")
    app.run()
