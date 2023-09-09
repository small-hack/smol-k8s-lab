---
layout: default
title: Kubectl
description: "Notes on Kubectl, the default cli for k8s"
parent: Toolbox
permalink: /toolbox/kubectl
---

# Kubectl
[`kubectl`](https://kubernetes.io/docs/reference/kubectl/kubectl/) is the default CLI for Kuberenetes. I use it mostly to apply things directly, or within simple BASH scripts for automation.

## Krew
[`krew`](https://krew.sigs.k8s.io/) is a package manager for kubectl plugins.

### Installation
Check out the current installation docs [here](https://krew.sigs.k8s.io/docs/user-guide/setup/install/), but you should be able to run (on macOS/Linux):

```bash
brew install krew
```

### Installing Plugins with Krew
Example for installing the ctx plugin:

```bash
kubectl krew install ctx
```

### Plugins I actually use

| Plugin | Why/What |
|:---:|:---|
| ctx     | kubeconfig context switching to switch to other clusters |
| ns      | switch to different namespaces in the current kubeconfig cluster/context |
| example | outputs example yaml files for a given cluster resource |
| deprecations | check which cluster resources are deprecated/will be deprecated soon |

todo: fill these in with ascinemas.
Check out the examples below to see how they're used.

#### ns

#### example

#### deprecations
