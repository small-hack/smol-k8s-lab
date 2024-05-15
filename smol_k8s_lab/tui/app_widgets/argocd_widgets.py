#!/usr/bin/env python3.11
from smol_k8s_lab.tui.util import create_sanitized_list
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Grid
from textual.validation import Length
from textual.widgets import Input, Label, Static, Switch, Collapsible


class ArgoCDApplicationConfig(Static):
    """
    An Argo CD directory type application creation textual widget
    ref: https://argo-cd.readthedocs.io/en/stable/user-guide/directory/
    """

    def __init__(self, app_name: str, argo_params: dict) -> None:
        self.app_name = app_name
        self.argo_params = argo_params
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Collapsible(Grid(classes="collapsible-updateable-grid",
                               id=f"{self.app_name}-collapsible-updateable-grid"),
                          collapsed=False,
                          title="Argo CD Application Configuration",
                          classes="collapsible-with-some-room",
                          id=f"{self.app_name}-argocd-app-config")

    def on_mount(self) -> None:
        """
        add tool tip for collapsible and generate all the argocd input rows
        """
        header = self.get_widget_by_id(f"{self.app_name}-argocd-app-config")

        header.tooltip = (
                "Configure parameters for an Argo CD Application. Designed "
                "to accomadate [i]directory-type[/] applications. Learn more at "
                "https://argo-cd.readthedocs.io/en/stable/user-guide/directory/"
                )

        self.generate_rows()

    def generate_rows(self) -> None:
        """
        generate all the rows for all the parameters we support for a directory
        type app
        """
        grid = self.get_widget_by_id(f"{self.app_name}-collapsible-updateable-grid")

        tooltips = {
                'repo': 'URL to a git repository where you have k8s manifests' +
                        ' (including Argo resources) to deploy',
                'path': 'Path in a git repo to resources you want to deploy. ' +
                        'Trailing slash is important',
                'revision': 'Git branch or tag to point to in the repo',
                'cluster': 'Kubernetes cluster to deploy the Argo CD App to',
                'namespace': 'Kubernetes namespace to deploy the Argo CD App to',
                'directory_recursion': 'Recurse [i]all[/i] directories of the' +
                                       ' git repo to apply any k8s manifests ' +
                                       'found in each directory.'
                }

        # create a label and input row for each argo value, excedpt directory_recursion
        for key, value in tooltips.items():
            if key != "directory_recursion":
                input_value = self.argo_params.get(key, "")
                input = Input(placeholder=f"Enter a {key}",
                              value=input_value,
                              name=key,
                              validators=[Length(minimum=2)],
                              id=f"{self.app_name}-{key}",
                              classes=f"{self.app_name} argo-config-input")
                input.validate(self.argo_params[key])

                argo_label = Label(f"{key}:", classes="argo-config-label")
                argo_label.tooltip = value

                grid.mount(Horizontal(argo_label, input, classes="argo-config-row"))

        # directory_recursion is a boolean, so we have a seperate process for it
        bool_label = Label("directory recursion:", classes="argo-config-label")
        bool_label.tooltip = tooltips['directory_recursion']

        switch = Switch(value=self.argo_params['directory_recursion'],
                        classes="bool-switch-row-switch",
                        name="directory_recursion",
                        id=f"{self.app_name}-directory_recursion")
        switch.tooltip = tooltips['directory_recursion']

        grid.mount(Horizontal(bool_label, switch, classes="argo-switch-row"))

    @on(Input.Changed)
    def update_base_yaml_for_input(self, event: Input.Changed) -> None:
        """
        whenever any of our inputs change, we update the base app's saved config.yaml
        """
        input = event.input
        parent_app_yaml = self.app.cfg

        parent_app_yaml['apps'][self.app_name]['argo'][input.name] = input.value

        self.app.write_yaml()

    @on(Switch.Changed)
    def update_base_yaml_for_switch(self, event: Switch.Changed) -> None:
        """
        if user changes the directory recursion value, we write that out
        """
        truthy = event.value
        self.app.cfg['apps'][self.app_name]['argo']['directory_recursion'] = truthy

        self.app.write_yaml()


class ArgoCDProjectConfig(Static):
    """
    a widget for configuring Argo CD project settings for a given app name
    """

    def __init__(self, app_name: str, argo_params: dict) -> None:
        self.app_name = app_name
        self.argo_params = argo_params
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Collapsible(
                Grid(classes=f"collapsible-updateable-grid {self.app_name}",
                     id=f"{self.app_name}-proj-collapsible-updateable-grid"),
                collapsed=True,
                title="Advanced Argo CD Project Configuration",
                classes="collapsible-with-some-room",
                id=f"{self.app_name}-argo-proj-config-collapsible")

    def on_mount(self):
        """
        generate all input rows on mount
        """
        self.generate_rows()

    def generate_rows(self):
        """
        generate input rows for the Argo CD project configuration widget including
        project name, project namespaces, and project source repos
        """
        grid = self.get_widget_by_id(f"{self.app_name}-proj-collapsible-updateable-grid")

        # row for project destination namespaces
        name_label = Label("project name:",
                      classes=f"{self.app_name} argo-config-label")
        name_label.tooltip = "The name of the Argo CD AppProject for the App to live"

        # set project name for the user if they don't have one
        proj_name = self.argo_params.get("name", "")
        if not proj_name:
            value = self.app_name.replace("_","-")
            if value == 'argo-cd':
                value = 'argocd'
        else:
            value = proj_name

        classes = f"{self.app_name} argo-config-input argo-proj-name"
        name_input =  Input(placeholder="Enter the name of your project",
                    name="name",
                    id="project-name",
                    validators=Length(minimum=2),
                    value=value,
                    classes=classes)

        grid.mount(Horizontal(name_label, name_input,
                              classes=f"{self.app_name} argo-config-row"))

        # row for project namespaces
        namespace_label = Label("namespaces:",
                                classes=f"{self.app_name} argo-config-label")
        namespace_label.tooltip = "Comma seperated list of namespaces"

        n_spaces = self.argo_params["destination"]["namespaces"]
        if n_spaces:
            value = ", ".join(n_spaces)
        else:
            value = ""

        classes = f"{self.app_name} argo-config-input argo-proj-ns"
        namespace_input = Input(
                placeholder="Enter comma seperated list of namespaces",
                name="namespaces",
                id="project-namespaces",
                validators=Length(minimum=2),
                value=value,
                classes=classes)

        grid.mount(Horizontal(namespace_label, namespace_input,
                              classes=f"{self.app_name} argo-config-row"))

        # row for project source repos
        label = Label("source repos:",
                      classes=f"{self.app_name} argo-config-label")
        label.tooltip = "Comma seperated list of project source repos"

        repos = self.argo_params["source_repos"]
        if repos:
            value = ", ".join(repos)
        else:
            value = ""
        classes = f"{self.app_name} argo-config-input argo-proj-repo"
        input = Input(placeholder="Enter comma seperated list of source repos",
                      value=value,
                      name="source_repos",
                      id="project-source-repos",
                      validators=Length(minimum=5),
                      classes=classes)

        grid.mount(Horizontal(label, input,
                              classes=f"{self.app_name} argo-config-row"))

    @on(Input.Changed)
    def update_base_yaml(self, event: Input.Changed) -> None:
        """
        if the input is valid, write the input as a list to the base yaml
        """
        if event.validation_result.is_valid:
            # section of the yaml this widget updates
            project_yml = self.app.cfg['apps'][self.app_name]['argo']['project']

            # the name of the input triggering this
            input_name = event.input.name

            if input_name in ['namespaces', 'source_repos']:
                # sorts out any spaces or commas as delimeters to create a list
                yaml_value = create_sanitized_list(event.input.value)
            else:
                yaml_value = event.input.value

            if event.input.name == 'namespaces':
                project_yml['destination'][event.input.name] = yaml_value
            else:
                project_yml[event.input.name] = yaml_value

            self.app.write_yaml()
