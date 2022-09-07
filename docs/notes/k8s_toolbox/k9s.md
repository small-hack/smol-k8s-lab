---
layout: default
title: K9s
description: "Notes on K9s, a terminal based dashboard for k8s"
grand_parent: Notes
parent: Toolbox
permalink: /notes/toolbox/k9s
---

## K9s
[K9s](https://k9scli.io/) is a CLI to manager your clusters from the terminal. I personally never deploy the default kubernetes dashboard anymore and instead just use a combination of k9s and kubectl with plugins installed with [krew](https://krew.sigs.k8s.io/).

K9s also has plugins of its own, and integrates with additional k8s tooling, like [Popeye](https://popeyecli.io/), a utility that scans live Kubernetes cluster and reports potential issues with deployed resources and configurations.
