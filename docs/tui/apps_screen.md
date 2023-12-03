The TUI features an applications screen to modify or create new Argo CD Applications for your cluster.

[<img src="/assets/images/screenshots/apps_screen.svg" alt="screenshot of the application configuration screen for the smol-k8s-lab TUI. On the top left-hand side, there is a list of applications (titled Select apps) that can be scrolled through with arrow keys once selected. It will always have one item in the list highlighted. On the top right-hand side, there is a configuration menu (titled Configure parameters for argo-cd) for the highlighted application from the left hand list. The configuration shows options for initialization with a switch to enable or disable it, and then headers and inputs for the following: Argo CD Application Configuration which has inputs for: repo, path, ref, and namespace. Template values for Argo CD ApplicationSets which has inputs for parameters that can passed to Argo CD ApplicationSets and in this screenshot shows an input for hostname. There are more headers that will be discussed further on in the docs. On the left-hand side below the apps list are two buttons: top button is ✨ New App, bottom button is ✏️ Modify Globals. Final box on the screen below all previously described elements is the App Description which shows a description and link to https://argo-cd.readthedocs.io/en/stable/">](/assets/images/screenshots/apps_screen.svg)

## Selecting Applications

The left hand side [SelectionList] can be clicked or navigated using your arrow keys. To enable an app, you can either click it, or you can use the `spacebar` or `enter` keys. Only selected apps will be installed on your cluster.

## Modifying an Application

To modify an application, ensure it highlighted in the left hand list and then you can modify the parameters under each section described below:

### Argo CD Application Configuration

This section contains parameters to configure a [directory-type Argo CD Application](https://argo-cd.readthedocs.io/en/stable/user-guide/directory/) which includes:

| parameter   | description                                                             |
|:------------|:------------------------------------------------------------------------|
| `repo`      | git repository to use for your Argo CD Application                      |
| `path`      | path in git repo to your kubernetes manifest files you'd like to deploy |
| `ref`       | git branch or git tag to point to in the git repo                       |
| `namespace` | Kubernetes namespace to deploy your Argo CD Application in              |

### Template Values for Argo CD ApplicationSet

This section for modifying and/or adding values for this the currently selected `ApplicationSet` using the [appset secret plugin] to provide variables to the Argo CD Application at creation time.


### Argo CD Project Configuration

This section is for modifying the [Argo CD Project] parameters, which currently includes the following:

| parameter      | description                                                             |
|:---------------|:------------------------------------------------------------------------|
| `namespaces`   | namespaces that the Argo CD Applications are allowed to operate in      |
| `source repos` | allow list of repos that Argo CD applications can be sourced from       |

## Adding new Applications

To add a new application, select the "✨ New App" button under the Select apps list, which will display this modal screen:

[<img src="/assets/images/screenshots/new_app_modal_screen.svg" alt="terminal screenshot of smol-k8s-lab new app modal screen, which shows a header that says Please enter a name and description for your application and two input fields and a Submit button: input 1: Name of your Argo CD Application, input 2: (optional) Description of your Argo CD Application">](/assets/images/screenshots/new_app_modal_screen.svg)

Enter a name for your app, and an optional description and select Submit. To cancel this action, you can either click the `cancel` link in the bottom border, or you can hit the `esc` key.


## Modifying Globally Available Templating Parameters for Argo CD ApplicationSets

To modify globally available templating parameters for *all* Argo CD ApplicationSets, select the second button the left hand side called "✏️  Modify Globals" which will launch a modal screen like this:

[<img src="/assets/images/screenshots/modify_global_parameters_modal_screen.svg" alt="terminal screenshot of smol-k8s-lab modify globals modal screen. Shows a box with a blue border around it and a header that says Modify globally available Argo CD ApplicationSet templating values and then by default one input field called cluster issuer with pre-populated text: 'letsencrypt-staging'. Below that is a row with an add button featuring a plus sign and another input field that says new key name. Below that is a link in the border that says close.">](/assets/images/screenshots/modify_global_parameters_modal_screen.svg)

To close this modal screen, you can either click the `close` link in the bottom border, or you can hit the `esc` key.


## Invalid Apps

If you have any Applications enabled that have invalid fields (empty fields), you'll see a screen like this:

[<img src="/assets/images/screenshots/invalid_apps_screen.svg" alt="terminal screenshot of smol-k8s-lab invalid apps screen, a box with an orange border and border title of The following app fields are empty. below it says Click the app links below to fix the errors or disable them. Below that there is a datatable with columns Application and Invalid fields. The rows read: argo-cd, hostname. cert_manager, email. k8up, timezone. metallb, address_pool. vouch, domains, emails, hostname. zitadel, username, email, first_name, last_name, hostname">](/assets/images/screenshots/invalid_apps_screen.svg)

To fix this, just click each app and either disable them by clicking the heart next app you don't want to use, or fill in any field that is empty, which should also be highlighted in pink.
