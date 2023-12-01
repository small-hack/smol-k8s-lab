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

`smol-k8s-lab` cannot function without at least the following installed:

- [Python](https://www.python.org/downloads/) 3.11 or higher
- [`pip`](https://pip.pypa.io/en/stable/installation/)
- [`kubectl`](https://kubernetes.io/docs/tasks/tools/)
- [`helm`](https://helm.sh/docs/intro/install/)
- [`argocd`](https://argo-cd.readthedocs.io/en/stable/cli_installation/)
- Internet access

### Optional

All of these are not Required for core functionality of `smol-k8s-lab`, but they greatly enhance the experience, so they are still recommended.

- [brew](https://brew.sh) - If installed, we can install all prerequisites for you (except python/pip, because you need those to run `smol-k8s-lab`)
- [`docker`](https://docs.docker.com/engine/install/) - needed for k3d, kind, and installing the mastodon app
- [`bw`](https://bitwarden.com/help/cli/#download-and-install) (only if you want to use Bitwarden to store your passwords)
- [`k3d`](https://k3d.io/v5.6.0/#installation) (only if you want to use `k3d`)
- [`k9s`](https://k9s.io) - only if you want a k8s TUI for viewing an already installed cluster
- [`kind`](https://kind.sigs.k8s.io/docs/user/quick-start/#installation) (only if you want to use `kind`)
- [`mc`](https://min.io/docs/minio/linux/reference/minio-mc.html#install-mc) (only if you want `smol-k8s-lab` to create MinIO users and buckets for you)

## Install via `pip`

!!! Note 
    `smol-k8s-lab` is only tested on Debian, Ubuntu, and macOS. It may run on other Linux distros and even WSL, but we do not actively test them at this time.


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
