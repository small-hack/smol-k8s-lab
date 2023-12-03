---
layout: default
parent: Intro
title: Configuration File
description: "smol-k8s-lab config file"
permalink: /config-file
---

smol-k8s-lab will walk you through an initial configuration, but you can also edit your configuration file directly in `$XDG_CONFIG_DIR/smol-k8s-lab/config.yaml` (usually `~/.config/smol-k8s-lab/config.yaml`) to be your own values.

You can checkout the full official current [default `config.yaml`](https://github.com/small-hack/smol-k8s-lab/blob/main/smol_k8s_lab/config/default_config.yaml).

## TUI Configuration

You can checkout more about the TUI in [our tui config section](/tui/tui_config), but briefly please see the default configuration for in the yaml below:

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
    # accessibility options for users that benefit from TTS and Bell sounds
    accessibility:
      # options related to terminal bell sounds
      bell:
        # ring the built in terminal bell on focus to new elements on the screen
        on_focus: true
        # ring the built in terminal bell when something is wrong
        on_error: true
      # options related to text to speech
      text_to_speech: 
        # use a specific program for text to speech - needs to be a full path
        # macOS default: say
        speech_program: say
        # read aloud the screen title and description
        screen_titles: true
        # read aloud the element id, value, and tooltip each time you switch focus
        on_focus: false
        # press f5 to read the element id and selected row of DataTables
        on_key_press: true
```

Regarding the `smol_k8s_lab.tui.accessibility` section. If you have experience with programming python on linux to work with screenreaders or working in the terminal using screen readers generally, please reach out on GitHub via an Issue or Discussion. We'd love your opinions and help!

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

!!! NOTE
    You cannot adjust the k3s node count at this time

```yaml
# which distros of Kubernetes to deploy. Options: kind, k3s, k3d
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
      - "max_pods=150"
    # not yet adjustable on k3s at this time
    nodes:
      control_plane: 1
      workers: 0
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
      - "max_pods=150"
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
      maxPods: 110
      podsPerCore: 0
      resolvConf: "/etc/resolv.conf"
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
    # if existing items are found in your password manager, do one of:
    #
    # ask: (default in tui mode) display a dialog window asking you how to proceed
    # edit: edit item, if there's one item found, ask if multiple found
    # duplicate: create an additional item with the same name
    # no_action: don't do anything, just continue on with the script
    duplicate_strategy: ask
```

## Applications

All applications are under the `apps` parameter in the `config.yaml`. You can even add your own. Here's an example application:

```yaml
apps:
  # name of the application to create with Argo CD
  home_assistant:
    # if enabled is set to false, we will skip this app
    enabled: true
    argo:
      # secrets keys to make available to Argo CD ApplicationSets
      secret_keys:
        # FQDN to use for home assistant
        hostname: "ha.test.com"
      # git repo to install the Argo CD app from
      repo: "https://github.com/small-hack/argocd-apps"
      # path in the argo repo to point to. Trailing slash very important!
      path: "demo/home_assistant/"
      # git branch or tag to point at in the argo repo above
      ref: "main"
      # Kubernetes namespace to install the k8s app in
      namespace: "home-assistant"
      # recurse directories in the provided git repo
      directory_recursion: false
      project:
        # source git repos for Argo CD App Project (in addition to argo.repo)
        source_repos:
          - registry-1.docker.io
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces:
            - prometheus
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
  # always deploy external secrets. *Must be a string of "" (don't use external secrets) or "bitwarden" to use bitwarden for external secrets*
  external_secrets: "bitwarden"
```
