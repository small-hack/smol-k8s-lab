#!/usr/bin/env python3.11
from textual import on
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Container, Horizontal
from textual.binding import Binding
from textual.events import Mount
from textual.widgets import (Button, Footer, Header, Input, Label,
                             Select, SelectionList, Static, TabbedContent,
                             TabPane)
from textual.widgets._toggle_button import ToggleButton
from textual.widgets.selection_list import Selection
from smol_k8s_lab.constants import (DEFAULT_APPS, DEFAULT_DISTRO,
                                    DEFAULT_DISTRO_OPTIONS, DEFAULT_CONFIG)
from smol_k8s_lab.utils.tui.help_screen import HelpScreen
from smol_k8s_lab.utils.tui.app_config_pane import ArgoCDAppInputs


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
                select_prompt = ("[magenta]Select Kubernetes distro from this "
                                 f"dropdown (default: {DEFAULT_DISTRO})")
                # create all the select choices
                my_options = tuple(DEFAULT_DISTRO_OPTIONS.keys())
                yield Select(((line, line) for line in my_options),
                             prompt=select_prompt,
                             id="distro-drop-down", allow_blank=False)

                for distro, distro_metadata in DEFAULT_DISTRO_OPTIONS.items():
                    if distro == DEFAULT_DISTRO:
                        display = True
                    else:
                        display = False

                    # node input row
                    node_class = f"{distro} nodes-input"
                    node_row = Horizontal(classes=f"{node_class}-row")
                    node_row.display = display
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

                    # kubelet config section
                    kubelet_container = Container(classes="kubelet-config-container")
                    kubelet_container.display = display
                    with kubelet_container:
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
                                    yield Button("🚮",
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
                                        yield Button("🚮",
                                                     classes=f"{k3s_class}-del-button")

                            yield Button("➕ Add New Arg",
                                         classes=f"{k3s_class}-add-button")

                with Container(id="k8s-distro-description-container"):
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
                    yield ArgoCDAppInputs()

                    with VerticalScroll(id="app-description-container"):
                        # Bottom half of the screen for select-apps TabPane()
                        yield Label("", id="app-description")

                        yield Label("[white]Argo CD App Repo[/]", id="app-repo-label")
                        yield Label("", id="app-repo")

    def action_show_tab(self, tab: str) -> None:
        """Switch to a new tab."""
        self.get_child_by_type(TabbedContent).active = tab

    def on_mount(self) -> None:
        # screen and header styling
        self.title = "ʕ ᵔᴥᵔʔ smol k8s lab"
        self.sub_title = "now with more 🦑"

        kubelet_title = "➕ [green]Extra Args for Kubelet Config"
        kubelet_containers = self.query(".kubelet-config-container")
        for container in kubelet_containers:
            container.border_title = kubelet_title

        node_rows = self.query("nodes-input-row")
        for row in node_rows:
            row.border_title = "Adjust how many of each node type to deploy"

        # styling for the select-apps tab - select apps container - left
        select_apps_title = "[green]Select apps"
        self.query_one(SelectionList).border_title = select_apps_title

        # styling for the select-distro tab - middle
        distro_desc = self.get_widget_by_id("k8s-distro-description-container")
        distro_desc.border_title = "[white]Distro Description[/]"

        app_desc = self.get_widget_by_id("app-description-container")
        app_desc.border_title = "[white]App Description[/]"

    # @on(Mount)
    # @on(SelectionList.SelectedChanged)
    # @on(TabbedContent.TabActivated)
    # def update_configure_apps_view(self) -> None:
    #     # get the last item in the list selected items
    #     selected_items = self.query_one(SelectionList).selected

    #     # for each application in DEFAULT_APPS
    #     for application in DEFAULT_APPS.keys():
    #         # get any objects using this application's name as their class
    #         app_class_objects = self.query(f".{application}")

    #         # if the application is in the selected items, set enabled to True
    #         if application in selected_items:
    #             enabled = True
    #         else:
    #             enabled = False

    #         # set the DEFAULT_APPS
    #         DEFAULT_APPS[application]['enabled'] = enabled
    #         if app_class_objects:
    #             for app_obj in app_class_objects:
    #                 app_obj.display = enabled

    @on(Mount)
    @on(SelectionList.SelectedChanged)
    @on(TabbedContent.TabActivated)
    @on(SelectionList.SelectionHighlighted)
    def update_selected_app_blurb(self) -> None:
        selection_list = self.query_one(SelectionList)

        # only the highlighted index
        highlighted_idx = selection_list.highlighted

        # the actual highlighted app
        highlighted_app = selection_list.get_option_at_index(highlighted_idx).value

        new_repo, new_blurb = generate_description(highlighted_app)

        # update the static text with the new app description and repo
        self.get_widget_by_id('app-repo').update(new_repo)
        self.get_widget_by_id('app-description').update(new_blurb)

        # for each application in DEFAULT_APPS
        for application in DEFAULT_APPS.keys():
            if application == highlighted_app:
                display = True
            else:
                display = False
            app_class_objects = self.query(f".{application}")
            if app_class_objects:
                for app_obj in app_class_objects:
                    app_obj.display = display

    @on(TabbedContent.TabActivated)
    def show_or_hide_init_inputs_on_new_tab(self,) -> None:
        switches = self.query(".app-init-switch")
        for switch in switches:
            app = switch.id.split("-init-switch")[0]
            if DEFAULT_APPS[app].get('init', None):
                if DEFAULT_APPS[app]['argo'].get('secret_keys', None):
                    app_inputs = self.get_widget_by_id(f"{app}-inputs")
                    app_inputs.display = switch.value

    @on(Select.Changed)
    def update_k8s_distro_description(self, event: Select.Changed) -> None:
        """
        change the description text in the bottom box for k8s distros
        """
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
        button_classes = event.button.classes

        # lets you delete a kubelet-arg row
        if "kubelet-arg-del-button" in button_classes:
            parent_row = event.button.parent
            parent_row.remove()

        if "kubelet-arg-add-button" in button_classes:
            parent_container = event.button.parent
            row_class = "kind kubelet-arg"

            # add a new row of kubelet arg inputs before the add button
            parent_container.mount(Horizontal(
                             Input(placeholder="optional kubelet config key arg",
                                   classes=f"{row_class}-input-key"),
                             Input(placeholder="optional kubelet config key arg",
                                   classes=f"{row_class}-input-value"),
                             Button("🚮", classes=f"{row_class}-del-button"),
                             classes=f"{row_class}-input-row"
                             ), before=event.button)

        # lets you delete a k3s-arg row
        if "k3s-arg-del-button" in button_classes:
            parent_row = event.button.parent
            parent_row.remove()

        # lets you add a new k3s config row
        if "k3s-arg-add-button" in button_classes:
            parent_container = event.button.parent
            placeholder = "enter an extra arg for k3s"
            parent_container.mount(Horizontal(
                Input(placeholder=placeholder, classes="k3s-arg-input"),
                Button("🚮", classes="k3s-arg-del-button"),
                classes="k3s-arg-row"
                ), before=event.button)

    def action_request_help(self) -> None:
        """
        if the user presses 'h' or '?', show the help modal screen
        """
        self.push_screen(HelpScreen())


def generate_description(app_name: str):
    """
    generate description like:
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
