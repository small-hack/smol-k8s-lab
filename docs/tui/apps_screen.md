The TUI features an applications screen to modify or create new Argo CD Applications for your cluster.

[<img src="../../assets/images/screenshots/apps_screen.svg" alt="screenshot of the application configuration screen for the smol-k8s-lab TUI. On the top left-hand side, there is a list of applications (titled Select apps) that can be scrolled through with arrow keys once selected. It will always have one item in the list highlighted. On the top right-hand side, there is a configuration menu (titled Configure parameters for argo-cd) for the highlighted application from the left hand list. The configuration shows options for initialization with a switch to enable or disable it, and then headers and inputs for the following: Argo CD Application Configuration which has inputs for: repo, path, ref, and namespace. Template values for Argo CD ApplicationSets which has inputs for parameters that can passed to Argo CD ApplicationSets and in this screenshot shows an input for hostname. There are more headers that will be discussed further on in the docs. On the left-hand side below the apps list are two buttons: top button is ✨ New App, bottom button is ✏️ Modify Globals. Final box on the screen below all previously described elements is the App Description which shows a description and link to https://argo-cd.readthedocs.io/en/stable/">](../../assets/images/screenshots/apps_screen.svg)

![type:video](../../assets/videos/tour_of_apps_config.mov)

## Selecting Applications

The left hand side [SelectionList] can be clicked or navigated using your arrow keys. To enable an app, you can either click it, or you can use the `spacebar` or `enter` keys. Only selected apps will be installed on your cluster.

## Modifying a simple or custom Application

To modify an application, ensure it's highlighted in the left hand list and then you can modify the parameters under each section described below:

### Argo CD Application Configuration

This section contains parameters to configure a [directory-type Argo CD Application](https://argo-cd.readthedocs.io/en/stable/user-guide/directory/) which includes:

| parameter             | description                                                                     |
|:----------------------|:--------------------------------------------------------------------------------|
| `repo`                | git repository to use for your Argo CD Application                              |
| `path`                | path in git repo to your kubernetes manifest files you'd like to deploy         |
| `revision`            | git branch or git tag to point to in the git repo                               |
| `cluster`             | Kubernetes cluster to deploy this Argo CD Application to                        |
| `namespace`           | Kubernetes namespace to deploy your Argo CD Application in                      |
| `directory_recursion` | Enabled recursive directory crawl of Argo CD repo for applying nested manifests |

### Template Values for Argo CD ApplicationSet

This section for modifying and/or adding values for this the currently selected `ApplicationSet` using the [appset secret plugin] to provide variables to the Argo CD Application at creation time.


### Argo CD Project Configuration

This section is for modifying the [Argo CD Project] parameters, which currently includes the following:

| parameter                 | description                                                        |
|:--------------------------|:-------------------------------------------------------------------|
| `name`                    | name of the Argo CD Project                                        |
| `destionation.namespaces` | namespaces that the Argo CD Applications are allowed to operate in |
| `source repos`            | allow list of repos that Argo CD applications can be sourced from  |

## Modifying an init-supported application

Some applications, such as nextcloud, matrix, and mastodon, support a special init phase for credentials creation, or restoration if backups are supported as well. When this is possible, you'll see a tabbed view for the configuration panel on the right hand side of the apps screen. It will include 4 tabs. We'll go through each below.

### Initialization Configuration
This phase includes setting up one time passwords in your password manager and in a kubernetes secret for credentials such as your admin credentials or SMTP credentials. To use the same name for an app without using our custom initialization process, please click the switch next to "Initialization Enabled" to set it to disabled. This will then treat this app as a normal custom app.

The values pictured in the screenshot below translate to the following YAML:
```yaml
apps:
  nextcloud:
    # initialize the app by setting up new k8s secrets and/or bitwarden items
    init:
      enabled: true
      values:
        # change the name of your admin user to whatever you like. This is used in an admin credentials k8s secret
        admin_user: my_nextcloud_admin
        smtp_user: my_smtp_nextcloud_username
        smtp_host: smtp-server.com
        # this value is taken from an environment variable
        smtp_password:
          value_from:
            env: NC_SMTP_PASSWORD
```

[<img src="../../assets/images/screenshots/apps_screen_init.svg" alt="terminal screenshot of smol-k8s-lab on the apps screen with the nextcloud app selected. It shows a tabbed configuration panel on the right hand side that shows the following tabs: initialization config, argo cd app config, backup, restore. Init config is selected which shows a switch to enable or disable init, followed by a header that says init values. below that are input fields specific to nextcloud's init phase. They include: admin user set to my_nextcloud_admin, smtp user set to my_smtp_nextcloud_username, smtp host set to smtp-server.com, and smtp password, which is currently blank. Because the last field is blank, it has a pink border showing the input is invalid. At the bottom of the configuration panel are two border links: sync, delete">](../../assets/images/screenshots/apps_screen_init.svg)

### Backups Configuration

Backups are done via k8up which is a wrapper around restic. For apps using cloud native postgres operator created clusters, we support both backup and restore of the database. For nextcloud specifically, we also put the database into maintainence mode. Here's an example of what you'll see in the TUI:

[<img src="../../assets/images/screenshots/apps_screen_backups.svg" alt="terminal screenshot of smol-k8s-lab on the apps sceen with the nextcloud app selected. it shows a tabbed config panel on the right hand side that shows the following tabs: initialization config, argo cd app config, backup, restore. Backup is currently selected. The backup tab starts with a centered button called 💾 Backup Now. Below that is a header that says 📆 Scheduled Backups. Below that are two input fields. First input is PVC schedule set to 10 0 astrik astrik astrik. Second input is DB schedule set to 0 0 0 astrik, astrik, astrik. Below that is a collapsible header called S3 Configuration. In the collapsible there are three input fields visible: endpoint, set to backblaze endpoint, bucket set to my-remote-s3-bucket, and region set to eu-central-003. The backup tab is long enough that it features a scrollbar.">](../../assets/images/screenshots/apps_screen_backups.svg)

For more on backups, see [Config File > Backups](/config_files/#backups).

### Restoring from Backup Configuration

To restore from a backup, you'll need to configure if you'd like to restore PVCs and the CNPG postgresql database or just the PVC. To do just the PVC set the "Restore 🐘 CNPG cluster enabled" switch to disabled by clicking it.

By default, we always use the latest restic snapshot ID to restore your cluster. If you'd like to use different snapshot IDs, please change the word "latest" for each PVC.


[<img src="../../assets/images/screenshots/apps_screen_restores.svg" alt="terminal screenshot of smol-k8s-lab on the apps sceen with the nextcloud app selected. it shows a tabbed config panel on the right hand side that shows the following tabs: initialization config, argo cd app config, backup, restore. The restore tab is selected and it features three header rows followed by some fields. First header row says restore from backup enabled and has a switch set to on, second header row says restore cnpg cluster enabled and has a switch set to on, and the third header row says Restic Snapshot IDs with the following input fields below, all set to latest: seaweedfs_volume, seaweedfs_filer, seaweedfs_master, and nextcloud_files.">](../../assets/images/screenshots/apps_screen_restores.svg)

For more on restores, see [Config File > Restores](/config_files/#restores).

### Deleting an Application

To delete an existing Argo CD Application, you can click the delete link at the bottom of the app configuration panel on the right. After you click it, you will see the following modal screen. If you click the checkbox next to word Force, you will pass in `--force` to the `argocd app delete` command when we run it. If/when you click the delete button, we will delete the app, associated appsets, and everything in the namespace.

[<img src="../../assets/images/screenshots/delete_app_modal_screen.svg" alt="terminal screenshot of smol">](../../assets/images/screenshots/delete_app_modal_screen.svg)


!!! Note
    The delete link will only be present if you're modifying an existing cluster, and the app is already present in Argo CD.

### Syncing an Application

To sync an existing Application, click the "sync" link at the bottom of the app configuration panel on the right.

!!! Note
    The sync link will only be present if you're modifying an existing cluster, and the app is already present in Argo CD.


## Adding new Applications

To add a new application, select the "✨ New App" button under the Select apps list, which will display this modal screen:

[<img src="../../assets/images/screenshots/new_app_modal_screen.svg" alt="terminal screenshot of smol-k8s-lab new app modal screen, which shows a header that says Please enter a name and description for your application and two input fields and a Submit button: input 1: Name of your Argo CD Application, input 2: (optional) Description of your Argo CD Application">](../../assets/images/screenshots/new_app_modal_screen.svg)

Enter a name for your app, and an optional description and select Submit. To cancel this action, you can either click the `cancel` link in the bottom border, or you can hit the `esc` key.


## Modifying Globally Available Templating Parameters for Argo CD ApplicationSets

To modify globally available templating parameters for *all* Argo CD ApplicationSets, select the second button the left hand side called "✏️  Modify Globals" which will launch a modal screen like this:

[<img src="../../assets/images/screenshots/modify_global_parameters_modal_screen.svg" alt="terminal screenshot of smol-k8s-lab modify globals modal screen. Shows a box with a blue border around it and a header that says Modify globally available Argo CD ApplicationSet templating values and then by default one input field called cluster issuer with pre-populated text: 'letsencrypt-staging'. Below that is a row with an add button featuring a plus sign and another input field that says new key name. Below that is a link in the border that says close.">](../../assets/images/screenshots/modify_global_parameters_modal_screen.svg)

To close this modal screen, you can either click the `close` link in the bottom border, or you can hit the `esc` key.


## Invalid Apps

If you have any Applications enabled that have invalid fields (empty fields), you'll see a screen like this:

[<img src="../../assets/images/screenshots/invalid_apps_screen.svg" alt="terminal screenshot of smol-k8s-lab invalid apps screen, a box with an orange border and border title of The following app fields are empty. below it says Click the app links below to fix the errors or disable them. Below that there is a datatable with columns Application and Invalid fields. The rows read: argo-cd, hostname. cert_manager, email. k8up, timezone. metallb, address_pool. vouch, domains, emails, hostname. zitadel, username, email, first_name, last_name, hostname">](../../assets/images/screenshots/invalid_apps_screen.svg)

To fix this, just click each app and either disable them by clicking the heart next app you don't want to use, or fill in any field that is empty, which should also be highlighted in pink.
