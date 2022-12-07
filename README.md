## ☁️ *smol k8s lab* 🧸

This is aimed at getting up and running quickly with mostly smaller k8s distros in one small command line script.

<p align="center">
  <a href="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/screenshots/help_text.svg">
      <img src="./docs/screenshots/help_text.svg" alt="Output of smol-k8s-lab --help after cloning the directory and installing the prerequisites.">
  </a>
</p>


## Docs

### Quick Start
If you've already got Python3.11 and brew installed, you should be able to:

```bash
pip3.11 install smol-k8s-lab
```

We've also got a [Quickstart guide](https://jessebot.github.io/smol-k8s-lab/quickstart) for you to jump right in!

There's also full tutorials to manually set up different distros in the [docs we maintain](https://jessebot.github.io/smol-k8s-lab/distros) as well as BASH scripts for basic automation of each k8s distro in:

`./distro/{NAME_OF_K8S_DISTRO}/bash_full_quickstart.sh`

## Under the hood
### Currently supported k8s distros

- [<img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/icons/k3s_icon.ico" width="26">&nbsp;&nbsp;k3s](https://k3s.io/)
- [<img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/icons/kind_icon.png" width="32">&nbsp;KinD](https://kind.sigs.k8s.io/)

We tend to test first on k3s and then kind.

We're working on k0s next :)


### Stack We Install on K8s

|    Application      | What is it? |
|:--------------------|:------------|
| &nbsp;🐄 &nbsp;[Local Path Provisioner](https://github.com/rancher/local-path-provisioner) | Default simple local file storage for persistent data |
| [<img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/icons/metallb_icon.png" width="32" alt="metallb logo, blue arrow pointing up, with small line on one leg of arrow to show balance">&nbsp; metallb](https://github.io/metallb/metallb) | loadbalancer for metal, since we're mostly selfhosting |
| [<img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/icons/nginx.ico" width="32" alt="nginx logo, white letter N with green background">&nbsp; nginx-ingress](https://github.io/kubernetes/ingress-nginx) | The ingress controller allows access to the cluster remotely, needed for web traffic |
| [<img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/icons/cert-manager_icon.png" width="32" alt="cert manager logo"> &nbsp;cert-manager](https://cert-manager.io/docs/) | For SSL/TLS certificates |
| [<img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/icons/k9s_icon.png" alt="k9s logo, outline of dog with ship wheels for eyes" width="32"> &nbsp;k9s](https://k9scli.io/topics/install/) | Terminal based dashboard for kubernetes |


#### Optionally installed

| Application/Tool | What is it? |
|:-----------------|:------------|
| [<img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/icons/eso_icon.png" width="32" alt="ESO logo, outline of robot with astricks in a screen in it's belly">&nbsp; ESO](https://external-secrets.io/v0.5.9/) | external-secrets-operator integrates external secret management systems like GitLab|
| [<img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/icons/argo_icon.png" width="32" alt="argo CD logo, an organer squid wearing a fishbowl helmet">&nbsp; Argo CD](https://github.io/argoproj/argo-helm) | Gitops - Continuous Deployment |
| [<img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/icons/kyverno_icon.png"  width="32" alt="kyvero logo">&nbsp; Kyverno](https://github.com/kyverno/kyverno/) | Kubernetes native policy management to enforce policies on k8s resources |

If you install argocd, and you use bitwarden, we'll generate an admin password and automatically place it in your vault if you pass in the `-p` option. Curently only works with Bitwarden.

Want to get started with argocd? If you've installed it via smol-k8s-lab, then you can jump [here](https://github.com/jessebot/argo-example#argo-via-the-gui). Otherwise, if you want to start from scratch, start [here](https://github.com/jessebot/argo-example#argocd)


### Tooling Used for the script itself and interface

[![made-with-python](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue)](https://www.python.org/)

- rich (this is what makes all the pretty formatted text)
- PyYAML (to handle the k8s yamls and configs)
- bcrypt (to pass a password to argocd and automatically update your bitwarden)
- click (handles arguments for the script)


## Troubleshooting
If you're stuck, checkout the [Notes](https://jessebot.github.io/smol-k8s-lab/notes) to see if we also got stuck on the same thing at some point :) Under each app or tool, we'll have notes on how to learn more about it, as well as any errors we've already battled.


## Other Notes
Check out the [`optional`](optional) directory for quick examples on apps this script does not default install.

e.g. for postgres, go to [`./optional/postgres`](./optional/postgres)

# Status
This is still in beta, as we figure out all the distros we want to support,
and pin all the versions, but if you'd like to contribute or just found a :bug:,
feel free to open an issue (or pull request), and we'll take a look! We'll try
to get back to you asap!

## Collaborators
<!-- readme: collaborators -start -->
<!-- readme: collaborators -end -->

## TODO
- Configure base policies for Kyverno
- bitwarden: check local env vars for password or api key
- look into https://kubesec.io/
