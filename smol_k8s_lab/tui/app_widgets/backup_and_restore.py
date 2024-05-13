from smol_k8s_lab.k8s_tools.backup import create_pvc_restic_backup
from smol_k8s_lab.utils.value_from import extract_secret
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Grid, Container
from textual.validation import Length
from textual.widgets import Input, Label, Static, Switch, Collapsible, Button, LoadingIndicator
from textual.worker import get_current_worker


class BackupWidget(Static):
    """
    a textual widget for backing up select apps via k8up
    """

    def __init__(self,
                 app_name: str,
                 backup_params: dict,
                 cnpg_restore: bool,
                 id: str) -> None:
        self.app_name = app_name
        self.backup_params = backup_params
        self.cnpg_restore = cnpg_restore
        self.backup_s3_bucket = backup_params['s3']['bucket']
        self.backup_s3_endpoint = backup_params['s3']['endpoint']
        super().__init__(id=id)

    def compose(self) -> ComposeResult:
        """
        compose grid skelleton for backup widget
        """
        if self.screen.modify_cluster:
            # first the grid for the backup button if this is an existing cluster
            yield Grid(classes="backup-button-grid",
                       id=f"{self.app_name}-backup-button-grid")

        # second put in the schedule row
        yield Label("📆 Scheduled backups", classes="header-row")
        yield Grid(id=f"{self.app_name}-backup-schedules-grid",
                   classes="backups-grid")

        # third: add Collapsible with grid for remote s3 backup values
        yield Collapsible(
                Grid(classes="collapsible-updateable-grid",
                     id=f"{self.app_name}-backup-grid"),
                id=f"{self.app_name}-s3-config-collapsible",
                title="S3 Configuration",
                classes="collapsible-with-some-room",
                collapsed=False
                )

        # fourth put in the restic password row
        yield Label("🔒Backup Encryption", classes="header-row")
        yield Horizontal(id=f"{self.app_name}-repo-password", classes="argo-config-row")


    def on_mount(self) -> None:
        """
        add button and generate all the backup option input rows
        """
        if self.screen.modify_cluster:
            button = Button("💾 Backup Now",
                            classes="backup-button",
                            id=f"{self.app_name}-backup-button")
            if not self.cnpg_restore or self.cnpg_restore == "not_applicable":
                button.tooltip = (
                        "Press to perform a one-time backup of "
                        f"[i]{self.app_name}[/i]'s PVC(s) via restic to the s3 "
                        "endpoint you've configured below"
                        )
            else:
                button.tooltip = (
                        f"Press to perform a one-time backup of {self.app_name}'s"
                        " CNPG postgres database with [b]barman[/b], as well as a "
                        f"backup of {self.app_name}'s PVC(s) via [b]restic[/] to the"
                        " s3 endpoint you've configured below"
                        )
            grid = self.get_widget_by_id(f"{self.app_name}-backup-button-grid")
            grid.mount(button)
            loader = LoadingIndicator(id=f"{self.app_name}-backup-running")
            loader.tooltip = "A backup is running. We'll notify you when it's completed."
            loader.display = False
            grid.mount(loader)

        self.add_schedule_rows()

        self.generate_s3_rows()

        repo_grid = self.get_widget_by_id(f"{self.app_name}-repo-password")
        # finally we need the restic repository password
        repo_pw_labl = Label("restic repo password:", classes="argo-config-label")
        repo_pw_labl.tooltip = "restic repository password for encrypting your backups"
        input_id = f"{self.app_name}-restic-repository-password"
        input_val = extract_secret(self.backup_params.get('restic_repo_password', ''))

        repo_pw_input = Input(
                placeholder="Enter a restic repo password for your encrypted backups",
                value=input_val,
                name="restic_repo_password",
                validators=[Length(minimum=5)],
                id=input_id,
                password=True,
                classes=f"{self.app_name} argo-config-input"
                )
        repo_pw_input.validate(input_val)
        repo_grid.mount(repo_pw_labl)
        repo_grid.mount(repo_pw_input)

    def add_schedule_rows(self) -> None:
        """
        add schedule input rows for pvc and postgres backups
        """
        # first put in the PVC schedule
        b_grid = self.get_widget_by_id(id=f"{self.app_name}-backup-schedules-grid")
        argo_label = Label("📁 PVC schedule:", classes="argo-config-label")
        input_id = f"{self.app_name}-pvc-backup-schedule"
        schedule_val = self.backup_params.get('pvc_schedule', "10 0 * * *")
        input = Input(placeholder="Enter a cron syntax schedule for backups.",
                      value=schedule_val,
                      name='pvc_schedule',
                      validators=[Length(minimum=5)],
                      id=input_id,
                      classes=f"{self.app_name} argo-config-input")
        input.validate(schedule_val)
        tip = ("Cron syntax schedule for recurring backup. If you're new to"
               " cron sytax, check out crontab.guru. Must be at least 7 minutes "
               "after postgres backup. Defaults to '10 0 * * *' which is ten "
               "minutes after midnight.")
        argo_label.tooltip = tip
        input.tooltip = tip
        b_grid.mount(Horizontal(argo_label, input,
                                id=f"{self.app_name}-pvc-schedule",
                                classes="argo-config-row"))

        # then put in the postgres schedule, if it's enabled
        if self.cnpg_restore != "not_applicable":
            argo_label = Label("🐘 DB schedule:", classes="argo-config-label")
            input_id = f"{self.app_name}-postgres-backup-schedule"
            schedule_val = self.backup_params.get('postgres_schedule', "0 0 0 * * *")
            input = Input(placeholder="Enter a cron syntax schedule for postgres database backups.",
                          value=schedule_val,
                          name='postgres_schedule',
                          validators=[Length(minimum=5)],
                          id=input_id,
                          classes=f"{self.app_name} argo-config-input")
            input.validate(schedule_val)
            tip = ("Schedule for recurring postgresql backup that includes a seconds field."
                   " This backup must be at least 7 minutes before the PVC backup."
                   " Defaults to '0 0 0 * * *' which runs when the clock strikes"
                   " midnight. 🎃")
            argo_label.tooltip = tip
            input.tooltip = tip
            b_grid.mount(Horizontal(argo_label, input,
                                    id=f"{self.app_name}-postgres-schedule",
                                    classes="argo-config-row"))

    def generate_s3_rows(self) -> None:
        """
        generate each row for the backup widget
        """
        grid = self.get_widget_by_id(f"{self.app_name}-backup-grid")

        # create a label and input row for each argo value, excedpt directory_recursion
        for key, value in self.backup_params['s3'].items():
            argo_label = Label(f"{key.replace('_',' ')}:",
                               classes="argo-config-label")
            argo_label.tooltip = f"{key} for backups to S3"
            input_id = f"{self.app_name}-backup-s3-{key}"
            if isinstance(value, str):
                input_val = value
                sensitive = False
            else:
                sensitive = True
                input_val = extract_secret(value)

            input = Input(placeholder=f"Enter a {key}",
                          value=input_val,
                          name=key,
                          validators=[Length(minimum=3)],
                          id=input_id,
                          password=sensitive,
                          classes=f"{self.app_name} argo-config-input")
            input.validate(input_val)

            grid.mount(Horizontal(argo_label, input, classes="argo-config-row"))

    @on(Input.Changed)
    def update_base_yaml_for_input(self, event: Input.Changed) -> None:
        """
        whenever any of our inputs change, we update the base app's saved config.yaml
        """
        input = event.input
        sensitive = input.password
        if not sensitive:
            if "s3" in input.id:
                self.app.cfg['apps'][self.app_name]['backups']['s3'][input.name] = input.value
            else:
                self.app.cfg['apps'][self.app_name]['backups'][input.name] = input.value
            self.app.write_yaml()
        else:
            self.log(f"saving special value for {input.name} to screen cache")
            self.screen.sensitive_values[self.app_name][input.name] = input.value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        get pressed button and act on it
        """
        id = event.button.id
        if id == f"{self.app_name}-backup-button":
            self.trigger_backup()
            event.button.display = False
            self.get_widget_by_id(f"{self.app_name}-backup-running").display = True
            self.app.notify(
                    "\nYour backup has been kicked off as a background job. "
                    "We'll notify you when it's done 👍",
                    title=f"💾 Backup of {self.app_name} started",
                    timeout=10)

    @work(thread=True, group="backup-worker")
    def trigger_backup(self) -> None:
        """
        run backup of an app in a thread so we don't lock up the UI
        """
        namespace = self.screen.cfg[self.app_name]['argo']['namespace']

        self.log(
                f"💾 kicking off backup for {self.app_name} in the {namespace}"
                f" namespace to the bucket: {self.backup_s3_bucket} at the "
                f" endpoint: {self.backup_s3_endpoint}."
                )
        worker = get_current_worker()
        if not worker.is_cancelled:
            if self.cnpg_restore == "not_applicable":
                cnpg_backup = False
                cnpg_endpoint = ""
            else:
                cnpg_backup = self.cnpg_restore
                cnpg_endpoint = self.screen.cfg[self.app_name]['argo']['secret_keys']['s3_endpoint']
            create_pvc_restic_backup(app=self.app_name,
                                     namespace=namespace,
                                     endpoint=self.backup_s3_endpoint,
                                     bucket=self.backup_s3_bucket,
                                     cnpg_backup=cnpg_backup,
                                     cnpg_s3_endpoint=cnpg_endpoint,
                                     quiet=True)
            self.get_widget_by_id(f"{self.app_name}-backup-button").display = True
            self.get_widget_by_id(f"{self.app_name}-backup-running").display = False
            self.app.notify("\nSuccessfully backed up! 🎉",
                            title=f"💾 backup of {self.app_name} completed",
                            timeout=10)


class RestoreApp(Static):
    """
    a textual widget for restoring select apps via k8up
    """

    def __init__(self, app_name: str, restore_params: dict, id: str) -> None:
        self.app_name = app_name
        self.restore_enabled = restore_params.get('enabled', False)
        self.snapshots = restore_params.get('restic_snapshot_ids', {})
        self.cnpg_restore = restore_params.get("cnpg_restore", "not_applicable")
        super().__init__(id=id)

    def compose(self) -> ComposeResult:
        # verify restore is enabled

        # restore enabled label switch row
        with Container(classes=f"app-less-switch-row {self.app_name}"):
            # left hand side: base label with tool tip
            init_lbl = Label("Restore from backup", classes="initialization-label")
            init_lbl.tooltip = (
                "If enabled, smol-k8s-lab will [#ffaff9]restore[/#ffaff9] "
                f"{self.app_name}'s PVCs from an [b]s3[/b] compatible endpoint "
                "using [b]restic[/b] via [b]k8up[/b]. (Optionally, we can also "
                "restore a CNPG cluster)")
            yield init_lbl

            # right hand side: Enabled label and switch
            yield Label("Enabled: ", classes="app-init-switch-label")
            switch = Switch(value=self.restore_enabled,
                            id=f"{self.app_name}-restore-enabled",
                            name="restore enabled",
                            classes="app-init-switch")
            yield switch

        # cnpg operator restore enabled switch row
        if self.cnpg_restore != "not_applicable":
            cnpg_row = Container(classes=f"app-less-switch-row {self.app_name}",
                                 id=f"{self.app_name}-restore-cnpg-row")
            if not self.restore_enabled:
                cnpg_row.display = self.restore_enabled
            yield cnpg_row

        # Restic snapshot IDs collapsible, that gets hidden if restore
        # is disabled with switch above
        label = Label("Restic Snapshot IDs", classes="header-row",
                      id=f"{self.app_name}-snapshots-header")
        snaphots_grid = Grid(classes="collapsible-updateable-grid",
                             id=f"{self.app_name}-restore-grid")
        label.display = self.restore_enabled
        snaphots_grid.display = self.restore_enabled
        yield label
        yield snaphots_grid

    def on_mount(self) -> None:
        """
        add tool tip for collapsible and generate all the argocd input rows
        """
        header = self.get_widget_by_id(f"{self.app_name}-snapshots-header")
        header.tooltip = "Configure parameters for a restore from backups."

        # enable or disable cnpg restore if available
        if isinstance(self.cnpg_restore, bool):
            box = self.get_widget_by_id(f"{self.app_name}-restore-cnpg-row")
            init_lbl = Label("Restore 🐘 CNPG cluster", classes="initialization-label")
            init_lbl.tooltip = (
                    "if supported, smol-k8s-lab will perform a one-time initial"
                    f" restore of this {self.app_name}'s CNPG cluster from an "
                    "s3 endpoint using [b]barman[/b]"
                    )
            box.mount(init_lbl)
            box.mount(Label("Enabled: ", classes="app-init-switch-label"))
            box.mount(Switch(value=self.cnpg_restore,
                             id=f"{self.app_name}-cnpg-restore-enabled",
                             name="cnpg restore enabled",
                             classes="app-init-switch"))

        if self.snapshots:
            self.generate_snapshot_id_rows()

    def generate_snapshot_id_rows(self,) -> None:
        """
        generate each row of snapshot ids for the restore widget
        """
        grid = self.get_widget_by_id(f"{self.app_name}-restore-grid")
        # create a label and input row for each restic snapshot ID
        for key, value in self.snapshots.items():
            if not value:
                value = "latest"
            elif isinstance(value, int):
                value = str(value)

            argo_label = Label(f"{key.replace('_',' ')}:", classes="argo-config-label")
            argo_label.tooltip = f"restic snapshot ID for {self.app_name} {key}"
            if self.app_name in key:
                input_id = f"{key}-restic-snapshot-id"
            else:
                input_id = f"{self.app_name}-{key}-restic-snapshot-id"
            input = Input(placeholder=f"Enter a {key}",
                          value=value,
                          name=key,
                          validators=[Length(minimum=3)],
                          id=input_id,
                          classes=f"{self.app_name} argo-config-input")
            input.validate(value)

            grid.mount(Horizontal(argo_label, input, classes="argo-config-row"))

    @on(Input.Changed)
    def update_base_yaml_for_input(self, event: Input.Changed) -> None:
        """
        whenever any of our inputs change, we update the base app's saved config.yaml
        """
        input = event.input

        # update our local cache of snapshot IDs
        self.snapshots[input.name] = input.value

        # update self.app's config with input that has changed
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
            # enable/disable display for cnpg restore switch row
            if self.cnpg_restore != "not_applicable":
                cnpg_grid = self.get_widget_by_id(f"{self.app_name}-restore-cnpg-row")
                cnpg_grid.display = truthy

            # enable/disable display for snapshots grid
            label = self.get_widget_by_id(f"{self.app_name}-snapshots-header")
            label.display = truthy
            snapshots = self.get_widget_by_id(f"{self.app_name}-restore-grid")
            snapshots.display = truthy

            # update this widget's restore.enabled variable
            self.restore_enabled = truthy

            # update the base app's init.restore.enabled variable
            self.app.cfg['apps'][self.app_name]['init']['restore']['enabled'] = truthy
            self.app.write_yaml()

        if event.switch.id == f"{self.app_name}-cnpg-restore-enabled":
            # update this widget's cnpg_restore.enabled variable
            self.cnpg_restore = truthy
            # update the base app's init.restore.cnpg_restore.enabled variable
            self.app.cfg['apps'][self.app_name]['init']['restore']['cnpg_restore'] = truthy
            self.app.write_yaml()
