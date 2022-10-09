---
layout: default
title: Quickstart
description: "Smol K8s Homelab Quickstart"
nav_order: 2
permalink: /quickstart
---

## Quickstart for `smol-k8s-lab.py`
This is aimed at being a much more scalable experience, but is still being worked on. So far, it works for k3s and kind.

### Pre-Req
- Have Python 3.10 as well as pip3.10
- [brew](https://brew.sh)
- **:bell: change the values in `config_sample.yml` to your own**
- Have internet access.

```bash
# Make sure you have brew installed (https://brew.sh)
brew bundle --file=./deps/Brewfile

# install the requirements
pip3.10 install -r ./deps/requirements.txt

# change the values in config_sample.yml to your own values then rename it
mv config_sample.yml config.yml

# test to make sure the script loads
./smol-k8s-lab.py --help
```

The help should return this:

<img src="https://raw.githubusercontent.com/jessebot/smol_k8s_homelab/main/docs/screenshots/help_txt.png" width="850" alt="Output of smol-k8s-lab.py --help after cloning the directory and installing the prerequisites.">


## Install a distro of k8s with smol-k8s-lab.py
Currently only being tested with k3s and kind.
```bash
# you can replace k3s with kind
./smol-k8s-lab.py k3s
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
./smol-k8s-lab.py k3s --delete
```
