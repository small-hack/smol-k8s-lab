## ☁️ *smol k8s lab* 🧸

A project aimed at getting up and running **quickly** with slimmer k8s distros in one small command line tool.

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
- [<img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/icons/k0s-logo.svg" width="32">&nbsp;k0s](https://k0sproject.io/)

We tend to test first on k3s and then kind.


### Stack We Install on K8s

|           Application           |                      Description                      |
|:-------------------------------:|:------------------------------------------------------|
| 🐄</br>[Local Path Provisioner] | Default simple local file storage for persistent data |
| [<img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/icons/metallb_icon.png" width="32px" alt="metallb logo, blue arrow pointing up, with small line on one leg of arrow to show balance">][metallb]</br> [metallb] | loadbalancer for metal, since we're mostly selfhosting |
| [<img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/icons/nginx.ico" width="32px" alt="nginx logo, white letter N with green background">][nginx-ingress]</br>[nginx-ingress] | The ingress controller allows access to the cluster remotely, needed for web traffic |
| [<img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/icons/cert-manager_icon.png" width="32px" alt="cert manager logo">][cert-manager]</br>[cert-manager] | For SSL/TLS certificates |
| [<img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/icons/k9s_icon.png" alt="k9s logo, outline of dog with ship wheels for eyes" width="32px">][k9s]</br>[k9s] | Terminal based dashboard for kubernetes |

**Current versions**
cert-manager  v1.10.1
ingress-nginx 4.4.0


#### Optionally installed

| Application/Tool | Description |
|:----------------:|:------------|
| [<img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/icons/eso_icon.png" width="32" alt="ESO logo, outline of robot with astricks in a screen in it's belly">][ESO]</br>[ESO]  | external-secrets-operator integrates external secret management systems like GitLab|
| [<img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/icons/argo_icon.png" width="32" alt="argo CD logo, an organer squid wearing a fishbowl helmet">][Argo CD]</br>[Argo CD] | Gitops - Continuous Deployment |
| [<img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/icons/kyverno_icon.png"  width="32" alt="kyvero logo">][Kyverno]</br>[Kyverno] | Kubernetes native policy management to enforce policies on k8s resources |

**Current versions**
argo-cd          5.16.2
external-secrets 0.6.1

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
This is still in later alpha, as we figure out all the distros we want to support,
and pin all the versions, but if you'd like to contribute or just found a :bug:,
feel free to open an issue (or pull request), and we'll take a look! We'll try
to get back to you asap!

## Contributors

<!-- readme: contributors -start -->
<table>
<tr>
    <td align="center">
        <a href="https://github.com/jessebot">
            <img src="https://avatars.githubusercontent.com/u/2389292?v=4" width="100;" alt="jessebot"/>
            <br />
            <sub><b>JesseBot</b></sub>
        </a>
    </td>
    <td align="center">
        <a href="https://github.com/cloudymax">
            <img src="https://avatars.githubusercontent.com/u/84841307?v=4" width="100;" alt="cloudymax"/>
            <br />
            <sub><b>Max!</b></sub>
        </a>
    </td></tr>
</table>
<!-- readme: contributors -end -->

<!-- link references -->
[metallb]: https://github.io/metallb/metallb "metallb"
[Local Path Provisioner]: https://github.com/rancher/local-path-provisioner
[nginx-ingress]: https://github.io/kubernetes/ingress-nginx
[cert-manager]: https://cert-manager.io/docs/
[k9s]: https://k9scli.io/topics/install/

[ESO]: https://external-secrets.io/v0.5.9/
[Argo CD]: https://github.io/argoproj/argo-helm
[Kyverno]: https://github.com/kyverno/kyverno/
