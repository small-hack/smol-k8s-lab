# smol-k8s-lab libraries
from smol_k8s_lab.constants import INITIAL_USR_CONFIG, XDG_CONFIG_FILE
from smol_k8s_lab.k8s_distros import check_all_contexts
from smol_k8s_lab.tui.apps_screen import AppsConfig
from smol_k8s_lab.tui.base_cluster_modal import ClusterModalScreen
from smol_k8s_lab.tui.confirm_screen import ConfirmConfig
from smol_k8s_lab.tui.distro_screen import DistroConfigScreen
from smol_k8s_lab.tui.help_screen import HelpScreen
from smol_k8s_lab.tui.app_widgets.invalid_apps import InvalidAppsScreen
from smol_k8s_lab.tui.smol_k8s_config_screen import SmolK8sLabConfig
from smol_k8s_lab.tui.tui_config_screen import TuiConfigScreen
from smol_k8s_lab.tui.validators.already_exists import CheckIfNameAlreadyInUse

# external libraries
from os import environ, system
from pyfiglet import Figlet
import random
from rich.text import Text
from ruamel.yaml import YAML
from textual import on
from textual.app import App, ComposeResult
from textual.events import DescendantFocus
from textual.binding import Binding
from textual.containers import Grid
from textual.validation import Length
from textual.widgets import (Footer, Button, DataTable, Input, Static, Label,
                             Switch, Select, _collapsible)

# list of approved words for nouns
CUTE_NOUNS = [
        "bunny", "hoglet", "puppy", "kitten", "knuffel", "friend", "egel",
        "meerkoet", "raccoon", "wasbeertje"
        ]

CUTE_ADJECTIVE = [
        "lovely", "adorable", "cute", "friendly", "nice", "leuke", "mooie", 
        "vriendelijke", "cool", "soft", "smol", "small", "klein"
        ]

class BaseApp(App):
    BINDINGS = [
            Binding(key="?,h",
                    key_display="?",
                    action="request_help",
                    description="Help",
                    show=True),
            Binding(key="c",
                    key_display="c",
                    action="request_config",
                    description="Config"),
            Binding(key="f",
                    key_display="f",
                    action="toggle_footer",
                    description="Toggle footer"),
            Binding(key="q,escape",
                    action="quit",
                    show=False),
            Binding(key="f5",
                    key_display="f5",
                    description="Speak",
                    action="app.say",
                    show=True),
            Binding(key="n",
                    key_display="n",
                    description="New Cluster",
                    action="app.new_cluster",
                    show=True)
            ]

    CSS_PATH = ["./css/base.tcss",
                "./css/help.tcss"]

    def __init__(self, user_config: dict = INITIAL_USR_CONFIG) -> None:
        self.cfg = user_config
        self.show_footer = self.cfg['smol_k8s_lab']['tui']['show_footer']
        self.cluster_names = []
        self.current_cluster = ""
        self.sensitive_values = {
                'nextcloud': {},
                'matrix': {},
                'mastodon': {},
                'zitadel': {}
                }

        # configure global accessibility
        accessibility_opts = self.cfg['smol_k8s_lab']['tui']['accessibility']
        tts = accessibility_opts['text_to_speech']
        self.speak_on_focus = tts['on_focus']
        self.speak_screen_titles = tts['screen_titles']
        self.speak_on_key_press = tts['on_key_press']
        self.speech_program = tts['speech_program']
        self.bell_on_focus = accessibility_opts['bell']['on_focus']
        self.bell_on_error = accessibility_opts['bell']['on_error']
        super().__init__()

    def compose(self) -> ComposeResult:
        """
        Compose app with screens
        """
        # Footer to show keys
        footer = Footer()

        if not self.show_footer:
            footer.display = False
        yield footer

        # full screen container
        with Grid(id="base-screen-container"):
            yield Label(Figlet(font="standard").renderText("smol-k8s-lab"),
                        id="smol-k8s-lab-header")

            with Grid(id="cluster-boxes"):
                # the actual little box in the middle of screen
                with Grid(id="base-new-cluster-input-box-grid"):
                    # container for new cluster buton
                    with Grid(id="cluster-input-row"):
                        yield NewClusterInput()

    def on_mount(self) -> None:
        """
        screen and box border styling
        """
        # main box title
        title = "[#ffaff9]Create[/] a [i]new[/] [#C1FF87]cluster[/] with the name below"
        self.get_widget_by_id("base-new-cluster-input-box-grid").border_title = title

        # get all clusters
        clusters = check_all_contexts()

        if clusters:
            self.generate_cluster_table(clusters)
            if self.speak_screen_titles:
                self.action_say("Welcome to smol-k8s-lab. Press c to configure "
                                "accessibility options.")
        else:
            self.get_widget_by_id("base-screen-container").add_class("no-cluster-table")
            if self.speak_screen_titles:
                self.action_say("Welcome to smol-k8s-lab. Press tab, then C, to configure "
                                "accessibility options.")


    def generate_cluster_table(self, clusters: list) -> None:
        """ 
        generate a readable table for all the clusters.

        Each row is has a height of 3 and is centered to make it easier to read
        for people with dyslexia
        """
        data_table = DataTable(zebra_stripes=True,
                               id="clusters-data-table",
                               cursor_type="row")

        # then fill in the cluster table
        data_table.add_column(Text("Cluster", justify="center"))
        data_table.add_column(Text("Distro", justify="center"))

        for row in clusters:
            # we use an extra line to center the rows vertically 
            styled_row = [Text(str("\n" + cell), justify="center") for cell in row]

            # we add extra height to make the rows more readable
            data_table.add_row(*styled_row, height=3, key=row[0])

            self.cluster_names.append(row[0])

        # grid for the cluster data table
        table_grid = Grid(data_table,
                          id="table-grid")

        # the actual little box in the middle of screen
        main_grid = Grid(table_grid, id="base-cluster-table-box-grid")

        # modify clusters box title
        main_grid.border_title = ("Select a row to [#ffaff9]modify[/] or [#ffaff9]"
                                  "delete[/] an [i]existing[/] [#C1FF87]cluster[/]")

        cluster_container = self.get_widget_by_id("cluster-boxes")
        self.get_widget_by_id("base-screen-container").add_class("with-cluster-table")
        cluster_container.mount(main_grid, before="#base-new-cluster-input-box-grid")


    @on(DataTable.RowSelected)
    def cluster_row_selected(self, event: DataTable.RowSelected) -> None:
        """
        check which row was selected to launch a modal screen
        """
        if event.data_table.id == "clusters-data-table":
            def check_if_cluster_deleted(response: list = []):
                """
                check if cluster has been deleted
                """
                cluster = response[0]
                row_key = response[1]

                # make sure we actually got anything, because the user may have hit
                # the cancel button
                if cluster and row_key:
                    data_table = self.query_one(DataTable)
                    data_table.remove_row(row_key)

                    self.cluster_names.remove(cluster)
                    self.current_cluster = ""

                    if data_table.row_count < 1:
                        self.get_widget_by_id("base-cluster-table-box-grid").remove()
                        screen = self.get_widget_by_id("base-screen-container")
                        screen.remove_class("with-cluster-table")
                        screen.add_class("no-cluster-table")
            row_index = event.cursor_row
            row = event.data_table.get_row_at(row_index)

            # get the row's first column (the name of the cluster) and remove whitespace
            cluster_name = row[0].plain.strip()
            distro = row[1].plain.strip()

            # set the current cluster name to return after we've done modifications
            self.current_cluster = cluster_name

            # launch modal UI to ask if they'd like to modify or delete a cluster
            self.app.push_screen(ClusterModalScreen(cluster_name,
                                                    distro,
                                                    event.row_key),
                                 check_if_cluster_deleted)

    @on(DataTable.RowHighlighted)
    def cluster_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """
        check which row was selected to launch a modal screen
        """
        if self.app.speak_on_focus:
            self.say_row(event.data_table)

    def action_new_cluster(self):
        """
        press button for new cluster
        """
        new_cluster_button = self.get_widget_by_id("new-cluster-button")
        if not new_cluster_button.disabled:
            new_cluster_button.action_press()

    def action_request_apps_cfg(self, app_to_highlight: str = "") -> None:
        """
        launches the argo app config screen
        """
        if app_to_highlight:
            self.app.push_screen(AppsConfig(self.cfg['apps'], app_to_highlight))
        else:
            self.app.push_screen(AppsConfig(self.cfg['apps'], ""))

    def action_request_distro_cfg(self) -> None:
        """
        launches the k8s distro (k3s,k3d,kind) config screen
        """
        self.app.push_screen(DistroConfigScreen(self.cfg['k8s_distros']))

    def action_request_smol_k8s_cfg(self) -> None:
        """
        launches the smol-k8s-lab config for the program itself for things like
        the TUI, but also logging and password management
        """
        # go check all the apps for empty inputs
        invalid_apps = self.check_for_invalid_inputs(self.cfg['apps'])

        if invalid_apps:
            self.app.push_screen(InvalidAppsScreen(invalid_apps))
        else:
            self.app.push_screen(SmolK8sLabConfig(self.cfg['smol_k8s_lab']))

    def action_request_confirm(self) -> None:
        """
        show confirmation screen
        """
        self.app.push_screen(ConfirmConfig(self.cfg))

    def action_request_help(self,) -> None:
        """
        if the user presses 'h' or '?', show the help modal screen
        """
        self.push_screen(HelpScreen())

    def action_request_config(self,) -> None:
        """ 
        if the user pressed 'c', show the TUI config screen
        """
        self.push_screen(TuiConfigScreen(self.cfg['smol_k8s_lab']['tui']))

    def action_toggle_footer(self) -> None:
        """
        don't display the footer, or do 🤷
        """
        footer = self.query_one(Footer)

        if footer.display:
            footer.display = False
            self.notify(
                "\n✨ Press [gold3]f[/] to re-enable the footer",
                timeout=9,
                title="Footer disabled"
            )
            self.cfg['smol_k8s_lab']['tui']['show_footer'] = False
        else:
            footer.display = True
            self.cfg['smol_k8s_lab']['tui']['show_footer'] = True

    def write_yaml(self, config_file: str = XDG_CONFIG_FILE) -> None:
        """
        dump current self.cfg to user's smol-k8s-lab config.yaml
        """
        yaml = YAML()

        with open(config_file, 'w') as smol_k8s_config:
            yaml.dump(self.cfg, smol_k8s_config)

    def action_say(self, text_for_speech: str = "") -> None:
        """ 
        Use the configured speech program to read a string aloud. If no string
        is passed in, and self.speak_on_key_press is True, we read the currently
        focused element id
        """
        say = self.speech_program
        if text_for_speech:
            text_for_speech = text_for_speech.replace("(", "").replace(")", "")
            text_for_speech = text_for_speech.replace("[i]", "").replace("[/]", "")
            system(f"{say} {text_for_speech}")

        elif not text_for_speech:
            # if the use pressed f5, the key to read the widget id aloud
            if self.speak_on_key_press:
                focused = self.app.focused
                if isinstance(focused, _collapsible.CollapsibleTitle):
                    system(f"{say} element is a Collapsible called {focused.label}.")
                else:
                    system(f"{say} element is {focused.id}")

                # if it's a data table, read out the row content
                if isinstance(focused, DataTable):
                    self.say_row(focused)

    def say_row(self, data_table: DataTable) -> None:
        """
        get the column names and row content of a DataTable and read aloud
        """
        row_index = data_table.cursor_row
        row = data_table.get_row_at(row_index)
        # get the row's first column and remove whitespace
        row_column1 = row[0].plain.strip()
        # change ? to question mark so it reads aloud well
        if row_column1 == "?":
            row_column1 = "question mark"
        row_column2 = row[1].plain.strip()

        # get the column names
        columns = list(data_table.columns.values())
        column1 = columns[0].label
        column2 = columns[1].label

        system(f"{self.speech_program} Selected {column1}: {row_column1}."
               f" {column2}: {row_column2}")

    @on(DescendantFocus)
    def on_focus(self, event: DescendantFocus) -> None:
        """ 
        on focus, say the id of each element and the value or label if possible
        """
        if self.speak_on_focus:
            id = event.widget.id
            self.action_say(f"element is {id}")

            # input fields
            if isinstance(event.widget, Input):
                content = event.widget.value
                placeholder = event.widget.placeholder
                if content:
                    self.action_say(f"value is {content}")
                elif placeholder:
                    self.action_say(f"place holder text is {placeholder}")

            # buttons
            elif isinstance(event.widget, Button):
                self.action_say(f"button text is {event.widget.label}")

            # switches
            elif isinstance(event.widget, Switch) or isinstance(event.widget, Select):
                self.action_say(f"value is {event.widget.value}")

            # also read the tooltip if there is one
            tooltip = event.widget.tooltip
            if tooltip:
                self.action_say(f"tooltip is {tooltip}")

        if self.bell_on_focus:
            self.app.bell()

    def check_for_invalid_inputs(self, apps_dict: dict = {}) -> list:
        """
        check each app for any empty init or secret key fields
        """
        invalid_apps = {}

        if apps_dict:
            for app, metadata in apps_dict.items():
                if not metadata['enabled']:
                    continue

                empty_fields = []

                # check for empty init fields (some apps don't support init at all)
                init_dict = metadata.get('init', None)
                if init_dict:
                    # make sure init is enabled before checking
                    if init_dict['enabled']:
                        # regular yaml inputs
                        init_values = init_dict.get('values', None)
                        if init_values:
                            for key, value in init_values.items():
                                if not value:
                                    empty_fields.append(key)

                        # sensitive inputs
                        init_sensitive_values = init_dict.get('sensitive_values', None)
                        if init_sensitive_values:
                            prompts = self.check_for_env_vars(app, metadata)
                            if prompts:
                                for value in prompts:
                                    if not self.sensitive_values[app].get(value, ""):
                                        empty_fields.append(value)

                # check for empty secret key fields (some apps don't have secret keys)
                secret_keys = metadata['argo'].get('secret_keys', None)
                if secret_keys:
                    for key, value in secret_keys.items():
                        if not value:
                            empty_fields.append(key)

                if empty_fields:
                    invalid_apps[app] = empty_fields

        return invalid_apps

    def check_for_env_vars(self, app: str, app_cfg: dict = {}) -> list:
        """
        check for required env vars and return list of dict and set:
            values found dict, set of values you need to prompt for
        """
        # keep track of a list of stuff to prompt for
        prompt_values = []

        env_vars = app_cfg['init']['sensitive_values']

        # provided there's actually any env vars to go get...
        if env_vars:
            # iterate through list of env vars to check
            for item in env_vars:
                # check env and self.sensitive_values
                value = environ.get(
                        "_".join([app.upper(), item]),
                        default=self.sensitive_values[app].get(item.lower(), ""))

                if not value:
                    # append any missing values to prompt_values
                    prompt_values.append(item.lower())

                self.sensitive_values[app][item.lower()] = value

        return set(prompt_values)


class NewClusterInput(Static):
    """ 
    small widget with an input and button that takes the names of a cluster,
    and changes the 
    """
    def compose(self) -> ComposeResult:
        with Grid(id="new-cluster-button-container"):
            input = Input(validators=[
                              Length(minimum=2),
                              CheckIfNameAlreadyInUse(self.app.cluster_names)
                              ],
                          placeholder="Name of your new cluster",
                          id="cluster-name-input")
            input.tooltip = ("Name of your ✨ [i]new[/] cluster. Note: The k8s distro"
                             " (selected on the next screen) will be pre-pended to the "
                             "name of the cluster by default.")
            yield input

            new_button = Button("✨ New Cluster", id="new-cluster-button")
            new_button.tooltip = "Add a new cluster managed by smol-k8s-lab"
            yield new_button

    def on_mount(self) -> None:
        input = self.get_widget_by_id("cluster-name-input")
        input.value = random.choice(CUTE_ADJECTIVE) + '-' + random.choice(CUTE_NOUNS)

    @on(Input.Changed)
    @on(Input.Submitted)
    def input_validation(self, event: Input.Changed | Input.Submitted) -> None:
        """ 
        Takes events matching Input.Changed and Input.Submitted events, and
        checks if input is valid. If the user presses enter (Input.Submitted),
        and the input is valid, we also press the button for them.
        """
        new_cluster_button = self.get_widget_by_id("new-cluster-button")

        if event.validation_result.is_valid:
            # if result is valid, enable the submit button
            new_cluster_button.disabled = False

            # if the user pressed enter, we also press the submit button ✨
            if isinstance(event, Input.Submitted):
                new_cluster_button.action_press()
        else:
            # if result is not valid, notify the user why
            self.notify("\n".join(event.validation_result.failure_descriptions),
                        timeout=8,
                        severity="warning",
                        title="⚠️ Input Validation Error\n")

            # and disable the submit button
            new_cluster_button.disabled = True

    @on(Button.Pressed)
    def button_pressed(self, event: Button.Pressed) -> None:
        """
        get pressed button (Button.Pressed event) and change current screen to
        the k8s distro config screen
        """
        self.app.current_cluster = self.get_widget_by_id("cluster-name-input").value
        self.app.action_request_distro_cfg()


if __name__ == "__main__":
    app = BaseApp()
    app.run()
