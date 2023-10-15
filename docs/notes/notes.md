---
layout: default
title: Notes
description: "Notes that didn't fit anywhere else"
has_children: true
permalink: /notes
---

Here's where I dump various notes on different apps you can host on k8s, as well as notes on various tools for kubernetes.

## Port Forwarding
If you want to access an app outside of port forwarding to test, you'll need to make sure your app's ingress is setup correctly and then you'll need to setup your router to port forward 80->80 and 443->443 for your WAN. then setup DNS for your domain if you want the wider internet to access this remotely.

## Helpful links
- The k3s knowledge here is in this [kauri.io self hosting guide](https://kauri.io/#collections/Build%20your%20very%20own%20self-hosting%20platform%20with%20Raspberry%20Pi%20and%20Kubernetes/%2838%29-install-and-configure-a-kubernetes-cluster-w/) is invaluable. Thank you kauri.io.

- This [encrypted secrets in helm charts guide](https://www.thorsten-hans.com/encrypted-secrets-in-helm-charts/) isn't the guide we need, but helm secrets need to be stored somewhere, and vault probably makes sense
