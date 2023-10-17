---
layout: default
parent: Intro
title: Installation
description: "smol-k8s-lab installation guide"
nav_order: 2
permalink: /install
---

## Prerequisites

### Required

- [Python](https://www.python.org/downloads/) 3.11 or higher
- [`pip`](https://pip.pypa.io/en/stable/installation/)
- [`kubectl`](https://kubernetes.io/docs/tasks/tools/)
- [`helm`](https://helm.sh/docs/intro/install/)
- [`k3d`](https://k3d.io/v5.6.0/#installation) (only if you want to use `k3d`)
- [`kind`](https://kind.sigs.k8s.io/docs/user/quick-start/#installation) (only if you want to use `kind`)
- Internet access

### Optional
- [brew](https://brew.sh) - If installed, we can install `kubectl`, `k3d`, `kind`, and `helm` for you :)

## Install via `pip`

!!! Note 
    `smol-k8s-lab` is only tested Debian, Ubuntu, and macOS. It may run on other Linux distros and even WSL, but it is not tested on those systems. 


`pip` is probably the best way to install `smol-k8s-lab`, but you can also probably use `pipx`:

```bash
# smol-k8s-lab will also work on newer python versions
pip3.11 install smol-k8s-lab
```

If all was successful, you should be able to run:

```bash
# this will show the help text
smol-k8s-lab --help
```

<details>
  <summary>Help text example</summary>

  <a href="/images/screenshots/help_text.svg">
    <img src="/images/screenshots/help_text.svg" alt="Output of smol-k8s-lab --help after cloning the directory and installing the prerequisites.">
  </a>

</details>

If the help text shows up, you most likely are good to go :) Check out the respectively [CLI](/cli) and [TUI](/tui) sections to learn more!
