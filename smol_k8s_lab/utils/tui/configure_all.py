#!/usr/bin/env python3.11
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
# from textual.containers import VerticalScroll, Horizontal
from textual.events import Mount
from textual.widgets import (Footer, Header, Input, Label, Pretty,
                             RadioButton, RadioSet, Rule, SelectionList,
                             TabbedContent, TabPane)
from textual.widgets._toggle_button import ToggleButton
from textual.widgets.selection_list import Selection
from smol_k8s_lab.constants import DEFAULT_APPS, DEFAULT_DISTRO, DEFAULT_DISTRO_OPTIONS


class ConfigureAll(App):
    """
    class helps the user configure specific custom values for applications such
    as hostnames and timezones
    """
    CSS_PATH = "./css/configure_all.tcss"
    BINDINGS = [
        Binding(key="tab",
                action="focus_next",
                description="Focus next",
                show=True),
        Binding(key="q",
                key_display="q",
                action="quit",
                description="Quit smol-k8s-lab")
    ]
    ToggleButton.BUTTON_INNER = '♥'

    def compose(self) -> ComposeResult:
        """
        Compose app with tabbed content.
        """
        header = Header()
        header.tall = True
        yield header
        # Footer to show keys
        yield Footer()

        # Add the TabbedContent widget
        with TabbedContent(initial="select-distro"):
            # tab 1
            with TabPane("Select k8s distro", id="select-distro"):
                with RadioSet():
                    # create all the radio button choices
                    for distro in DEFAULT_DISTRO_OPTIONS:
                        enabled = False

                        if distro == DEFAULT_DISTRO:
                            enabled = True

                        # note that k3s is in alpha testing
                        elif distro == 'k3d':
                            distro += ' [magenta](alpha)[/]'

                        radio_button = RadioButton(distro, value=enabled)
                        # make the radio button cute
                        radio_button.BUTTON_INNER = '♥'

                        yield radio_button

            # tab 2 - allows selection of different argo cd apps to run in k8s
            with TabPane("Select Apps", id="select-apps"):
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
                yield Pretty([], id='pretty-selected-apps')

            # tab 3 - allows configuration of any selected apps
            with TabPane("Configure Apps", id="configure-apps"):
                yield Label(" ")
                # yield Pretty(DEFAULT_APPS, id='default-apps')

                for app, metadata in DEFAULT_APPS.items():
                    secret_keys = metadata['argo'].get('secret_keys', None)
                    init = metadata.get('init', None)
                    if init:
                        init_enabled = metadata['init'].get('enabled', False)
                    else:
                        init_enabled = False

                    if metadata['enabled'] and secret_keys and init_enabled:
                        # make a pretty title for the app to configure
                        app_title = app.replace('_', ' ').title()
                        yield Label(f"[green]{app_title}[/]", classes=app)

                        for secret_key, value in secret_keys.items():
                            if not value:
                                yield Input(placeholder=secret_key, classes=app)
                            else:
                                yield Input(placeholder=value, classes=app)
                        yield Rule(classes=app)

    def action_show_tab(self, tab: str) -> None:
        """Switch to a new tab."""
        self.get_child_by_type(TabbedContent).active = tab

    def on_mount(self) -> None:
        # screen and header styling
        self.screen.styles.border = ("heavy", "cornflowerblue")
        self.title = "🧸smol k8s lab"
        self.sub_title = "now with more 🦑"

        # styling for the select-apps tab
        cute_question = "ʕ ᵔᴥᵔʔ Select which apps to install on k8s"
        self.query_one(SelectionList).border_title = cute_question
        self.get_widget_by_id('pretty-selected-apps').border_title = "Selected Apps"

    @on(Mount)
    @on(SelectionList.SelectedChanged)
    @on(TabbedContent.TabActivated)
    def update_selected_view(self) -> None:
        # update the pretty view of the selected options
        selected_items = self.query_one(SelectionList).selected
        self.get_widget_by_id('pretty-selected-apps').update(selected_items)

        # for each application in DEFAULT_APPS
        for application in DEFAULT_APPS.keys():
            # get any objects using this application's name as their class
            app_class_objects = self.query(f".{application}")

            # if the application is in the selected items, set enabled to True
            if application in selected_items:
                enabled = True
            else:
                enabled = False

            # set the DEFAULT_APPS
            DEFAULT_APPS[application]['enabled'] = enabled
            if app_class_objects:
                for app_obj in app_class_objects:
                    app_obj.display = enabled


if __name__ == "__main__":
    reply = ConfigureAll().run()
    print(reply)
