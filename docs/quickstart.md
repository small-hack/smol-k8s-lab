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


### Installation

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


### Configuration

🔔 You *have to edit* your `$XDG_CONFIG_DIR/smol-k8s-lab/config.yaml` (usually `~/.config/smol-k8s-lab/config.yaml`) to be your own values. Better cli options and Interactive config setup coming soon!

Here's an example config file already filled out with comments:

```yaml
---
# the logging of smol-k8s-lab itself
log:
  ## path of file to log to if console logging is not desired
  # file: "./smol-k8s-log.log"
  # logging level, Options: debug, info, warn, error
  level: "info"

distribution:
  k3s:
    # enable k3s deployment
    enabled: true
    # if kubernetes.distribution set to k3s, you can add an array of extra
    # arguments to pass to the k3s install script
    extra_args: []
  kind:
    # enable kind deployment
    enabled: false
  k0s:
    # enable k0s deployment
    enabled: false

ingress-nginx:
  # enable or disable ingress-nginx
  enabled: true

# enable or disable cert-manager
cert-manager:
  # enable or disable cert-manager
  enabled: true
  # Used for letsencrypt-staging, to generate certs
  email: "coolemailfordogs@verygooddogs.net"

metallb:
  enabled: true
  # metallb IPs used for DNS later (make sure they're not in use)
  address_pool: []
  ## Example of required full CIDR notation
  # - 192.168.90.01/32

argo_cd:
  # Install ArgoCD to install other apps
  enabled: true
  domain: "argocd.coolwebsitesfordogs.com"
  # set to "" for basic authentication via ArgoCD directly
  # only keycloak has been tested so far
  identity_provider: "keycloak"

# plugin allows us to specify a k8s secret with info like your hostnames
argo_cd_appset_secret_plugin:
  # this is enabled by default if you enable Argo CD
  enabled: true

# keycloak is an IAM provider that you can use with ArgoCD for user/group
# management and oauth2. it can work with vouch to secure domains that
# otherwise wouldn't have authentication
keycloak:
  enabled: true
  domain: "iam.coolwebsitesfordogs.com"

# kubernetes native security policy management
kyverno:
  enabled: false
```

## Install a distro of k8s

```bash
# you can replace kind with k0s or k3s
smol-k8s-lab kind
```

🎉 You're done!

## UnInstall a distro of k8s

```bash
# you can replace kind with k0s or k3s
# --delete can be replaced with -D
smol-k8s-lab kind --delete
```

🎉 You're done! Again! 🎉

<hr>

## Bonus Stuff
Everything below here is optional, but will help you get rolling faster.

### Install some kubectl plugins with krew
Krew is a plugin manager for `kubectl` plugins. You can install it with `brew install krew` and update plugins with `kubectl krew update`

These together make namespace switching better. Learn more about kubectx + kubens [here](https://github.com/ahmetb/kubectx).

```bash
kubectl krew install ctx
kubectl krew install ns
```

This will help with generating example k8s resources:

```bash
kubectl krew install example
```

This one helps find deprecated stuff in your cluster:

```bash
kubectl krew install deprecations
```

To install plugins from a krew file, you just need a file with one plugin per line. You can use [this one](https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/deps/kubectl_krew_plugins):

```bash
curl -O https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/deps/kubectl_krew_plugins

kubectl krew install < kubectl_krew_plugins
```

### k8s shell aliases

Add some [helpful k8s aliases](https://github.com/jessebot/dot_files/blob/main/.bashrc_k8s):

```bash
# copy the file
curl -O https://raw.githubusercontent.com/jessebot/dot_files/main/.bashrc_k8s

# load the file for your current shell
source ~/.bashrc_k8s
```

To have the above file sourced every new shell, copy this into your `.bashrc` or `.bash_profile`:

```bash
# include external .bashrc_k8s if it exists
if [ -f $HOME/.bashrc_k8s ]; then
    . $HOME/.bashrc_k8s
fi
```
