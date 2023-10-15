---
layout: default
parent: Intro
title: Configuration File
description: "smol-k8s-lab config file"
permalink: /config-file
---

# Configuration File

smol-k8s-lab will walk you through an initial configuration, but you can also edit your configuration file directly in `$XDG_CONFIG_DIR/smol-k8s-lab/config.yaml` (usually `~/.config/smol-k8s-lab/config.yaml`) to be your own values.

You can checkout the full official current default `config.yaml` [here](https://github.com/small-hack/smol-k8s-lab/blob/main/smol_k8s_lab/config/default_config.yaml).

## Logging

Logging defaults to `info` level, but you can you make it more verbose by changing it to `debug` or less verbose by changing it to `warn` or `error`.

All logging is done directly to your console (stdout) aka standard out, unless you pass in `log.filename` in the configuration.

Example logging configuration:

```yaml
# logging configuration for the smol-k8s-lab CLI
log:
  # path of file to log to if console logging is NOT desired
  file: "./smol-k8s-log.log"
  # logging level, Options: debug, info, warn, error
  level: "debug"
```

## Kubernetes distros

Each supported Kubernetes distro is listed under `k8s_distros` in config.yaml. You can enable one by setting `k8s_distros.{distro}.enabled` to `true`.
Currently you can only deploy one distro at a time.


### k3s

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
      # if you enable metallb, we automatically add servicelb to the disable list
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
      path: "alpha/home_assistant"
      # git branch or tag to point at in the argo repo above
      ref: "main"
      # Kubernetes namespace to install the k8s app in
      namespace: "zitadel"
      # source git repos for Argo CD App Project (in addition to argo.repo)
      project_source_repos:
        - "registry-1.docker.io"
```

Note: Only applications with the `init` field in the [`default_config.yaml`](https://github.com/small-hack/smol-k8s-lab/blob/main/smol_k8s_lab/config/default_config.yaml) can be initialized by `smol-k8s-lab`, therefore, you cannot use the `apps.{app}.init` parameter for custom apps. You can still use the appset secret plugin for Argo CD though :)

### Globally Available Argo CD ApplicationSet 

You can also use the [appset secret plugin]() to store parameters that are available to _all_ Argo CD ApplicationSets. You can configure these via the configuration file like this:

```yaml
```
