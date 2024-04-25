from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Grid
from textual.validation import Length
from textual.widgets import Input, Label, Static, Switch, Collapsible


class RestoreAppConfig(Static):
    """
    a textual widget for restoring select apps via k8up
    """
    def __init__(self, app_name: str, restore_params: dict, id: str) -> None:
        self.app_name = app_name
        self.restore_params = restore_params
        super().__init__(id=id)

    def compose(self) -> ComposeResult:
        with Collapsible(collapsed=False,
                         title="Restore Configuration",
                         classes="collapsible-with-some-room",
                         id=f"{self.app_name}-restore-config-collapsible"):
            yield Grid(classes="collapsible-updateable-grid",
                       id=f"{self.app_name}-restore-grid")

    def on_mount(self) -> None:
        """
        add tool tip for collapsible and generate all the argocd input rows
        """
        header = self.get_widget_by_id(f"{self.app_name}-restore-config-collapsible")
        header.tooltip = "Configure parameters for a restore from backups."

        # 'cnpg_restore': 'restore a CNPG postgres cluster from backups'
        # restore enabled is a boolean, so we have a seperate process for it
        enabled_tooltip = 'enable restoring PVCs from restic backups via k8up'
        label = Label("enable restore:", classes="argo-config-label")
        label.tooltip = enabled_tooltip

        switch = Switch(value=self.restore_params['enabled'],
                        classes="argo-switch",
                        name="enabled",
                        id=f"{self.app_name}-restore-enabled")
        switch.tooltip = enabled_tooltip

        grid = self.get_widget_by_id(f"{self.app_name}-restore-grid")
        grid.mount(Horizontal(label, switch, classes="argo-switch-row"))

        if self.restore_params.get("restic_snapshot_ids", None):
            self.generate_rows(grid)

    def generate_rows(self, base_grid: Grid) -> None:
        """
        generate each row for the restore widget
        """
        base_grid.mount(Grid(id=f"{self.app_name}-restic-snapshot-ids"))
        grid = self.get_widget_by_id(f"{self.app_name}-restic-snapshot-ids")
        grid.mount(Label("Restic Snapshot IDs", classes="argo-config-header"))

        # create a label and input row for each argo value, excedpt directory_recursion
        for key, value in self.restore_params["restic_snapshot_ids"].items():
            if not value:
                input_value = "latest"
            else:
                input_value = value

            argo_label = Label(f"{key.replace('_',' ')}:", classes="argo-config-label")
            argo_label.tooltip = value

            input = Input(placeholder=f"Enter a {key}",
                          value=input_value,
                          name=key,
                          validators=[Length(minimum=3)],
                          id=f"{self.app_name}-{key}",
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
           grid = self.get_widget_by_id(f"{self.app_name}-restic-snapshot-ids")
           grid.display = truthy

           self.app.cfg['apps'][self.app_name]['init']['restore']['enabled'] = truthy
           self.app.write_yaml()
