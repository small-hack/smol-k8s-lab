---
layout: default
title: Postgresql
description: "Quick notes on hosting postgresql on Kubernetes"
grand_parent: Notes
parent: Apps running on K8s
permalink: /notes/apps/postgresql
---

## Deploy PostgreSQL
Do this step only if you need to have postgres as a standalone helm chart.

This only needs to be done once locally
```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm install postgres bitnami/postgres --values helm/values.yml
```

## Backups with k8up
This tutorial will also assume you're using k8up for backups of Persistent Volumes and you make sure those are set up properly by following [this guide](https://github.com/jessebot/k8s-backups-tutorial).
