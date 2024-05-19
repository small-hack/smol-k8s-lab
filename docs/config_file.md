---
layout: default
parent: Intro
title: Configuration File
description: "smol-k8s-lab config file"
permalink: /config-file
---

smol-k8s-lab will walk you through an initial configuration, but you can also edit your configuration file directly in `$XDG_CONFIG_DIR/smol-k8s-lab/config.yaml` (usually `~/.config/smol-k8s-lab/config.yaml`) to be your own values.

You can checkout the full official current [default `config.yaml`](https://github.com/small-hack/smol-k8s-lab/blob/main/smol_k8s_lab/config/default_config.yaml).

## TUI and Accessibility Configuration

You can checkout more about the TUI in [our tui config section](/tui), but briefly please see the default configuration for in the yaml below:

### Visual TUI config options
```yaml
smol_k8s_lab:
  # Terminal User Interface with clickable buttons.
  # Useful for learning smol-k8s-lab or verifying your configuration
  tui:
    # if set to true, we'll always launch smol-k8s-lab in interactive mode :)
    # else you need to pass in --interactive or -i to use the TUI
    enabled: true
    # show bottom footer help bar
    show_footer: true
```

### Accessibility Options

???+ tip
    If you are using smol-k8s-lab via SSH or on a machine that does not have audio drivers installed, you may experience errors in the TUI related to Alsa not running. You can disable ALL of the text to speech and terminal bell features to make it go away.

Below are all the currently supported accessibility features in the `smol-k8s-lab` TUI. If you have experience with python and screenreaders or working in the terminal using screen readers generally, please reach out on GitHub via an Issue or Discussion. We'd love your opinions and help on making our interface more accessible. We're also happy to hear more feed back on other accessibility features!


#### Text to Speech

These are all the options related to text to speech:

```yaml
smol_k8s_lab:
  # Terminal User Interface with clickable buttons.
  # Useful for learning smol-k8s-lab or verifying your configuration
  tui:
    # accessibility options for users that benefit from TTS and Bell sounds
    accessibility:
      # options related to text to speech
      text_to_speech:
        # language to speak in. so far only english supported
        language: en
        # use a specific program for text to speech - needs to be a full path
        speech_program: ''
        # read aloud the screen title
        screen_titles: true
        # read aloud the screen description
        screen_descriptions: false
        # read aloud the element id, value, and tooltip each time you switch focus
        on_focus: false
        # press f5 to read the element id and selected row of DataTables
        on_key_press: true
```

#### Terminal Bell

These options use your built in terminal bell:

```yaml
smol_k8s_lab:
  # Terminal User Interface with clickable buttons.
  # Useful for learning smol-k8s-lab or verifying your configuration
  tui:
    # accessibility options for users that benefit from TTS and Bell sounds
    accessibility:
      # options related to terminal bell sounds
      bell:
        # ring the built in terminal bell on focus to new elements on the screen
        on_focus: true
        # ring the built in terminal bell when something is wrong
        on_error: true
```

## Run command

`run_command` is a special section of the config file to run a command after the config and cluster setup phases of smol-k8s-lab. Here's an example:

```yaml
smol_k8s_lab:
  run_command:
    # command to run after smol-k8s-lab tui is done or immediately when running
    command: k9s --command applications.argoproj.io
    # tell me which terminal you use if you'd like to use split or tab features
    terminal: wezterm
    # where to run the command, options: same window, new window, new tab,
    # split left, split right, split top, split bottom
    # if set to "same window", we just run it in the same window after we're
    # done the entire smol-k8s-lab cli run
    window_behavior: split right
```

The above will setup the k8s cluster, and then immediately run a command to split the current wezterm window into two panes. On the left will be the log output from smol-k8s-lab. On the right, we will launch k9s and view applications as they spin up.

If you set `smol_k8s_lab.run_command.window_behavior` to "same window", then we will not run your command until after smol-k8s-lab is completed.

We rely on knowing what terminal multiplexer you're using to do splits, new tabs, and new windows. The supported terminal values are `wezterm` and `zellij`. If you'd like to see another terminal supported, and the terminal has cli commands or a python library, please feel free to submit a GitHub Issue and we'll try to implement it. If you're savy with python, please also feel free to submit a PR :)

## Logging

Logging defaults to `info` level, but you can you make it more verbose by changing it to `debug` or less verbose by changing it to `warn` or `error`.

All logging is done directly to your console (stdout) aka standard out, unless you pass in `log.filename` in the configuration.

Example logging configuration:

```yaml
smol_k8s_lab:
  # logging configuration for the smol-k8s-lab CLI
  log:
    # path of file to log to if console logging is NOT desired
    file: ""
    # logging level, Options: debug, info, warn, error
    level: "debug"
```

## Kubernetes distros

Each supported Kubernetes distro is listed under `k8s_distros` in config.yaml. You can enable one by setting `k8s_distros.{distro}.enabled` to `true`.
Currently you can only deploy one distro at a time.


### k3s

For k3s, we use a [config file](https://docs.k3s.io/installation/configuration#configuration-file) for [all the options](https://docs.k3s.io/cli/server) that get passed to the k3s install script. We define them under `k8s_distros.k3s.k3s_yaml` in the `smol-k8s-lab` config file.

```yaml
# NOTE: only kind is available on macOS at this time
k8s_distros:
  k3s:
    # set to true to enable deploying a Kubernetes cluster using k3s
    enabled: false
    # if k8s_distro set to k3s/k3d, you can add an array of extra arguments to pass
    # to the k3s install script as a k3s.yaml file. If you enable cilium, we
    # automatically pass in flannel-backend: none and disable-network-policy: true
    k3s_yaml:
      # if you enable MetalLB, we automatically add servicelb to the disable list
      # enables encryption at rest for Kubernetes secrets
      secrets-encryption: true
      # disables traefik so we can enable ingress-nginx, remove if you're using traefik
      disable:
      - "traefik"
      node-label:
      - "ingress-ready=true"
      kubelet-arg:
      - "max-pods=150"
    # list of nodes to SSH to and join to cluster
    # if using single node, set to nodes: {}
    nodes:
      # name can be a hostname or ip address
      serverfriend1.lan:
        # must be node type of "worker" or "control_plane"
        node_type: worker
        # change this if not using default port 22
        ssh_port: 22
        # change ssh_key to the name of a local private key to use if id_rsa is not preferred
        ssh_key: id_rsa
        # labels are optional, but may be useful for pod node affinity
        node_labels:
          - iot=true
        # taints are optional, but may be useful for pod tolerations
        node_taints:
          - iot=true:NoSchedule
```

### k3d

```yaml
k8s_distros:
  k3d:
    # set to true to enable deploying a Kubernetes cluster using k3d
    enabled: false
    # if k8s_distro set to k3s/k3d, you can add an array of extra arguments to pass
    # to the k3s install script as a k3s.yaml file. If you enable cilium, we
    # automatically pass in flannel-backend: none and disable-network-policy: true
    k3s_yaml:
      # if you enable metallb, we automatically add servicelb to the disable list
      # enables encryption at rest for Kubernetes secrets
      secrets-encryption: true
      # disables traefik so we can enable ingress-nginx, remove if you're using traefik
      disable:
      - "traefik"
      kubelet-arg:
      - "max-pods=150"
      node-label:
      - "ingress-ready=true"
    # how many dockerized k3s nodes to deploy
    nodes:
      control_plane: 1
      workers: 0
```

### kind

```yaml
k8s_distros:
  kind:
    # set to true to enable deploying a Kubernetes cluster using kind
    enabled: false
    # change the kubelet config for this node in k3s, feel free to add more values
    kubelet_extra_args:
      # all these options are defaults
      node-labels: "ingress-ready=true"
      max-pods: 110
      pods-per-core: 0
      resolv-conf: "/etc/resolv.conf"
    networking_args:
      # all these options are defaults
      ipFamily: "ipv4"
      disableDefaultCNI: False
      apiServerAddress: "127.0.0.1"
      podSubnet: "10.244.0.0/16"
    # how many dockerized kind nodes to deploy
    nodes:
      control_plane: 1
      workers: 0
```

## Password Management
We support using Bitwarden to store and manage your Kubernetes secrets. Enable this feature using `smol-k8s-lab.local_password_manager.enabled` set to `true`.

```yaml
smol_k8s_lab:
  # store your password and tokens directly in your local password manager
  local_password_manager:
    enabled: true
    # enable the use of Bitwarden as your password manager.
    # To use Bitwarden, you must export the following environment variables:
    # BW_PASSWORD, BW_CLIENTID, BW_CLIENTSECRET, BW_SESSION
    # If you're missing any of these, smol-k8s-lab will prompt for them
    name: bitwarden
    # if existing items are found in your password manager, do this:
    duplicate_strategy: ask
```

For `smol_k8s_lab.local_password_manager.duplicate_strategy`, you can choose one of the following strategies:

| strategy  | description                                                             |
|-----------|-------------------------------------------------------------------------|
| ask       | (default in tui mode) display a dialog window asking you how to proceed |
| edit      | edit item, if there's one item found, ask if multiple found             |
| duplicate | create an additional item with the same name                            |
| no_action | don't do anything, just continue on with the script                     |

## Applications

All applications are under the `apps` parameter in the `config.yaml`. For the default installable applications, please check out the [Default Apps](/k8s_apps/argocd) tab. You can even add your own.


### Sensitive values

Since `v5.0.0`, smol-k8s-lab now supports getting your sensitive values from arbitrary environment variables or bitwarden. We support using sensitive values for any value under the following:

- `apps.APP.init.values`
- `apps.APP.backups.s3`
- `apps.APP.backups.restic_repo_password`

To use a value from an environment variable try the following:

```yaml
apps:
  nextcloud:
    backups:
      s3:
        # this value comes from an environment variable
        secret_access_key:
          value_from:
            env: NC_S3_BACKUP_SECRET_KEY
```

If we see `value_from` under any field in init or backups, we will attempt to get the value either from your environment variables or bitwarden.


### Backups and restores

Apps with an init section, which include apps such as nextcloud, mastodon, matrix, and home assistant, can include a backups and restores sections.

#### Backups

For each app that supports backups, you can set:

-  PVC schedule, which is the cron syntax schedule used for running backups of all k8up annotated PVCs in the app's namespace.

-  postgres schedule, which is the cron syntax schedule used for running backups of a cloud native postgresql cluster. NOTE: the cron sytax for this field includes a field for seconds.

- remote s3 configuration, which is a series of fields for the remote backup endpoint, bucket, region, secret_access_key, and access_key_id.

- restic repo password, which is a password for encrypting your remote backups bucket

Here's an example backup section for nextcloud in `config.yaml`:

```yaml
apps:
  nextcloud:
    backups:
      # cronjob syntax schedule to run nextcloud pvc backups
      pvc_schedule: 10 0 * * *
      # cronjob syntax (with SECONDS field) for nextcloud postgres backups
      # must happen at least 10 minutes before pvc backups, to avoid corruption
      # due to missing files. This is because the cnpg backup shows as completed
      # before it actually is, due to the wal archive it lists as it's end not
      # being in the backup yet
      postgres_schedule: 0 0 0 * * *
      s3:
        # these are for pushing remote backups of your local s3 storage, for speed and cost optimization
        endpoint: s3.eu-central-003.backblazeb2.com
        bucket: my-remote-s3-bucket
        region: eu-central-003
        # comes from an environment variable
        secret_access_key:
          value_from:
            env: NC_S3_BACKUP_SECRET_KEY
        # comes from an environment variable
        access_key_id:
          value_from:
            env: NC_S3_BACKUP_ACCESS_ID
      # comes from an environment variable
      restic_repo_password:
        value_from:
          env: NC_RESTIC_REPO_PASSWORD
```

#### Restores

To restore from a backup, you'll need to configure whether you'd like to restore PVCs and the CNPG postgresql database or just the PVC.

By default, we always use the latest restic snapshot ID to restore your cluster. If you'd like to use different snapshot IDs, please change the word "latest" for each PVC.

example YAML:
```yaml
apps:
  nextcloud:
    init:
      # initialize the app by setting up new k8s secrets and/or bitwarden items
      enabled: true
      # restore section
      restore:
        # set to false to disable restoring
        enabled: true
        # set this to false to only restore the PVCs but not the postgres cluster
        cnpg_restore: true
        restic_snapshot_ids:
          # each of these seaweedfs values also contains your postgresql backups
          seaweedfs_volume: latest
          seaweedfs_filer: latest
          seaweedfs_master: latest
          # this is just the nextcloud files pvc
          nextcloud_files: latest
```


### Custom Applications

Here's an example application:

```yaml
apps:
  # name of the application to create with Argo CD
  my_home_assistant:
    # if enabled is set to false, we will skip this app
    enabled: true
    argo:
      # secrets keys to make available to Argo CD ApplicationSets
      secret_keys:
        # FQDN to use for home assistant
        hostname: "ha.test.com"
      # git repo to install the Argo CD app from
      repo: "https://github.com/my-user/argocd-apps"
      # path in the argo repo to point to. Trailing slash very important!
      path: "home_assistant/"
      # git branch or tag to point at in the argo repo above
      revision: "main"
      # name of cluster to deploy this app to
      cluster: "in-cluster"
      # Kubernetes namespace to install the k8s app in
      namespace: "home-assistant"
      # recurse directories in the provided git repo
      directory_recursion: false
      project:
        name: my-home-assistant
        # source git repos for Argo CD App Project (in addition to argo.repo)
        source_repos:
          - registry-1.docker.io
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces:
            - prometheus
            - home-assistant
```

!!! Note
    Only applications with the `init` field in the [`default_config.yaml`](https://github.com/small-hack/smol-k8s-lab/blob/main/smol_k8s_lab/config/default_config.yaml) can be initialized by `smol-k8s-lab`, therefore, you cannot use the `apps.{app}.init` parameter for custom apps. You can still use the appset secret plugin for Argo CD though :) If you'd like initialization supported by smol-k8s-lab, please feel free to open a feature request in the GitHub Issues.

### Globally Available Argo CD ApplicationSet

You can also use the [appset secret plugin]() to store parameters that are available to _all_ Argo CD ApplicationSets. You can configure these via the configuration file like this:

```yaml
apps_global_config:
  # setting this changes all the below domains to use the following cluster_issuer
  # change to letsencrypt-prod when you're ready to go live with your infra
  cluster_issuer: "letsencrypt-staging"
  # change to your tz: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List
  time_zone: "Europe/Amsterdam"
  # always deploy external secrets. *Must be a string of "none" (don't use external secrets) or "bitwarden" to use bitwarden for external secrets*
  external_secrets: "bitwarden"
```
