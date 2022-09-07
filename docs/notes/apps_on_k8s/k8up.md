---
layout: default
title: K8up
description: "Quick notes on K8up"
grand_parent: Notes
parent: Apps on K8s
permalink: /notes/apps/k8up
---

## K8up - Restic backups for k8s

My work with k8up spans across a couple of repos. On github, I setup [k8s-backups-tutorial](https://github.com/jessebot/k8s-backups-tutorial), and I've also contributed a tiny bit to k8up directly in the form of [minor commits](https://github.com/jessebot/argo-example#argocd) to help with Backblaze B2 support.

In addition to stuff on GitHub, I also have some work using argocd to deploy k8up:

- [argocd repo with k8up template](https://gitlab.com/vleermuis_tech/goobernetes/argocd/-/blob/main/templates/k8up.yaml)
- [k8up repo with argocd template](https://gitlab.com/vleermuis_tech/goobernetes/k8up)
- [Nextcloud backup example](https://gitlab.com/vleermuis_tech/goobernetes/nextcloud/-/tree/main/deps/k8up_backups)
