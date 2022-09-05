---
layout: default
title: Quickstart
description: "Smol K8s Homelab Quickstart"
nav_order: 2
permalink: /quickstart
---

## Quickstart for `smol-k8s-homelab.py`
This is aimed at being a much more scalable experience, but is still being worked on. So far, it works for k3s and kind.

### Pre-Req
- Have Python 3.9 or higher installed as well as pip3
- [brew](https://brew.sh)
- **:bell: change the values in `config_sample.yml` to your own**
- Have internet access.

```bash
# Make sure you have brew installed (https://brew.sh)
brew bundle --file=./deps/Brewfile

# install the requirements
pip3 install -r ./deps/requirements.txt

# change the values in config_sample.yml to your own values then rename it
mv config_sample.yml config.yml

# test to make sure the script loads
./smol-k8s-homelab.py --help
```

The help should return this:
```bash
usage: smol-k8s-homelab.py [-h] [-a] [-d] [-e] [-f FILE] [-k] [-p] [-s] k8s

Quickly install a k8s distro for a homelab setup. Installs k3s with metallb, nginx-ingess-controller, cert-manager, and argocd

positional arguments:
  k8s                   distribution of kubernetes to install: k3s or kind. k0s coming soon

optional arguments:
  -h, --help            show this help message and exit
  -a, --argo            Install Argo CD as part of this script, defaults to False
  -d, --delete          Delete the existing cluster, REQUIRES -k/--k8s [k3s|kind]
  -e, --external_secret_operator
                        Install the external secrets operator to pull secrets from somewhere else, so far only supporting gitlab
  -f FILE, --file FILE  Full path and name of yml to parse, e.g. -f /tmp/config.yml
  -k, --k9s             Run k9s as soon as this script is complete, defaults to False
  -p, --password_manager
                        Store generated admin passwords directly into your password manager. Right now, this defaults to Bitwarden and
                        requires you to input your vault password to unlock the vault temporarily.
  -s, --sealed_secrets  Install bitnami sealed secrets, defaults to False
```

## Install a distro of k8s with smol-k8s-homelab.py
Currently only being tested with k3s and kind, but soon you can do other distros listed above. In the meantime, use the tutorial above for k0s.
```bash
# you can replace k3s with kind
./smol-k8s-homelab.py k3s
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
```
# include external .bashrc_k8s if it exists
if [ -f $HOME/.bashrc_k8s ]; then
    . $HOME/.bashrc_k8s
fi
```

### Uninstall distro with python script
```bash
# you can replace k3s with kind
./smol-k8s-homelab.py k3s --delete
```
