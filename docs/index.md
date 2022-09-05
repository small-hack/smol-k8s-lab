---
layout: default
title: Intro
description: "Smol K8s Homelab Overview"
nav_order: 1
permalink: /
---

# Smol K8s Homelab
Currently in a beta state. We throw local k8s (kubernetes) testing tools in this repo, mainly [`smol-k8s-homelab.py`](./smol-k8s-homelab.py). This project is aimed at getting up and running quickly with mostly smaller k8s distros in one small command line script, but there's also full tutorials to manually set up each distro in the [docs we maintain](https://jessebot.github.io/smol_k8s_homelab/distros).

## QuickStart
Get started with `smol-k8s-homelab.py` today with our tutorial [here](https://jessebot.github.io/smol_k8s_homelab/quickstart).

### Currently supported k8s distros

| Distro | [smol-k8s-homelab.py](./smol-k8s-homelab.py)| [Quickstart BASH](#quickstart-in-bash) |
|:---:|:---:|:---:|
|[k3s](https://k3s.io/)            | ✅   | [./k3s/bash_full_quickstart.sh](./k3s/bash_full_quickstart.sh) |
|[KinD](https://kind.sigs.k8s.io/) | ✅   | [./kind/bash_full_quickstart.sh](./kind/bash_full_quickstart.sh) |
|[k0s](https://k0sproject.io/)     | soon | soon :3 |


### Stack We Install on K8s
We tend to test first one k3s and then kind and then k0s.

| Application/Tool | What is it? |
|:---:|:---|
| [metallb](https://github.io/metallb/metallb) | loadbalancer for metal, since we're mostly selfhosting |
| [nginx-ingress-controller](https://github.io/kubernetes/ingress-nginx) | Ingress: access to the cluster remotely, needed for web traffic |
| [cert-manager](https://cert-manager.io/docs/) | For SSL/TLS certificates |
| [k9s](https://k9scli.io/topics/install/) | Terminal based dashboard for kubernetes |
| [local path provisioner]() | Default simple local file storage |

### Optionally installed

| Application/Tool | What is it? |
|:-----------:|:--------------| 
| [sealed-secrets](https://github.com/bitnami-labs/sealed-secrets) | Encrypts secrets files so you can check them into git |
| [external-secrets-operator](https://external-secrets.io/v0.5.9/) | integrates external secret management systems like GitLab|
| [argo-cd](https://github.io/argoproj/argo-helm) | Gitops - Continuous Deployment |

#### Other important stuff we install

- [k9s](https://k9scli.io/topics/install/): Terminal based dashboard for kubernetes

If you install argocd, and you use bitwarden, we'll generate an admin password and automatically place it in your vault if you pass in the `-p` option. Curently only works with Bitwarden.


### Port Forwarding
If you want to access an app outside of port forwarding to test, you'll need to make sure your app's ingress is setup correctly and then you'll need to setup your router to port forward 80->80 and 443->443 for your WAN. then setup DNS for your domain if you want the wider internet to access this remotely.

### SSL/TLS

After SSL is working (if it's not, follow the steps in the [cert-manager common error troubleshooting guide](https://cert-manager.io/docs/faq/acme/#common-errors)), you can also change the `letsencrypt-staging` value to `letsencrypt-prod` for any domains you own and can configure to point to your cluster via DNS.


### Remote cluster administration

You can also copy your remote k3s kubeconfig with a little script in `k3s/`:

```bash
# CHANGE THESE TO YOUR OWN DETAILS or not ¯\_(ツ)_/¯
export REMOTE_HOST="192.168.20.2"
export REMOTE_SSH_PORT="22"
export REMOTE_USER="cooluser4dogs"

# this script will totally wipe your kubeconfig :) use with CAUTION
./k3s/get-remote-k3s-yaml.sh
```

### Troubleshooting
If you're stuck, checkout the [Troubleshooting section](https://jessebot.github.io/smol_k8s_homelab/troubleshooting) to see if we also got stuck on it at some point :)
