---
layout: default
title: Intro
description: "Smol K8s Homelab Overview"
nav_order: 1
permalink: /
---

# Smol K8s Homelab
We throw local k8s (kubernetes) testing tools in this repo, mainly [`smol-k8s-lab`](./smol-k8s-lab). This project is aimed at getting up and running quickly with mostly smaller k8s distros in one small command line script, but there's also full tutorials to manually set up each distro in the [docs we maintain](https://jessebot.github.io/smol_k8s_homelab/distros) as well as BASH scripts for basic automation of each k8s distro in each directory under `./distro/[NAME OF K8S DISTRO]/bash_full_quickstart.sh`.

## QuickStart
Get started with `smol-k8s-lab` today with our tutorial [here](https://jessebot.github.io/smol_k8s_homelab/quickstart).

### Currently supported k8s distros

- [<img src="https://raw.githubusercontent.com/jessebot/smol_k8s_homelab/main/docs/icons/k3s_icon.ico" width="26">&nbsp;&nbsp;k3s](https://k3s.io/)
- [<img src="https://raw.githubusercontent.com/jessebot/smol_k8s_homelab/main/docs/icons/kind_icon.png" width="32">&nbsp;KinD](https://kind.sigs.k8s.io/)

### Stack We Install on K8s

|    Application      | What is it? |
|:--------------------|:------------|
| &nbsp;🐄 &nbsp;[Local Path Provisioner](https://github.com/rancher/local-path-provisioner) | Default simple local file storage for persistent data |
| [<img src="https://raw.githubusercontent.com/jessebot/smol_k8s_homelab/main/docs/icons/metallb_icon.png" width="32" alt="metallb logo, blue arrow pointing up, with small line on one leg of arrow to show balance">&nbsp; metallb](https://github.io/metallb/metallb) | loadbalancer for metal, since we're mostly selfhosting |
| [<img src="https://raw.githubusercontent.com/jessebot/smol_k8s_homelab/main/docs/icons/nginx.ico" width="32" alt="nginx logo, white letter N with green background">&nbsp; nginx-ingress](https://github.io/kubernetes/ingress-nginx) | The ingress controller allows access to the cluster remotely, needed for web traffic |
| [<img src="https://raw.githubusercontent.com/jessebot/smol_k8s_homelab/main/docs/icons/cert-manager_icon.png" width="32" alt="cert manager logo"> &nbsp;cert-manager](https://cert-manager.io/docs/) | For SSL/TLS certificates |


#### Optionally Installed

| Application/Tool | What is it? |
|:-----------------|:------------| 
| [<img src="https://raw.githubusercontent.com/jessebot/smol_k8s_homelab/main/docs/icons/eso_icon.png" width="32" alt="ESO logo, outline of robot  iwth astricks in a screen in it's belly">&nbsp; ESO](https://external-secrets.io/v0.5.9/) | external-secrets-operator integrates external secret management systems like GitLab|
| [<img src="https://raw.githubusercontent.com/jessebot/smol_k8s_homelab/main/docs/icons/argo_icon.png" width="32" alt="argo CD logo, an organer squid wearing a fishbowl helmet">&nbsp; Argo CD](https://github.io/argoproj/argo-helm) | Gitops - Continuous Deployment |
| [<img src="https://raw.githubusercontent.com/jessebot/smol_k8s_homelab/main/docs/icons/kyverno_icon.png"  width="32" alt="kyvero logo">&nbsp; Kyverno](https://github.com/kyverno/kyverno/) | Kubernetes native policy management to enforce policies on k8s resources |
| [<img src="https://raw.githubusercontent.com/jessebot/smol_k8s_homelab/main/docs/icons/k9s_icon.png" alt="k9s logo, outline of dog with ship wheels for eyes" width="32"> &nbsp;k9s](https://k9scli.io/topics/install/) | Terminal based dashboard for kubernetes |

If you install argocd, and you use bitwarden, we'll generate an admin password and automatically place it in your vault if you pass in the `-p` option. Curently only works with Bitwarden.

Want to get started with argocd? If you've installed it via smol_k8s_homelab, then you can jump [here](https://github.com/jessebot/argo-example#argo-via-the-gui). Otherwise, if you want to start from scratch, start [here](https://github.com/jessebot/argo-example#argocd)


### Port Forwarding
If you want to access an app outside of port forwarding to test, you'll need to make sure your app's ingress is setup correctly and then you'll need to setup your router to port forward 80->80 and 443->443 for your WAN. then setup DNS for your domain if you want the wider internet to access this remotely.

### SSL/TLS

After SSL is working (if it's not, follow the steps in the [cert-manager common error troubleshooting guide](https://cert-manager.io/docs/faq/acme/#common-errors)), you can also change the `letsencrypt-staging` value to `letsencrypt-prod` for any domains you own and can configure to point to your cluster via DNS.

### Troubleshooting
If you're stuck, checkout the [Notes section](https://jessebot.github.io/smol_k8s_homelab/notes) to see if we also got stuck on the same thing at some point :)
