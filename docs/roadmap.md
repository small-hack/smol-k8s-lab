---
layout: default
title: RoadMap
description: "roadmap for smol-k8s-lab"
permalink: /roadmap
---

## RoadMap

Here we'll document our general task list going forward.

#### Major Features

- Support OpenBao in place of Bitwarden and the Appset Secrets Plugin
- Support setting up an initial cluster via SSH (this would prevent you needing to log into a node to initially setup k8s before you can manage it remotely as normal via smol-k8s-lab)
- Make the bitwarden feature a generic password manager feature. See [small-hack/smol-k8s-lab:issues#45](https://github.com/small-hack/smol-k8s-lab/issues/45)
  - support local keyring
  - support 1password
  - support OpenBao
- improve [`make_screenshots.py`](https://github.com/small-hack/smol-k8s-lab/blob/main/smol_k8s_lab/tui/make_screenshots.py). See [small-hack/smol-k8s-lab:issue#101](https://github.com/small-hack/smol-k8s-lab/issues/101)
  - handle both existing and non-existing clusters
  - create gif with screenshots for the README, docs, and pypi
- Thorough Diagrams, see: [small-hack/smol-k8s-lab:issues#34](https://github.com/small-hack/smol-k8s-lab/issues/34):
  - Diagram showing each phase of smol-k8s-lab
  - Diagram describing backups
  - Diagram describing restores
- support disabling backups
- support a generic backup section for all custom apps
- support a security scan of all k8s resources
- update docs for our monitoring stack

#### Minor Features

- Support a dropdown menu in the TUI for sensitive values to select from environment variable or bitwarden
- Support a dropdown menu in the TUI for restic snapshot IDs to choose from, maybe this could also have a calendar feature to choose a date?
- Flesh out sensitive values from bitwarden and OpenBao
- Fix the issue where clicking an app on the apps screen causes it to be disabled/enabled. See [Textualize/textual:discussions#4478](https://github.com/Textualize/textual/discussions/4478) for more info.

## Contributing to smol-k8s-lab

If you'd like to help with `smol-k8s-lab`, please see our [contributing doc](https://github.com/small-hack/smol-k8s-lab/blob/main/CONTRIBUTING.md)
