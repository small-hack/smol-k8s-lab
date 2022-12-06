---
layout: default
title: Quickstart
description: "Smol K8s Homelab Quickstart"
nav_order: 2
permalink: /quickstart
---

## Quickstart for `smol-k8s-lab`

You should be able to use `pip` to install things after you've got the one time
setup pre-reqs listed below.

<details>
  <summary>One time Pre-Req</summary>
- Python 3.11 (`brew install python3.11`)
- [brew](https://brew.sh)
- Have internet access.

```bash
# install prereqs like brew
./setup.sh
```

</details>

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

The help should return this:

[<img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/screenshots/help_text.svg" alt="Output of smol-k8s-lab --help after cloning the directory and installing the prerequisites.">](https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/screenshots/help_text.svg)

🔔 Then you *Have To* edit the `config_sample.yml` to be your own values:

```yaml
---
domains:
  argo_cd: "argocd.coolwebsitefordogs.com"

# these HAVE to be full CIDR notation
metallb_address_pool:
  - 192.168.90.01/32
  - 192.168.90.02/32
  - 192.168.90.03/32

email: "coolemailfordogs@onlydogs.com"

external_secrets:
  gitlab:
    access_token: "kjdfsk758934fkldsafds"
    namespace: "nextcloud"
```

## Install a distro of k8s with smol-k8s-lab
Currently only being tested with k3s and kind.
```bash
# you can replace k3s with kind
./smol-k8s-lab k3s
```

#### Install some kubectl plugins (Optional)

These together make namespace switching better. Learn more about kubectx + kubens [here](https://github.com/ahmetb/kubectx).

```bash
kubectl krew update
kubectl krew install ctx
kubectl krew install ns
```

To install plugins from my newline-delimited krew file, run:

```bash
kubectl krew install < deps/kubectl_krew_plugins
```

#### Install @jessebot's `.bashrc_k8s` (optional)

You can copy over the rc file for some helpful aliases:

```bash
# copy the file to your home directory
cp deps/.bashrc_k8s ~

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

### Uninstall distro with python script

```bash
# you can replace k3s with kind
./smol-k8s-lab k3s --delete
```
