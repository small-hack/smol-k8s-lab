<h2 align="center">
  <img
    src="https://raw.githubusercontent.com/catppuccin/catppuccin/main/assets/misc/transparent.png"
    height="30"
    width="0px"
  />
smol k8s lab 🧸
</h2>

<p align="center">
  <a href="https://github.com/jessebot/smol-k8s-lab/releases">
    <img src="https://img.shields.io/github/v/release/jessebot/smol-k8s-lab?style=plastic&labelColor=484848&color=3CA324&logo=GitHub&logoColor=white">
  </a>
</p>

A tool to get up and running **quickly** with slimmer k8s distros on your local machine. Also helpful for benchmarking various k8s distros! :)

<p align="center">
  <a href="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/screenshots/help_text.svg">
      <img src="./docs/screenshots/help_text.svg" alt="Output of smol-k8s-lab --help after cloning the directory and installing the prerequisites.">
  </a>
</p>


## Getting Started

### Installation
If you've already got Python3.11 and brew installed, you should be able to:

```bash
# install the CLI
pip3.11 install smol-k8s-lab

# Check the help menu before proceeding
smol-k8s-lab --help
```

### Configuration
We've got a [Quickstart guide](https://small-hack.github.io/smol-k8s-lab/quickstart) for you to jump right in :)

## Under the hood
Note: this project is not officially afilliated with any of the below tooling or applications.

### Supported k8s distributions
We always install the latest version of kubernetes that is available from the distro's startup script.

|  Distro    |         Description              |
|:----------:|:------------------------------------------------------|
| [<img src="https://raw.githubusercontent.com/small-hack/smol-k8s-lab/main/docs/icons/k0s-logo.svg" width="32">][k0s] <br /> [k0s] | Simple, Solid & Certified Kubernetes Distribution |
| [<img src="https://raw.githubusercontent.com/small-hack/smol-k8s-lab/main/docs/icons/k3s_icon.ico" width="26">][k3s] <br /> [k3s] | The certified Kubernetes distribution built for IoT & Edge computing |
| [<img src="https://raw.githubusercontent.com/small-hack/smol-k8s-lab/main/docs/icons/kind_icon.png" width="32">][KinD] <br /> [KinD] | kind is a tool for running local Kubernetes clusters using Docker container “nodes”. kind was primarily designed for testing Kubernetes itself, but may be used for local development or CI. |

We tend to test first on k3s first, then the other distros.

### Stack We Install on K8s
Version is the helm chart version, or manifest version.

|           Application           |    Version    |                      Description                      |
|:-------------------------------:|:-------------:|:------------------------------------------------------|
| 🐄 <br /> [Local Path Provisioner] |    latest  | [**k3s only**] Default simple local file storage for persistent data |
| [<img src="https://raw.githubusercontent.com/small-hack/smol-k8s-lab/main/docs/icons/metallb_icon.png" width="32px" alt="metallb logo, blue arrow pointing up, with small line on one leg of arrow to show balance">][metallb] <br /> [metallb] | 0.13.10 | loadbalancer for metal, since we're mostly selfhosting |
| [<img src="https://raw.githubusercontent.com/small-hack/smol-k8s-lab/main/docs/icons/nginx.ico" width="32px" alt="nginx logo, white letter N with green background">][nginx-ingress] <br /> [nginx-ingress] | 4.7.1 | The ingress controller allows access to the cluster remotely, needed for web traffic |
| [<img src="https://raw.githubusercontent.com/small-hack/smol-k8s-lab/main/docs/icons/cert-manager_icon.png" width="32px" alt="cert manager logo">][cert-manager] <br /> [cert-manager] | 1.12.3 | For SSL/TLS certificates |


#### Optionally installed

| Application/Tool |    Version    | Description |
|:----------------:|:-------------:|:------------|
| [<img src="https://raw.githubusercontent.com/small-hack/smol-k8s-lab/main/docs/icons/eso_icon.png" width="32" alt="ESO logo, outline of robot with astricks in a screen in it's belly">][ESO] <br /> [ESO] | 0.9.1 | external-secrets-operator integrates external secret management systems like GitLab|
| [<img src="https://raw.githubusercontent.com/small-hack/smol-k8s-lab/main/docs/icons/argo_icon.png" width="32" alt="argo CD logo, an organer squid wearing a fishbowl helmet">][Argo CD] <br /> [Argo CD] | 5.42.1 | Gitops - Continuous Deployment |
| [<img src="https://raw.githubusercontent.com/small-hack/smol-k8s-lab/main/docs/icons/kyverno_icon.png"  width="32" alt="kyvero logo">][Kyverno] <br /> [Kyverno] | latest | Kubernetes native policy management to enforce policies on k8s resources |
| [<img src="https://raw.githubusercontent.com/small-hack/smol-k8s-lab/main/docs/icons/keycloak_icon.png"  width="32" alt="keycloak logo">][Keycloak] <br /> [KeyCloak] | 16.0.2 | Self hosted IAM/Oauth2 solution |
| [<img src="https://raw.githubusercontent.com/small-hack/smol-k8s-lab/main/docs/icons/k9s_icon.png" alt="k9s logo, outline of dog with ship wheels for eyes" width="32px">][k9s]</br>[k9s] | latest | Terminal based dashboard for kubernetes |


### Tooling Used for the CLI itself and interface
smol-k8s-lab is written in Python and built and published using [Poetry]. You can check out the `pyproject.toml` for the versions of each library we install below:

- [rich] (this is what makes all the pretty formatted text)
- [PyYAML] (to handle the k8s yamls and configs)
- [bcrypt] (to pass a password to argocd and automatically update your Bitwarden)
- [click] (handles arguments for the CLI)

We also utilize the [Bitwarden cli], for a password manager so you never have to see/know your argocd password.


## Troubleshooting
If you're stuck, checkout the [Notes](https://jessebot.github.io/smol-k8s-lab/notes) to see if we also got stuck on the same thing at some point :) Under each app or tool, we'll have notes on how to learn more about it, as well as any errors we've already battled.


# Status
This is still in later alpha, as we figure out all the apps and distros we want to support, and pin all the versions, but if you'd like to contribute or just found a :bug:, feel free to open an issue (or pull request), and we'll take a look! We'll try to get back to you asap!

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

## And more!

Want to get started with argocd? If you've installed it via smol-k8s-lab, then you can jump [here](https://github.com/jessebot/argo-example#argo-via-the-gui). Otherwise, if you want to start from scratch, start [here](https://github.com/jessebot/argo-example#argocd)

<!-- k8s distro link references -->
[k3s]: https://k3s.io/
[KinD]: https://kind.sigs.k8s.io/
[k0s]: https://k0sproject.io/

<!-- k8s apps link references -->
[metallb]: https://github.io/metallb/metallb "metallb"
[Local Path Provisioner]: https://github.com/rancher/local-path-provisioner
[nginx-ingress]: https://github.io/kubernetes/ingress-nginx
[cert-manager]: https://cert-manager.io/docs/

<!-- k8s optional apps link references -->
[ESO]: https://external-secrets.io/v0.8.1/
[Argo CD]: https://github.io/argoproj/argo-helm
[Kyverno]: https://github.com/kyverno/kyverno/
[Keycloak]: https://github.com/bitnami/charts/tree/main/bitnami/keycloak/templates

<!-- k8s tooling reference -->
[k9s]: https://k9scli.io/topics/install/

<!-- smol-k8s-lab dependency lib link references -->
[Poetry]: https://python-poetry.org/
[rich]: https://github.com/Textualize/richP
[PyYAML]: https://pyyaml.org/
[bcrypt]: https://pypi.org/project/bcrypt/
[click]: https://pypi.org/project/click/
[Bitwarden cli]: https://bitwarden.com/help/cli/
