#!/usr/bin/env python3.11
from textual import on
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Container, Horizontal, Grid
from textual.binding import Binding
from textual.events import Mount
from textual.screen import ModalScreen
from textual.widgets import (Button, Footer, Header, Input, Label,
                             Select, SelectionList, Static, Switch, TabbedContent,
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

        welcome = ("Use your 🐁 to click anything in this UI ✨ Or use "
                   "these key bindings:")

        with Container(id="help-container"):
            yield Label(welcome, id="help-label")
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
                # create all the select choices
                my_options = tuple(DEFAULT_DISTRO_OPTIONS.keys())
                yield Select(((line, line) for line in my_options),
                             prompt="Select Kubernetes Distro",
                             id="distro-drop-down")

                # these are distro configurations 
                with VerticalScroll(id="k8s-distro-config"):
                    for distro, distro_metadata in DEFAULT_DISTRO_OPTIONS.items():
                        if distro == DEFAULT_DISTRO:
                            display = True
                        else:
                            display = False

                        # node input row
                        node_class = f"{distro} nodes-input"
                        node_row = Horizontal(classes=f"{node_class}-row")
                        node_row.display = display
                        node_header = Label("Number of nodes to deploy",
                                            classes=f"{node_class}-header-label")
                        node_header.display = display
                        yield node_header
                        with node_row:
                            disabled = False
                            if distro == 'k3s':
                                disabled = True

                            # take number of nodes from config and make string
                            nodes = distro_metadata.get('nodes', False)
                            if nodes:
                                control_nodes = str(nodes.get('control_plane', 1))
                                worker_nodes = str(nodes.get('workers', 0))
                            else:
                                control_nodes = "1"
                                worker_nodes = "0"

                            yield Label("control plane nodes:",
                                        classes=f"{node_class}-label")
                            yield Input(value=control_nodes,
                                        placeholder='1',
                                        classes=f"{node_class}-control-input",
                                        disabled=disabled)

                            yield Label("worker nodes:",
                                        classes=f"{node_class}-label")
                            yield Input(value=worker_nodes,
                                        placeholder='0',
                                        classes=f"{node_class}-worker-input",
                                        disabled=disabled)

                        args_label = Label("Extra Args for Kubelet Config",
                                           classes=f"{distro} kubelet-config-label")
                        args_label.display = display
                        yield args_label
                        # kubelet config section
                        with Container(classes="kubelet-config-container"):
                            # take extra kubelet config args
                            row_class = f"{distro} kubelet-arg"
                            row_container = Horizontal(classes=f"{row_class}-input-row")
                            row_container.display = display
                            kubelet_args = distro_metadata['kubelet_extra_args']
                            if kubelet_args:
                                for key, value in kubelet_args.items():
                                    with row_container:
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
                            k3_class = f"{distro} k3s-config-container"
                            k3_container = Container(classes=k3_class)
                            k3_container.display = display

                            with k3_container:
                                yield Label("Extra Args for k3s install script",
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
                                                         classes=f"{k3s_class}-del-button")

                                yield Button("➕ Add New Arg",
                                             classes=f"{k3s_class}-add-button")

                with Container(id="k8s-distro-description-container"):
                    yield Label("[b]Description[/]",
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
                                    yield Label(app_title, classes="app-label")
                                    yield Label("Initialize: ",
                                                classes="app-init-switch-label")
                                    yield Switch(value=init_enabled,
                                                 id=f"{app}-init-switch",
                                                 classes="app-init-switch")

                                # container for all inputs associated with one app
                                app_inputs_class = f"{app} app-all-inputs-container"
                                inputs_container = Container(id=f"{app}-inputs",
                                                       classes=app_inputs_class)

                                if not init_enabled:
                                    inputs_container.display = False

                                with inputs_container:
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
                                        container_class = f"app-input-row {app}"
                                        with Horizontal(classes=container_class):
                                            label_class = f"app-input-label {app}"
                                            yield Label(f"{secret_label}: ",
                                                        classes=label_class)
                                            yield app_input

                    with VerticalScroll(id="app-description-container"):
                        # Bottom half of the screen for select-apps TabPane()
                        yield Label("[b]Description[/]",
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
        DEFAULT_APPS[app]['init']['enabled'] = truthy_value

    @on(TabbedContent.TabActivated)
    def show_or_hide_init_inputs_on_new_tab(self,) -> None:
        switches = self.query(".app-init-switch")
        for switch in switches:
            app = switch.id.split("-init-switch")[0]
            app_inputs = self.get_widget_by_id(f"{app}-inputs")
            app_inputs.display = switch.value

    @on(Select.Changed)
    def update_k8s_distro_description(self, event: Select.Changed) -> None:
        distro = str(event.value)
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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        get pressed button and act on it
        """
        # lets you delete a kubelet-arg row
        if "kubelet-arg-del-button" in event.button.classes:
            parent_row = event.button.parent
            parent_row.remove()

        # lets you delete a k3s-arg row
        if "k3s-arg-del-button" in event.button.classes:
            parent_row = event.button.parent
            parent_row.remove()

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
