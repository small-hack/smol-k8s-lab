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
- Make the bitwarden feature a generic password manager feature
  - support local keyring
  - support 1password
  - support OpenBao

#### Minor Features

- Support a dropdown menu in the TUI for sensitive values to select from environment variable or bitwarden
- Support a dropdown menu in the TUI for restic snapshot IDs to choose from, maybe this could also have a calendar feature to choose a date?
- Diagram showing each phase of smol-k8s-lab
- Diagram describing backups
- Diagram describing restores
- Flesh out sensitive values from bitwarden and OpenBao

## Contributing to smol-k8s-lab

If you'd like to help with `smol-k8s-lab`, please see our [contributing doc](https://github.com/small-hack/smol-k8s-lab/blob/main/CONTRIBUTING.md)
