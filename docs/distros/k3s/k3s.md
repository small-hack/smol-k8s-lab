---
layout: default
title: K3s
description: "K3s"
parent: K8s Distros
has_children: true
permalink: /distros/k3s
---

# k3s
[K3s](https://k3s.io/) is packaged as a single <50MB binary that reduces the dependencies and steps needed to install, run and auto-update a production Kubernetes cluster. Optimized for ARM Both ARM64 and ARMv7 are supported with binaries and multiarch images available for both.

## Troubleshooting
### Default directory for Persistent Volumes
Where is your persistent volume data? If you used the local path provisioner it is here:
`/var/lib/rancher/k3s/storage`
