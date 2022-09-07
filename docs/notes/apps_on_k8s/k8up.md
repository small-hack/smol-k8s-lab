---
layout: default
title: K8up
description: "Quick notes on K8up"
grand_parent: Notes
parent: Apps on K8s
permalink: /notes/apps/k8up
---

## K8up
K8up is a kubernetes app that utilizes [Restic](https://restic.net/) to create backups of persistent volume claims to object stores like S3, MinIO, and Backblaze B2.

My work with k8up spans across a couple of repos. On github, I setup [k8s-backups-tutorial](https://github.com/jessebot/k8s-backups-tutorial), and I've also contributed a tiny bit to k8up directly in the form of [minor commits](https://github.com/jessebot/argo-example#argocd) to help with Backblaze B2 support.

In addition to stuff on GitHub, I also have some work using argocd to deploy k8up:

- [argocd repo with k8up template](https://gitlab.com/vleermuis_tech/goobernetes/argocd/-/blob/main/templates/k8up.yaml)
- [k8up repo with argocd template](https://gitlab.com/vleermuis_tech/goobernetes/k8up)
- [Nextcloud backup example](https://gitlab.com/vleermuis_tech/goobernetes/nextcloud/-/tree/main/deps/k8up_backups)

### API Docs

The full API docs are [here](https://doc.crds.dev/github.com/k8up-io/k8up@v2.3.0).

- [One time Backups](https://doc.crds.dev/github.com/k8up-io/k8up/k8up.io/Backup/v1@v2.3.0)
- [Scheduled Backups](https://doc.crds.dev/github.com/k8up-io/k8up/k8up.io/Schedule/v1@v2.3.0)
- [Restores](https://doc.crds.dev/github.com/k8up-io/k8up/k8up.io/Backup/v1@v2.3.0)
