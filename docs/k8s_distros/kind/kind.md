---
layout: default
title: Kind
description: "Kind"
parent: K8s Distros
has_children: true
permalink: /distros/kind
---

# KinD (kubernetes in docker)
[Kind](https://kind.sigs.k8s.io/) is a tool for running local Kubernetes clusters using Docker container "nodes". kind was primarily designed for testing Kubernetes itself, but may be used for local development or CI. If you have go ( 1.17+) and docker installed, this should be all you need to get started, in theory:

```bash
go install sigs.k8s.io/kind@v0.15. && kind create cluster
```
