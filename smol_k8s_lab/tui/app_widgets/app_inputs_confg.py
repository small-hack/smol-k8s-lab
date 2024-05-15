# smol-k8s-lab libraries
from smol_k8s_lab.tui.app_widgets.argocd_widgets import (ArgoCDApplicationConfig,
                                                         ArgoCDProjectConfig)
from smol_k8s_lab.tui.app_widgets.input_widgets import SmolK8sLabInputsWidget
from smol_k8s_lab.tui.app_widgets.backup_and_restore import BackupWidget, RestoreApp
from smol_k8s_lab.tui.util import placeholder_grammar, create_sanitized_list

# external libraries
from ruamel.yaml import CommentedSeq
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Grid
from textual.validation import Length
from textual.widgets import (Input, Label, Button, Switch, Static, Collapsible,
                             TabbedContent, TabPane)

RESTOREABLE = ["home_assistant", "matrix", "mastodon", "nextcloud",
               "seaweedfs", "zitadel"]


class AppInputs(Static):
    """
    Display inputs for given smol-k8s-lab supported application
    """
    def __init__(self, app_name: str, config_dict: dict, id: str = "") -> None:
        self.app_name = app_name
        self.argo_params = config_dict['argo']
        self.init = config_dict.get('init', None)
        self.backup_params = config_dict.get('backups', None)
        super().__init__(id=id)

    def compose(self) -> ComposeResult:
        # standard values to source an argo cd app from an external repo
        if self.init:
            if self.init['enabled']:
                initial_tab = "init-tab"
            else:
                initial_tab = "argocd-tab"
            # Add the TabbedContent widget for app config
            with TabbedContent(initial=initial_tab,
                               id="app-config-tabbed-content"):
                # tab 1 - init options
                yield TabPane("Initialization Config", id="init-tab")
                # tab 2 - argo options
                yield TabPane("Argo CD App Config", id="argocd-tab")

                # tab 3,4 - backup/restore options (if we support it for this app)
                if self.app_name in RESTOREABLE:
                    yield TabPane("Backup", id="backup-tab")
                    yield TabPane("Restore", id="restore-tab")

    def on_mount(self) -> None:
        """
        mount either a custom app widget or a default app widget
        """
        secret_keys = self.argo_params.get('secret_keys', False)

        # different process for custom apps that don't support init
        if not self.init:
            self.create_custom_app_widget(secret_keys)
        else:
            self.create_default_app_widget(secret_keys)

    def create_default_app_widget(self, secret_keys: dict|bool):
        """
        using a tabbed content feature, mount the widgets into the tab on mount
        """
        # mount widgets into the init tab pane
        init_pane = self.get_widget_by_id("init-tab")
        init_pane.mount(InitValues(self.app_name, self.init))

        # mount widgets into the argocd tab pane
        argo_pane = self.get_widget_by_id("argocd-tab")
        argo_pane.mount(ArgoCDApplicationConfig(self.app_name,
                                                self.argo_params))
        argo_pane.mount(AppsetSecretValues(self.app_name, secret_keys))
        argo_pane.mount(ArgoCDProjectConfig(self.app_name,
                                            self.argo_params['project']))

        # if we support backups/restorations for this app, mount restore widget
        if self.app_name in RESTOREABLE:
            self.create_backup_and_restore_widgets()

    def create_custom_app_widget(self, secret_keys: dict|bool):
        """
        create a custom app widget for the app-config-pane
        """
        self.mount(ArgoCDApplicationConfig(self.app_name, self.argo_params))
        self.mount(AppsetSecretValues(self.app_name, secret_keys))
        self.mount(ArgoCDProjectConfig(self.app_name,
                                       self.argo_params['project']))

    def create_backup_and_restore_widgets(self):
        restore_params = self.init.get("restore", {"enabled": False})
        # mount the backup wiget into the restore tab
        backup_widget = BackupWidget(
                self.app_name,
                self.backup_params,
                restore_params.get('cnpg_restore', "not_applicable"),
                id=f"{self.app_name}-restore-widget"
                )
        # only display restore widget if init is enabled
        backup_widget.display = self.init["enabled"]
        self.get_widget_by_id("backup-tab").mount(backup_widget)

        # mount the restore wiget into the restore tab
        restore_widget = RestoreApp(
                self.app_name,
                restore_params,
                id=f"{self.app_name}-restore-widget"
                )
        # only display restore widget if init is enabled
        restore_widget.display = self.init["enabled"]
        self.get_widget_by_id("restore-tab").mount(restore_widget)

    def action_show_tab(self, tab: str) -> None:
        """Switch to a new tab."""
        tabbed_content = self.get_widget_by_id("app-config-tabbed-content")
        tabbed_content.show_tab(tab)
        tabbed_content.active = tab


class InitValues(Static):
    """
    widget to take special smol-k8s-lab init and sensitive init values
    """
    CSS_PATH = "../css/apps_init_config.tcss"

    def __init__(self, app_name: str, init_dict: dict) -> None:
        self.app_name = app_name
        self.init_enabled = init_dict['enabled']
        self.init_values = init_dict.get('values', None)

        super().__init__()

    def compose(self) -> ComposeResult:
        # container for all inputs associated with one app
        # make a pretty title with an init switch for the app to configure
        with Container(classes=f"app-init-switch-and-labels-row {self.app_name}"):
            init_lbl = Label("Initialization", classes="initialization-label")
            init_lbl.tooltip = ("if supported, smol-k8s-lab will perform a "
                                "one-time initial setup of this app")
            yield init_lbl

            yield Label("Enabled: ", classes="app-init-switch-label")

            switch = Switch(value=self.init_enabled,
                            id=f"{self.app_name}-init-switch",
                            classes="app-init-switch")
            yield switch

        inputs_container = Container(
                id=f"{self.app_name}-init-inputs",
                classes=f"{self.app_name} init-inputs-container"
                )
        if self.init_values and not self.init_enabled:
            inputs_container.display = False

        if self.init_values:
            with inputs_container:
                cid = f"{self.app_name}"
                if self.init_values:
                    # these are special values that are only set up via
                    # smol-k8s-lab and do not live in a secret on the k8s cluster
                    init_vals =  SmolK8sLabInputsWidget(
                            app_name=self.app_name,
                            title="Init Values",
                            id=f"{cid}-init-values-collapsible",
                            inputs=self.init_values)

                    init_vals.tooltip = (
                                "Init values for special one-time setup of "
                                f"{self.app_name}. These values are [i]not[/i] "
                                "stored in a secret for later reference by Argo CD."
                                )
                    yield init_vals

    @on(Switch.Changed)
    def show_or_hide_init_inputs(self, event: Switch.Changed) -> None:
        """
        if user pressed the init switch, we hide the inputs
        """
        truthy_value = event.value

        if self.init_values and event.switch.id == f"{self.app_name}-init-switch":
           app_init_inputs = self.get_widget_by_id(f"{self.app_name}-init-inputs")
           app_init_inputs.display = truthy_value
           restore_inputs = self.screen.get_widget_by_id(f"{self.app_name}-restore-widget")
           restore_inputs.display = truthy_value

           self.app.cfg['apps'][self.app_name]['init']['enabled'] = truthy_value
           self.app.write_yaml()


class AppsetSecretValues(Static):
    """
    widget to take secret key values to pass to argocd appset secret plugin helm
    chart. These values are saved to the base yaml in:
    self.app.cfg['apps'][app]['secret_keys']
    """
    def __init__(self, app_name: str, secret_keys: dict|bool = False) -> None:
        self.app_name = app_name
        # if not secret keys, make sure we write it to the yaml
        if not secret_keys and isinstance(secret_keys, bool):
            self.app.cfg['apps'][self.app_name]['secret_keys'] = {}
            self.app.write_yaml()
        self.secret_keys = secret_keys
        super().__init__()

    def compose(self) -> ComposeResult:
        with Collapsible(collapsed=False,
                         title="Template values for Argo CD ApplicationSet",
                         classes="collapsible-with-some-room",
                         id=f"{self.app_name}-secret-keys-collapsible"):
            yield Grid(
                    classes="collapsible-updateable-grid",
                    id=f"{self.app_name}-secret-keys-collapsible-updateable-grid"
                    )

    def on_mount(self) -> None:
        """
        generate all the input rows for the each secret value.
        also add tooltip to collapsible
        """
        header = self.get_widget_by_id(f"{self.app_name}-secret-keys-collapsible")
        header.tooltip = ("🔒[i]optional[/]: Added to k8s secret for the Argo CD "
                          "ApplicationSet Secret Plugin Generator.")
        self.generate_initial_rows()

    def generate_initial_rows(self) -> None:
        """
        generate initial secret key input rows
        """
        grid = self.get_widget_by_id(
                f"{self.app_name}-secret-keys-collapsible-updateable-grid"
                )

        # secret keys
        if self.secret_keys:
            # iterate through the app's secret keys
            for secret_key, value in self.secret_keys.items():
                secret_row = self.generate_secret_key_row(secret_key, value)
                grid.mount(secret_row)
        else:
            help = ("smol-k8s-lab doesn't include any templated values for"
                    " this app, but you can add some below if you're using "
                    "a custom Argo CD App repo.")
            grid.mount(Label(help, classes="secret-key-help-text"))

        key_input = Input(placeholder="new key name",
                          id=f"{self.app_name}-new-secret",
                          classes="new-secret-input",
                          validators=Length(minimum=2))

        key_input.tooltip = ("🔒key name to pass to the Argo CD ApplicationSet"
                             " Secret Plugin Generator for templating non-"
                             "sensitive values such as hostnames.")

        button = Button("➕", id=f"{self.app_name}-new-secret-button",
                        classes="new-secret-button")
        grid.mount(Horizontal(button, key_input, classes="app-input-row",
                              id=f"{self.app_name}-new-button-row"))

    def generate_secret_key_row(self, secret_key: str, value: str = "") -> None:
        """
        add a new row of secret keys to pass to the argocd app
        """
        # root app yaml
        apps_yaml = self.app.cfg['apps'][self.app_name]
        apps_yaml['argo']['secret_keys'][secret_key] = value

        key_label = secret_key.replace("_", " ")

        # create input
        input_class = f"app-secret-key-input {self.app_name}"
        input_keys = {"placeholder": placeholder_grammar(key_label),
                      "classes": input_class,
                      "name": secret_key,
                      "validators": [Length(minimum=2)],
                      "id": secret_key}

        if value:
            # handle ruamel commented sequence (dict from yaml with comments)
            if isinstance(value, CommentedSeq) or isinstance(value, list):
                if isinstance(value[0], str):
                    sequence_value = ", ".join(value)

                elif isinstance(value[0], list):
                    # we grab value[0] because ruamel.yaml's CommentedSeq is weird
                    sequence_value = ", ".join(value[0])

                # reassign value if this is a CommentedSeq for validation later on
                value = sequence_value

            input_keys["value"] = value

        input = Input(**input_keys)
        input.validate(value)

        # create the input row
        secret_label = Label(f"{key_label}:",
                             classes=f"input-label {self.app_name}")

        return Horizontal(secret_label, input,
                          classes=f"app-input-row {self.app_name}")

    @on(Input.Changed)
    def update_base_yaml(self, event: Input.Changed) -> None:
        if event.validation_result.is_valid:
            input = event.input
            if input.id != f"{self.app_name}-new-secret":
                if "," in input.value:
                    value = create_sanitized_list(input.value)
                else:
                    value = input.value

                parent_app_yaml = self.app.cfg['apps'][self.app_name]
                parent_app_yaml['argo']['secret_keys'][input.name] = value

                self.app.write_yaml()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        add a new input row for secret stuff
        """
        grid = self.get_widget_by_id(
                f"{self.app_name}-secret-keys-collapsible-updateable-grid"
                )
        input = self.get_widget_by_id(f"{self.app_name}-new-secret")

        if len(input.value) > 1:
            # add new secret key row
            grid.mount(
                    self.generate_secret_key_row(input.value),
                    before=self.get_widget_by_id(f"{self.app_name}-new-button-row")
                    )
            # clear the input field after we're created the new row and
            # updated the yaml
            input.value = ""
