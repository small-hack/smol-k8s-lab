---
layout: default
title: K0s
description: "K0s"
parent: K8s Distros
has_children: true
permalink: /distros/k0s
---

# K0s

K0s is a kubernetes distribution by [Mirantis]. It's a distributed as a single binary with no dependancies aside from the kernel. It's batteries-included and open-source. Some of the key features listed on the [K0s github page] have been summarized below:

- Install as a single node, multiple nodes, airgap, or container
- Min Specs: 1 vCore 1GB RAM
- Vanilla upstream Kubernetes (with no changes)
- Kube-Router is the default CNI, Calico is offered as preconfigured alternative.
- Containerd is the default CRI
- Supportsall CSI's
- Uses etcd for multi-node clusters, SQLite for single node clusters (MySQL, and PostgreSQL also supported)
- Supports x86-64, ARM64 and ARMv7

K0s stores its config in `/var/lib/k0s` - [Source]

<!--  Link References -->
[Source]: https://docs.k0sproject.io/v1.25.4+k0s.0/cli/k0s_config/?h=config "K0s config documentation"
[Mirantis]: https://www.mirantis.com/ "Mirantis - the Lens and Docker people"
[K0s]: https://k0sproject.io/ "Homepage for the K0s project"
[K0s github page]: https://github.com/k0sproject/k0s "Official Github page for the K0s project" 
