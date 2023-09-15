#!/usr/bin/env python3.11
from textual import on
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Container, Horizontal, Grid
from textual.binding import Binding
from textual.events import Mount
from textual.screen import ModalScreen
from textual.widgets import (Button, Footer, Header, Input, Label, RadioButton,
                             RadioSet, SelectionList, Static, Switch, TabbedContent,
                             TabPane)
from textual.widgets._toggle_button import ToggleButton
from textual.widgets.selection_list import Selection
from smol_k8s_lab.constants import (DEFAULT_APPS, DEFAULT_DISTRO,
                                    DEFAULT_DISTRO_OPTIONS, DEFAULT_CONFIG)


class HelpScreen(ModalScreen):
    """
    dialog screen to show help text
    """
    BINDINGS = [Binding(key="h,?,q",
                        key_display="h",
                        action="disable_help",
                        description="Exit Help Screen",
                        show=True)
                ]

    def compose(self) -> ComposeResult:
        # tips for new/forgetful users (the maintainers are also forgetful <3)
        help_dict = {"⬅️,➡️": "navigate tabs",
                     "tab": "switch to next pane, field, or button",
                     "shift+tab": "switch to previous pane, field, or button",
                     "enter": "press button",
                     "h,?": "toggle help screen"}

        welcome = ("[green]Use your 🐁 to click anything in this UI ✨ Or use "
                   "these key bindings:")

        with Container(id="help-container"):
            yield Label(welcome)
            with Container(id="help-options"):
                for help_option, help_text in help_dict.items():
                    with Grid(classes="help-option-row"):
                        key = f"[gold3]{help_option}[/gold3]"
                        key = key.replace(",", "[bright_white],[/]")
                        key = key.replace("+", "[bright_white]+[/]")
                        yield Label(key)
                        yield Label(help_text)

            yield Label("ℹ️ [dim]Clicking links varies based on your terminal, but"
                        " is usually one of:\n[gold3]option[/]+[gold3]click[/] or"
                        " [gold3]command[/]+[gold3]click[/] or [gold3]shift[/]+"
                        "[gold3]click", id="mouse-help")


    def action_disable_help(self) -> None:
        """
        if user presses '?', 'h', or 'q', we exit the help screen
        """
        self.app.pop_screen()


class ConfigureAll(App):
    """
    class helps the user configure specific custom values for applications such
    as hostnames and timezones
    """
    CSS_PATH = "./css/configure_all.tcss"
    BINDINGS = [Binding(key="h,?",
                        key_display="h",
                        action="request_help",
                        description="Show Help",
                        show=True),
                Binding(key="q",
                        key_display="q",
                        action="quit",
                        description="Quit smol-k8s-lab")]
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
            with TabPane("Select Kubernetes distro", id="select-distro"):

                # this is the distro picker
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

                # these are distro configurations 
                with VerticalScroll(id="k8s-distro-config"):
                    for distro, distro_metadata in DEFAULT_DISTRO_OPTIONS.items():
                        if distro == DEFAULT_DISTRO:
                            display = True
                        else:
                            display = False

                        node_class = f"{distro} nodes-input"
                        node_row = Horizontal(classes=f"{node_class}-row")
                        node_row.display = display
                        with node_row:
                            yield Label("number of nodes: ",
                                        classes=f"{node_class}-label")

                            disabled = False
                            if distro == 'k3s':
                                disabled = True

                            yield Button("➖",
                                         classes=f"{node_class}-minus-button",
                                         disabled=disabled)

                            # take number of nodes from config and make string
                            nodes = str(distro_metadata.get('nodes', 1))
                            yield Input(value=nodes,
                                        placeholder='enter number of nodes',
                                         classes=f"{node_class}",
                                        disabled=disabled)

                            yield Button("➕",
                                         classes=f"{node_class}-plus-button",
                                         disabled=disabled)


                        with Container(classes="kubelet-config-container"):
                            # take extra kubelet config args
                            args_label = Label("[green]Extra Args for Kubelet Config",
                                               classes=f"{distro} kubelet-config-label")
                            args_label.display = display
                            yield args_label

                            row_class = f"{distro} kubelet-arg"
                            row_container = Horizontal(classes=f"{row_class}-input-row")
                            row_container.display = display
                            with row_container:
                                kubelet_args = distro_metadata['kubelet_extra_args']
                                if kubelet_args:
                                    for key, value in kubelet_args.items():
                                            pholder = "optional kubelet config key arg"
                                            yield Input(value=key,
                                                        placeholder=pholder,
                                                        classes=f"{row_class}-input-key")

                                            yield Input(value=str(value),
                                                        placeholder=key,
                                                        classes=f"{row_class}-input-value")

                                            yield Button("🗑️",
                                                         classes=f"{row_class}-del-button")
                            new_button = Button("➕ Add New Arg",
                                                classes=f"{row_class}-add-button")
                            new_button.display = display
                            yield new_button

                        # take extra k3s args
                        if distro == 'k3s' or distro == 'k3d':
                            k3_container = Container(id="k3s-config-container",
                                                     classes=distro)
                            k3_container.display = display

                            with k3_container:
                                yield Label(" ", classes=distro)
                                yield Label("[green]Extra Args for k3s install script",
                                            classes=f"{distro} k3s-config-label")

                                if distro == 'k3s':
                                    k3s_args = distro_metadata['extra_cli_args']
                                else:
                                    k3s_args = distro_metadata['extra_k3s_cli_args']

                                if k3s_args:
                                    k3s_class = f'{distro} k3s-arg'
                                    for arg in k3s_args:
                                        placeholder = "enter an extra arg for k3s"
                                        with Container(classes=f'{k3s_class}-row'):
                                            yield Input(value=arg,
                                                        placeholder=placeholder,
                                                        classes=f"{k3s_class}-input")
                                            yield Button("🗑️",
                                                         classes=f"{k3s_class}-delete-button")

                                yield Button("➕ Add New Arg",
                                             classes=f"{k3s_class}-add-button")

                with Container(id="k8s-distro-description-container"):
                    yield Label("[b][green]Description[/][/]",
                                id='k8s-distro-description-label')
                    description = DEFAULT_DISTRO_OPTIONS[DEFAULT_DISTRO]['description']
                    formatted_description = format_description(description)
                    yield Static(f"{formatted_description}",
                                 id='k8s-distro-description')

            # tab 2 - allows selection of different argo cd apps to run in k8s
            with TabPane("Select Applications", id="select-apps"):
                full_list = []
                for argocd_app, app_metadata in DEFAULT_APPS.items():
                    full_list.append(Selection(argocd_app.replace("_","-"),
                                               argocd_app,
                                               app_metadata['enabled']))

                with Container(id="select-apps-container"):
                    # top left is the SelectionList of k8s applications
                    yield SelectionList[str](*full_list,
                                             id='selection-list-of-apps')

                    # top right are any input values we need
                    # this is a vertically scrolling container for all the inputs
                    with VerticalScroll(id='app-inputs'):
                        for app, metadata in DEFAULT_APPS.items():
                            secret_keys = metadata['argo'].get('secret_keys', None)
                            app_enabled = metadata['enabled']

                            # if app doesn't have secret keys, continue to next app
                            if not secret_keys:
                                continue
                            # if the app has secret keys
                            else:
                                init = metadata.get('init', False)
                                # if there's no init possible, skip this app
                                if not init:
                                    continue
                                else:
                                    init_enabled = init.get('enabled', False)

                                # make a pretty title for the app to configure
                                s_class = f"app-init-switch-and-labels-row {app}"
                                with Container(classes=s_class):
                                    app_title = app.replace('_', ' ').title()
                                    yield Label(f"[green]{app_title}[/]",
                                                classes="app-label")
                                    yield Label("Initialize: ",
                                                classes="app-init-switch-label")
                                    yield Switch(value=True,
                                                 id=f"{app}-init-switch",
                                                 classes="app-init-switch")

                                # container for all inputs associated with one app
                                app_inputs_class = f"{app} app-all-inputs-container"
                                with Container(id=f"{app}-inputs",
                                               classes=app_inputs_class):
                                    # iterate through the app's secret keys
                                    for secret_key, value in secret_keys.items():
                                        secret_label = secret_key.replace("_", " ")

                                        # create a gramatically corrrect placeholder
                                        if secret_key.startswith(('o','a','e')):
                                            article = "an"
                                        else:
                                            article = "a"
                                        placeholder = f"enter {article} {secret_label}"

                                        # create input variable
                                        input_classes = f"app-input {app}"
                                        if value:
                                            app_input = Input(placeholder=placeholder,
                                                              value=value,
                                                              classes=input_classes)
                                        else:
                                            app_input = Input(placeholder=placeholder,
                                                              classes=input_classes)

                                        # create the input row
                                        container_class = f"app-label-and-input {app}"
                                        with Horizontal(classes=container_class):
                                            label_class = f"app-input-label {app}"
                                            yield Label(f"{secret_label}: ",
                                                        classes=label_class)
                                            if not app_enabled or not init_enabled:
                                                app_input.display = False
                                            yield app_input

                    with VerticalScroll(id="app-description-container"):
                        # Bottom half of the screen for select-apps TabPane()
                        yield Label("[b][green]Description[/][/]",
                                    id="app-description-label")
                        yield Label("", id="app-description")

                        yield Label("[b][cornflower_blue]Argo CD App Repository[/][/]",
                                    id="app-repo-label")
                        yield Label("", id="app-repo")

    def action_show_tab(self, tab: str) -> None:
        """Switch to a new tab."""
        self.get_child_by_type(TabbedContent).active = tab

    def on_mount(self) -> None:
        # screen and header styling
        self.screen.styles.border = ("heavy", "cornflowerblue")
        self.title = "🧸smol k8s lab"
        self.sub_title = "now with more 🦑"

        # styling for the select-apps tab - select apps container - left
        select_apps_title = "Select apps"
        self.query_one(SelectionList).border_title = select_apps_title

        # styling for the select-apps tab - configure apps container - right
        app_config_title = "ʕ ᵔᴥᵔʔ Configure initalization for each selected app"
        self.get_widget_by_id("app-inputs").border_title = app_config_title

        # styling for the select-distro tab - top
        select_k8s_title = "ʕ ᵔᴥᵔʔ Select Kubernetes Distribution"
        self.query_one(RadioSet).border_title = select_k8s_title

        # styling for the select-distro tab - middle
        configure_distro_title = "ʕ ᵔᴥᵔʔ Configure selected Kubernetes Distribution"
        self.get_widget_by_id('k8s-distro-config').border_title = configure_distro_title

    @on(Mount)
    @on(SelectionList.SelectedChanged)
    @on(TabbedContent.TabActivated)
    def update_configure_apps_view(self) -> None:
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
        self.get_widget_by_id('app-repo').update(new_repo)
        self.get_widget_by_id('app-description').update(new_blurb)

    @on(Switch.Changed)
    def show_or_hide_init_inputs(self, event: Switch.Changed) -> None:
        truthy_value = event.value
        app = event.switch.id.split("-init-switch")[0]
        app_inputs = self.get_widget_by_id(f"{app}-inputs")
        app_inputs.display = truthy_value

    @on(RadioSet.Changed)
    def update_k8s_distro_description(self) -> None:
        pressed_index = self.query_one(RadioSet).pressed_index
        distro = sorted(DEFAULT_DISTRO_OPTIONS.keys())[pressed_index]
        desc = format_description(DEFAULT_CONFIG['k8s_distros'][distro]['description'])
        self.get_widget_by_id('k8s-distro-description').update(desc)

        for default_distro_option in DEFAULT_DISTRO_OPTIONS.keys():
            # get any objects using this distro's name as their class
            distro_class_objects = self.query(f".{default_distro_option}")

            if default_distro_option == distro:
                enabled = True
            else:
                enabled = False

            # change display to True if the radio is pressed, else False
            if distro_class_objects:
                for distro_obj in distro_class_objects:
                    distro_obj.display = enabled

    def action_request_help(self) -> None:
        """ 
        if the user presses 'h' or '?', show the help modal screen
        """
        self.push_screen(HelpScreen())


def generate_tool_tip(app_name: str):
    """
    generate tooltip like:
    """
    description = format_description(DEFAULT_APPS[app_name]['description'])

    repo_link = "/".join([DEFAULT_APPS[app_name]['argo']['repo'],
                          'tree',
                          DEFAULT_APPS[app_name]['argo']['ref'],
                          DEFAULT_APPS[app_name]['argo']['path']])

    repo = f"[steel_blue][link={repo_link}]{repo_link}[/link]"

    return repo, description


def format_description(description: str):
    """
    change description to dimmed colors
    links are changed to steel_blue and not dimmed
    """
    description = description.replace("[link", "[/dim][steel_blue][link")
    description = description.replace("[/link]", "[/link][/steel_blue][dim]")

    return f"""[dim]{description}[/dim]"""



if __name__ == "__main__":
    reply = ConfigureAll().run()
    print(reply)
