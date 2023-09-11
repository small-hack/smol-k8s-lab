#!/usr/bin/env python3.11
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.events import Mount
from textual.widgets import (Footer, Header, Input, Label, Pretty,
                             RadioButton, RadioSet, Rule, SelectionList, Static,
                             TabbedContent, TabPane)
from textual.widgets._toggle_button import ToggleButton
from textual.widgets.selection_list import Selection
from smol_k8s_lab.constants import (DEFAULT_APPS, DEFAULT_DISTRO,
                                    DEFAULT_DISTRO_OPTIONS, DEFAULT_CONFIG)


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
            # tab 1 - select a kubernetes distro
            with TabPane("Select k8s distro", id="select-distro"):
                with RadioSet():
                    # create all the radio button choices
                    for distro in sorted(DEFAULT_DISTRO_OPTIONS.keys()):
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

                yield Label(" ")

                yield Label("[b][green]Description[/][/]")
                yield Static(DEFAULT_CONFIG['k8s_distros'][DEFAULT_DISTRO]['description'],
                             id='selected-distro-tooltip')
                yield Label(" ")

            # tab 2 - allows selection of different argo cd apps to run in k8s
            with TabPane("Select k8s apps", id="select-apps"):
                full_list = []
                for argocd_app, app_metadata in DEFAULT_APPS.items():
                    full_list.append(Selection(argocd_app.replace("_","-"),
                                               argocd_app,
                                               app_metadata['enabled']))

                yield SelectionList[str](*full_list)
                yield Label(" ")

                yield Label("[b][green]Description[/][/]")
                yield Static("", id='selected-app-tooltip-description')
                yield Label(" ")

                yield Label("[b][cornflower_blue]Argo CD App Repository[/][/]")
                yield Static("", id='selected-app-tooltip-repo')

            # tab 3 - allows configuration of any selected apps
            with TabPane("Configure Apps", id="configure-apps"):
                # this is just for spacing
                yield Label(" ")

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

        # styling for the select-distro tab
        cute_question2 = "ʕ ᵔᴥᵔʔ Select which Kubernetes distributrion to use"
        self.query_one(RadioSet).border_title = cute_question2

    @on(Mount)
    @on(SelectionList.SelectedChanged)
    @on(TabbedContent.TabActivated)
    def update_configue_apps_view(self) -> None:
        # get the last item in the list selected items
        selected_items = self.query_one(SelectionList).selected

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

    @on(SelectionList.SelectionHighlighted)
    def update_selected_app_blurb(self) -> None:
        selection_list = self.query_one(SelectionList)

        # only the highlighted index
        highlighted_idx = selection_list.highlighted

        # the actual highlighted app
        highlighted_app = selection_list.get_option_at_index(highlighted_idx).value

        new_repo, new_blurb = generate_tool_tip(highlighted_app)

        # update the static text with the new app description and repo
        self.get_widget_by_id('selected-app-tooltip-repo').update(new_repo)
        self.get_widget_by_id('selected-app-tooltip-description').update(new_blurb)

    @on(RadioSet.Changed)
    def update_k8s_distro_description(self) -> None:
        pressed_index = self.query_one(RadioSet).pressed_index
        pressed_distro = sorted(DEFAULT_DISTRO_OPTIONS.keys())[pressed_index]
        description = DEFAULT_CONFIG['k8s_distros'][pressed_distro]['description']
        self.get_widget_by_id('selected-distro-tooltip').update(description)


def generate_tool_tip(app_name: str):
    """
    generate tooltip like:
    """
    app_description = DEFAULT_APPS[app_name]['description']

    repo_link = "/".join([DEFAULT_APPS[app_name]['argo']['repo'],
                          'tree',
                          DEFAULT_APPS[app_name]['argo']['ref'],
                          DEFAULT_APPS[app_name]['argo']['path']])

    repo = f"[steel_blue][link={repo_link}]{repo_link}[/link]"

    desc = f"[dim]{app_description}[/dim]"

    return repo, desc


if __name__ == "__main__":
    reply = ConfigureAll().run()
    print(reply)
