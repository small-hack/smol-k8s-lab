---
layout: default
parent: Intro
title: Quickstart
description: "Smol K8s Lab Quickstart"
nav_order: 2
permalink: /quickstart
---

## Quickstart

#### Prereqs

- [brew](https://brew.sh)
- Python 3.11 (`brew install python3.11`)
- Have internet access.


## Installation

```bash
# this will install smol-k8s-lab using python 3.11
pip3.11 install smol-k8s-lab
```

Then you should be able to show the help text :)

```bash
# this will show the help text
./smol-k8s-lab --help
```

<details>
  <summary>Help text example</summary>

  <a href="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/screenshots/help_text.svg">
    <img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/screenshots/help_text.svg" alt="Output of smol-k8s-lab --help after cloning the directory and installing the prerequisites.">
  </a>

</details>


## Usage

### Install a distro of k8s
```bash
smol-k8s-lab
```

🎉 You're done!

### UnInstall a distro of k8s

```bash
# --delete can be replaced with -D
smol-k8s-lab --delete
```

🎉 You're done! Again! 🎉


## Configuration

smol-k8s-lab will walk you through an initial configuration, but you can also edit your config directly in `$XDG_CONFIG_DIR/smol-k8s-lab/config.yaml` (usually `~/.config/smol-k8s-lab/config.yaml`) to be your own values.

You can checkout the full official current default config.yaml [here](https://github.com/small-hack/smol-k8s-lab/blob/main/smol_k8s_lab/config/default_config.yaml).

### Logging

Logging defaults to `info` level, but you can you make it more verbose by changing it to `debug` or less verbose by changing it to `warn` or `error`.

All logging is done directly to your console (stdout) aka standard out, unless you pass in `log.filename` in the config.

Example logging config:

```yaml
# logging config for the smol-k8s-lab CLI
log:
  # path of file to log to if console logging is NOT desired
  # file: "./smol-k8s-log.log"
  # logging level, Options: debug, info, warn, error
  level: "debug"
```

### Kubernetes distros

Each supported kubernetes distro is listed under `k8s_distros` in config.yaml. You can enable one by setting `k8s_distros.DISTRO.enabled` to `true`.
Currently you can only deploy one distro at a time. Here's an example of enabling k3s:

```yaml
# which distros of Kubernetes to deploy. Options: kind, k3s, k3d
# NOTE: only kind is available on macOS at this time
k8s_distros:
  # k3s is a small Kubernetes distro maintained by Rancher, which is owned by Suse Linux
  k3s:
    # set to true to enable deploying a kubernetes cluster using k3s
    enabled: true
    # set the maximum pods per node via /etc/rancher/k3s/kubelet.config
    # it's set high for beefy nodes, but you can set it lower if you'd like
    max_pods: 200
    # if k8s_distribution set to k3s, you can add an array of extra
    # arguments to pass to the k3s install script
    extra_args: []

  # NOTE: all of these are disabled by default
  # WARNING: k3d is NOT tested yet. k3d is k3s in docker.
  k3d:
    # set to true to enable deploying a kubernetes cluster using k3d
    enabled: false
  # KinD stands for Kubernetes in Docker, and is developed by the Kubernetes Project
  kind:
    # set to true to enable deploying a kubernetes cluster using kind
    enabled: false
```

### Password Management
We support using Bitwarden to store and manage your kubernetes secrets. Enable this feature using `local_password_manager.enabled` set to `true`.

```yaml
# store your password and tokens directly in your local password manager
local_password_manager:
  enabled: true
  # enable the use of bitwarden as your password manager.
  # To use Bitwarden, you must export the following environment variables:
  # BW_PASSWORD, BW_CLIENTID, BW_CLIENTSECRET, BW_SESSION
  # If you're missing any of these, smol-k8s-lab will prompt for them
  name: bitwarden
  # if existing items are found in your password manager, give smol-k8s-lab
  # permission to delete the old item and create a new one.
  # If set to false, we attempt to create a second item
  overwrite: false
```

### Applications

All applications are under the `apps` parameter in the config.yaml. You can even add your own. Here's an example application:

```yaml
apps:
  # name of the application to create with Argo CD
  zitadel:
    # if enabled is set to false, we will skip this app
    enabled: true
    # Initialization of the app through smol-k8s-lab.
    # In this case, Creates bitwarden and/or k8s secrets and also creates an
    # initial OIDC application for Argo CD and Vouch, a human admin user, and 2
    # groups for argo (users/admins) along with a groupsClaim action. Updates
    # your values in the argo_cd_appset_secret_plugin secret and refreshes the pod
    init:
      # Switch to false if you don't want to create intial secrets or use a the
      # API via a service acocunt to create the above described resources
      # If you're using your own custom argo repo, setting this to false may make sense.
      enabled: true
      # these values are used for init and are only used once.
      # there is no source of truth for these on the cluster
      values:
        username: ""
        email: ""
        first_name: ""
        last_name: ""
        # options: GENDER_UNSPECIFIED, GENDER_MALE, GENDER_FEMALE, GENDER_DIVERSE
        # more coming soon, see: https://github.com/zitadel/zitadel/issues/6355
        gender: "GENDER_UNSPECIFIED"
    argo:
      # secrets keys to make available to ArgoCD ApplicationSets
      secret_keys:
        # FQDN to use for zitadel
        hostname: ""
        # type of database to use: postgresql or cockroachdb
        database_type: "postgresql"
      # repo to install the Argo CD app from
      # git repo to install the Argo CD app from
      repo: "https://github.com/small-hack/argocd-apps"
      # path in the argo repo to point to. Trailing slash very important!
      # if you want to use cockroachdb, change to zitadel/zitadel_and_cockroachdb
      path: "zitadel/zitadel_and_postgresql"
      # either the branch or tag to point at in the argo repo above
      ref: "main"
      # namespace to install the k8s app in
      namespace: "zitadel"
      # source repos for Argo CD App Project (in addition to argo.repo)
      project_source_repos:
        - "https://charts.zitadel.com"
        - "https://zitadel.github.io/zitadel-charts"
        - "https://charts.cockroachdb.com/"
        - "registry-1.docker.io"
```

Note: Only applications with the `init` field in the [default_config.yaml](https://github.com/small-hack/smol-k8s-lab/blob/main/smol_k8s_lab/config/default_config.yaml) can be initialized by smol-k8s-lab with one time values created as a k8s secrets.
