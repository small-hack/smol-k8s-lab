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
# FQDN to access your web interfaces: all of these are only required if you
# specify optional app installs, such as argo
domain:
  # your base domain for use with subdomains below
  # if commented out, you need to provide the entire domain name for each app
  base: "coolwebsitefordogs.com"
  # subdomain for Argo CD, if you had base set, this would be:
  # argocd.coolwebsitefordogs.com, otherwise you'd need to change to the FQDN
  argo_cd: "argocd"

# metallb IPs used for DNS later (make sure they're not in use)
metallb_address_pool:
#   Example of required full CIDR notation
#   - 192.168.90.01/32

# Used for letsencrypt-staging, to generate certs
email: "coolemailfordogs@verygooddogs.net"

# Use the external secrets provider with gitlab
external_secrets:
  gitlab:
    # going to be deprecated soon in favor of using another password manager
    # token from here: https://gitlab.com/-/profile/personal_access_tokens
    access_token: "kjdfsk758934fkldsafds"
    namespace: "nextcloud"

log:
  # logging level, Options: debug, info, warn, error
  level: "info"
  # path of file to log to
  # file: "./smol-k8s-log.log"
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
