---
layout: default
title: Notes
description: "Notes that didn't fit anywhere else"
has_children: true
permalink: /notes
---

# Misc Notes

### ArgoCD
Want to get started with argocd? If you've installed it via smol_k8s_homelab, then you can jump to here:
https://github.com/jessebot/argo-example#argo-via-the-gui

Otherwise, if you want to start from scratch, start here: https://github.com/jessebot/argo-example#argocd

### K3s persistent data
Where is your persistent volume data? If you used the local path provisioner it is here:
`/var/lib/rancher/k3s/storage`
