from smol_k8s_lab.k8s_tools.backup import create_pvc_restic_backup
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Grid, Container
from textual.validation import Length
from textual.widgets import Input, Label, Static, Switch, Collapsible, Button


class BackupRestoreAppConfig(Static):
    """
    a textual widget for backing up and restoring select apps via k8up
    """

    def __init__(self,
                 app_name: str,
                 restore_params: dict,
                 backup_s3_endpoint: str,
                 backup_bucket: str,
                 id: str) -> None:
        self.app_name = app_name
        self.restore_params = restore_params
        self.cnpg_restore = restore_params.get("cnpg_restore", "not_applicable")
        self.backup_s3_bucket = backup_bucket
        self.backup_s3_endpoint = backup_s3_endpoint
        super().__init__(id=id)

    def compose(self) -> ComposeResult:
        # verify restore is enabled
        restore_enabled = self.restore_params['enabled']

        # restore enabled label
        with Container(classes=f"app-less-switch-row {self.app_name}"):
            init_lbl = Label("Restore from backup", classes="initialization-label")
            init_lbl.tooltip = ("if supported, smol-k8s-lab will perform a "
                                "one-time initial restore of this app's PVCs "
                                "from an s3 endpoint using restic via k8up")
            yield init_lbl

            yield Label("Enabled: ", classes="app-init-switch-label")

            switch = Switch(value=restore_enabled,
                            id=f"{self.app_name}-restore-enabled",
                            name="restore enabled",
                            classes="app-init-switch")
            yield switch

        if self.cnpg_restore != "not_applicable":
            cnpg_row = Container(classes=f"app-less-switch-row {self.app_name}",
                                 id=f"{self.app_name}-restore-cnpg-row")
            if not restore_enabled:
                cnpg_row.display = restore_enabled
            yield cnpg_row

        # Restic snapshot IDs collapsible, that gets hidden if restore
        # is disabled with switch above
        update_grid = Grid(classes="collapsible-updateable-grid",
                           id=f"{self.app_name}-restore-grid")
        collapsible = Collapsible(
                update_grid,
                id=f"{self.app_name}-restore-config-collapsible",
                title="Restic Snapshot IDs",
                classes="collapsible-with-some-room"
                )
        collapsible.display = restore_enabled
        yield collapsible

        with Grid(classes="backup-button-grid"):
            yield Button("💾 Backup Now",
                         classes="backup-button",
                         id=f"{self.app_name}-backup-button")

    def on_mount(self) -> None:
        """
        add tool tip for collapsible and generate all the argocd input rows
        """
        header = self.get_widget_by_id(f"{self.app_name}-restore-config-collapsible")
        header.tooltip = "Configure parameters for a restore from backups."

        # enable or disable cnpg restore if available
        if isinstance(self.cnpg_restore, bool):
            box = self.get_widget_by_id(f"{self.app_name}-restore-cnpg-row")
            init_lbl = Label("Restore CNPG cluster",
                             classes="initialization-label")
            init_lbl.tooltip = (
                    "if supported, smol-k8s-lab will perform a one-time initial"
                    " restore of this app's CNPG cluster from an s3 endpoint using barman"
                    )
            box.mount(init_lbl)
            box.mount(Label("Enabled: ", classes="app-init-switch-label"))
            box.mount(Switch(value=self.cnpg_restore,
                             id=f"{self.app_name}-cnpg-restore-enabled",
                             name="cnpg restore enabled",
                             classes="app-init-switch"))

        if self.restore_params.get("restic_snapshot_ids", None):
            grid = self.get_widget_by_id(f"{self.app_name}-restore-grid")
            self.generate_rows(grid)

    def generate_rows(self, base_grid: Grid) -> None:
        """
        generate each row for the restore widget
        """
        grid = self.get_widget_by_id(f"{self.app_name}-restore-grid")
        # create a label and input row for each argo value, excedpt directory_recursion
        for key, value in self.restore_params["restic_snapshot_ids"].items():
            if not value:
                input_value = "latest"
            else:
                input_value = value

            argo_label = Label(f"{key.replace('_',' ')}:", classes="argo-config-label")
            argo_label.tooltip = value
            if self.app_name in key:
                input_id = f"{key}-restic-snapshot-id"
            else:
                input_id = f"{self.app_name}-{key}-restic-snapshot-id"
            input = Input(placeholder=f"Enter a {key}",
                          value=input_value,
                          name=key,
                          validators=[Length(minimum=3)],
                          id=input_id,
                          classes=f"{self.app_name} argo-config-input")
            input.validate(input_value)

            grid.mount(Horizontal(argo_label, input, classes="argo-config-row"))

    @on(Input.Changed)
    def update_base_yaml_for_input(self, event: Input.Changed) -> None:
        """
        whenever any of our inputs change, we update the base app's saved config.yaml
        """
        input = event.input
        parent_app_yaml = self.app.cfg

        parent_app_yaml['apps'][self.app_name]['init']['restore']['restic_snapshot_ids'][input.name] = input.value

        self.app.write_yaml()

    @on(Switch.Changed)
    def update_base_yaml_for_switch(self, event: Switch.Changed) -> None:
        """
        if user changes the restore enabled value, we write that out
        and we display or hide the restic values based on that
        """
        truthy = event.value

        if event.switch.id == f"{self.app_name}-restore-enabled":
           grid = self.get_widget_by_id(f"{self.app_name}-restore-config-collapsible")
           grid.display = truthy
           restore_row = self.get_widget_by_id(f"{self.app_name}-restore-cnpg-row")
           restore_row.display = truthy

           self.app.cfg['apps'][self.app_name]['init']['restore']['enabled'] = truthy
           self.app.write_yaml()

        if event.switch.id == f"{self.app_name}-cnpg-restore-enabled":
           self.app.cfg['apps'][self.app_name]['init']['restore']['cnpg_restore'] = truthy
           self.app.write_yaml()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        get pressed button and act on it
        """
        id = event.button.id
        if id == f"{self.app_name}-backup-button":
            create_pvc_restic_backup(self.app_name,
                                     bucket=self.backup_s3_bucket,
                                     endpoint=self.backup_s3_endpoint,
                                     cnpg_backup=self.cnpg_restore)
