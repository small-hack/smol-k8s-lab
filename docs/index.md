<h1 align="center">
🧸 Smol K8s Lab
</h1>

Leverage Argo CD and slim Kubernetes distributions, like K3s, to create production-like environments via a declarative workflow. Batteries and 🦑 included.

## About

`smol-k8s-lab`'s declarative workflow, CLI, and TUI enable rapid iteration in production-like environments with minimal costs for failure. This makes it ideal for proof-of-concepts, prototyping, and benchmarking Kubernetes applications and distributions. It's also great for home labs, with some common FOSS apps such as Home Assistant, Nextcloud, Matrix, and more!

By default, `smol-k8s-lab` deploys [Argo CD] + [Argo CD Appset Secret Plugin] which enables Argo CD to securely manage your lab via files in [open source Git repos](https://github.com/small-hack/argocd-apps). Additionally, a customized nord-like dark-theme is provided for Argo CD's incredibly useful web-interface.


Consider viewing our very long walk through if you like video walk-throughs (which is a little out of date, but we intend to update it as soon as possible to include new features):

<p align="center">
<iframe width="720" height="480" src="https://www.youtube.com/embed/UdOQM9n5hyU?si=5dDCf2J2Oczhdej3" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>
</p>

Here's the [same video with captions](https://youtu.be/2E9DVJpv440?feature=shared).

### Features

- Deploys [Argo CD](https://github.com/argoproj/argo-cd) by default, so you can manage your entire lab using files in [open source git repos](https://github.com/small-hack/argocd-apps)
  - Argo CD ships with a dashboard with a custom theme 💙
- Specializes in using Bitwarden (though not required) to store sensitive values both in your Bitwwarden vault, and on your cluster as Secrets.
- Manages all your authentication needs centrally using [Zitadel] and [Vouch] 💪
- Supports initialization on a [range of common self-hosted apps](https://small-hack.github.io/smol-k8s-lab/k8s_apps/argocd/) 📱
  - featured initialized apps such as [Zitadel], [Nextcloud](https://small-hack.github.io/smol-k8s-lab/k8s_apps/nextcloud/), [Matrix](https://small-hack.github.io/smol-k8s-lab/k8s_apps/matrix/), and [Home Assistant](https://small-hack.github.io/smol-k8s-lab/k8s_apps/home_assistant/) include [b]backups and restores[/b]!
- Lots o' [docs](https://small-hack.github.io/smol-k8s-lab)

## Getting Started

Please see our [Getting Started guide](https://small-hack.github.io/smol-k8s-lab/installation).

# Under the hood

Note: this project is not officially affiliated with any of the below tooling or applications. We just love open source projects 💙

## Supported k8s distributions
We always install the latest version of Kubernetes that is available from the distro's startup script.

|                                     Distro                                     | Description                                                                                                                                     |
|:------------------------------------------------------------------------------:|:------------------------------------------------------------------------------------------------------------------------------------------------|
|   [<img src="assets/images/icons/k3s_icon.ico" width="26">][k3s] <br /> [k3s]  | The certified Kubernetes distribution built for IoT & Edge computing                                                                            |
|     [<img src="assets/images/icons/k3d.png" width="26">][k3d] <br /> [k3d]     | K3d is k3s in Docker 🐳. <br> In beta!                                                                                                        |
| [<img src="assets/images/icons/kind_icon.png" width="32">][KinD] <br /> [KinD] | kind is a tool for running local Kubernetes clusters using Docker container “nodes”. kind was primarily designed for testing Kubernetes itself. |

We tend to test first on k3s first, then the other distros.

## Default Installed Applications
Version is the helm chart version, or manifest version. See the [Default Applications](/k8s_apps/argocd) tab for more info on each application.

|                                                                                          Application                                                                                          | Description                                                                                      | Initialization Supported |
|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------:|:-------------------------------------------------------------------------------------------------|:------------------------:|
|   [<img src="assets/images/icons/metallb_icon.png" width="32px" alt="metallb logo, blue arrow pointing up, with small line on one leg of arrow to show balance">][metallb] <br /> [metallb]   | Loadbalancer and IP Address pool manager for metal                                               |            ✅            |
|                     [<img src="assets/images/icons/nginx.ico" width="32px" alt="nginx logo, white letter N with green background">][ingress-nginx] <br /> [ingress-nginx]                     | The ingress-nginx controller allows access to the cluster remotely, needed for web traffic       |            ❌            |
|                                [<img src="assets/images/icons/cert-manager_icon.png" width="32px" alt="cert manager logo">][cert-manager] <br /> [cert-manager]                               | For SSL/TLS certificates                                                                         |            ✅            |
|                      [<img src="assets/images/icons/argo_icon.png" width="32" alt="argo CD logo, an organer squid wearing a fishbowl helmet">][Argo CD] <br /> [Argo CD]                      | Gitops - Continuous Deployment                                                                   |            ✅            |
| [<img src="assets/images/icons/argo_icon.png" width="32" alt="argo CD logo, an organer squid wearing a fishbowl helmet">][Argo CD Appset Secret Plugin] <br /> [Argo CD Appset Secret Plugin] | Gitops - Continuous Deployment                                                                   |            ✅            |
|                      [<img src="assets/images/icons/eso_icon.png" width="32" alt="ESO logo, outline of robot with astricks in a screen in it's belly">][ESO] <br /> [ESO]                     | external-secrets-operator integrates external secret management systems like Bitwarden or GitLab |            ❌            |
|                            [<img src="assets/images/icons/eso_icon.png" width="32" alt="ESO logo, again">][Bitwarden ESO Provider] <br /> [Bitwarden ESO Provider]                            | Bitwarden external-secrets-operator provider                                                     |            ✅            |
|                              [<img src="assets/images/icons/zitadel.png" width="32" alt="Zitadel logo, an orange arrow pointing left">][ZITADEL] <br /> [ZITADEL]                             | An identity provider and OIDC provider to provide SSO                                            |            ✅            |
|                                    [<img src="assets/images/icons/vouch.png" width="32" alt="Vouch logo, the letter V in rainbow ">][Vouch] <br /> [Vouch]                                    | Vouch proxy allows you to secure web pages that lack authentication e.g. prometheus              |            ✅            |
|                             [<img src="assets/images/icons/prometheus.png" width="32" alt="Prometheus logo, a torch">][Prometheus Stack] <br /> [Prometheus Stack]                            | Prometheus monitoring and logging stack using [loki]/[promtail], [alert manager], and [grafana]  |            ✅            |


Minor Notes:

>All Default Applications can be disabled through your `~/.config/smol-k8s-lab/config.yaml` file, **except** Argo CD. You can still choose not to install it, but if not installed, smol-k8s-lab will <i>only</i> install: metallb, nginx-ingress, and cert-manager</sub>


## Optionally Installed Applications

|                                                                                                                          Application/Tool                                                                                                                          | Description                                                                                                                               | Initialization Supported |
|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------:|:------------------------------------------------------------------------------------------------------------------------------------------|:------------------------:|
|                                                                          [<img src="assets/images/icons/cilium.png"  width="32" alt="cilium logo">][Cilium] <br /> [Cilium]<sup>demo</sup>                                                                         | Kubernetes netflow visualizer and policy editor                                                                                           |            ✅            |
| [<img src="assets/images/icons/home_assistant_icon.png"  width="32" alt="home assistant logo, which is a small blue house with three white tracers inside of it, making it appear as though the home is a circuit board">][Home Assistant] <br /> [Home Assistant] | Home Assistant, a self hosted, at home IoT management solution.                                                                           |            ✅            |
|                                                                     [<img src="assets/images/icons/kyverno_icon.png"  width="32" alt="kyvero logo">][Kyverno] <br /> [Kyverno]<sup>alpha</sup>                                                                     | Kubernetes native policy management to enforce policies on k8s resources                                                                  |            ❌            |
|                                                                                  [<img src="assets/images/icons/kepler.png" width="32" alt="kepler logo">][kepler] <br /> [kepler]                                                                                 | Kepler (Kubernetes Efficient Power Level Exporter) uses eBPF to probe energy-related system stats and exports them as Prometheus metrics. |            ✅            |
|                                         [<img src="assets/images/icons/k8up.png" width="32" alt="k8up logo, a minimalist logo of a small blue hill with line starting the right going into the hill">][k8up] <br /> [k8up]                                         | Backups operator using [restic] to backup to s3 endpoints                                                                                 |            ✅            |
|                                                  [<img src="assets/images/icons/k8tz.png" width="32" alt="k8tz logo, the k8s logo but with a watch in the center instead of the ship wheel">][k8tz] <br /> [k8tz]                                                  | Timezone environment variable injector for pods and cronjobs                                                                              |            ✅            |
|                                                                  [<img src="assets/images/icons/netmaker-icon.png" width="32" alt="netmaker logo, a purple letter N">][Netmaker] <br /> [Netmaker]                                                                 | Netmaker is a self hosted vpn management tool that uses Wiregaurd®                                                                                             |            ✅            |
|                                               [<img src="assets/images/icons/nextcloud.png" width="32" alt="nextcloud logo, 3 white circles touching eachother on a blue background">][Nextcloud] <br /> [Nextcloud]                                               | Nextcloud is a self hosted file server                                                                                                    |            ✅            |
|                                                            [<img src="assets/images/icons/mastodon.png" width="32" alt="Mastodon logo, a white M in a purple chat bubble">][Mastodon] <br /> [Mastodon]                                                            | Mastodon is a self hosted federated social media network                                                                                  |            ✅            |
|                                                                                  [<img src="assets/images/icons/matrix.png" width="32" alt="Matrix logo">][matrix] <br /> [matrix]                                                                                 | Matrix is a self hosted chat platform                                                                                                     |            ✅            |
|                                                                [<img src="assets/images/icons/minio.png" width="32" alt="minio logo, a minimalist drawing in red of a crane">][minio] <br /> [minio]                                                               | Self hosted S3 Object Store operator                                                                                                      |            ✅            |
|                                                                           [<img src="assets/images/icons/seaweedfs.png" width="32" alt="seaweedfs logo, ">][seaweedfs] <br /> [seaweedfs]                                                                          | Self hosted S3 Object Store                                                                                                               |            ✅            |
|                                                                 [<img src="assets/images/icons/k9s_icon.png" alt="k9s logo, outline of dog with ship wheels for eyes" width="32px">][k9s]</br>[k9s]                                                                | Terminal based dashboard for kubernetes                                                                                                   |            ✅            |


# Status
`smol-k8s-lab` is actively maintained, and in a semi-stable state. We still may introduce features that, upon major version releases, can introduce breaking changes, but we'll always include how to update your config files in the merged pull request description, and that will be linked in the release notes.

## Development
`smol-k8s-lab` is written in Python 3.12 and built and published using [Poetry]. You can check out the [`pyproject.toml`](https://github.com/small-hack/smol-k8s-lab/blob/main/pyproject.toml) for the versions of each library we install below.

### Core libraries

These are installed anytime you install `smol-k8s-lab` as an end user:

| Default Library | Description                                                                      |
|-----------------|----------------------------------------------------------------------------------|
| [bcrypt]        | to pass a password to argocd and automatically update your Bitwarden             |
| [click]         | handles arguments for the CLI                                                    |
| [kubernetes]    | for using the partially functional python sdk for kubernetes                     |
| [minio]         | for connecting to s3 and saving credentials                                      |
| [pyfiglet]      | uses figlet to print the ascii text banner in the tui                            |
| [pyjwt]         | used for processing tokens from zitadel                                          |
| [pyyaml]        | this is actively being removed in favor of ruamel.yaml                           |
| [rich]          | makes all the pretty formatted text in logs and `--help`                         |
| [textual]       | this is the framework used for writing the TUI                                   |
| [ruamel.yaml]   | to handle the k8s yamls and configs while maintaining comments)                  |
| [xdg-base-dirs] | lets us use default config and cache directories for storage  accross major OSes |

### Development libraries

These are installed anytime you want to develop smol-k8s-lab:

| Development Library       | Description                                                      |
|---------------------------|------------------------------------------------------------------|
| [mkdocs-material]         | for the docs site                                                |
| [mkdocs-video]            | for videos on the docs site                                      |
| [deptry]                  | for purging unused libraries                                     |
| [textual-dev]             | for consoling textual                                            |
| [pytest-textual-snapshot] | for taking screenshots with textual                              |
| [poethepoet]              | for running special tasks during poetry build                    |
| [coqui-tts]               | for generating text to speech audio files                        |
| [pydub]                   | for converting audio files from wav to mp3, requires ffmpeg      |
| [pygame]                  | for playing audio accross different OSes, requires alsa on linux |


We also utilize the [Bitwarden cli], for a password manager so you never have to see/know your Argo CD password.

## Things we don't handle (yet)

1. Port Forwarding

    If you want to access an app outside of port forwarding to test, you'll need to make sure your app's ingress is setup correctly and then you'll need to setup your router to port forward 80->80 and 443->443 for your WAN. Then, setup DNS for your domain if you want the wider internet to access this remotely.

2. High-Availability

    HA cluster design with K3s requires etcd or another external key-value store such as PostgreSQL. Smol-K8s-Lab deploys k3s in a single-node configuration using SQLite which can be used for multi-node configurations but is not suitable for high-availability.

<!-- k8s apps link references -->
[Local Path Provisioner]: https://github.com/rancher/local-path-provisioner
[nginx-ingress]: https://github.io/kubernetes/ingress-nginx

<!-- k8s distro link references -->
[k3s]: https://k3s.io/
[k3d]: https://k3d.io/
[KinD]: https://kind.sigs.k8s.io/

<!-- k8s optional apps link references -->
[ESO]: https://external-secrets.io
[alert manager]: https://prometheus.io/docs/alerting/latest/alertmanager/
[Argo CD]:https://argo-cd.readthedocs.io/en/latest/
[Argo CD Appset Secret Plugin]: https://github.com/small-hack/argocd-appset-secret-plugin/

[cert-manager]: https://cert-manager.io/docs/
[cilium]: https://github.com/cilium/cilium/tree/main/install/kubernetes/cilium
[Bitwarden ESO Provider]: https://github.com/small-hack/bitwarden-eso-provider
[grafana]: https://grafana.com/
[ingress-nginx]: https://github.io/kubernetes/ingress-nginx
[Home Assistant]: https://www.home-assistant.io/
[k8tz]: https://github.com/small-hack/argocd-apps/tree/main/alpha/k8tz
[k8up]: https://k8up.io
[Kyverno]: https://github.com/kyverno/kyverno/
[kepler]: https://github.com/sustainable-computing-io/kepler-helm-chart/tree/main/chart/kepler
[Local Path Provisioner]: https://github.com/rancher/local-path-provisioner
[loki]: https://grafana.com/oss/loki/
[Mastodon]: https://joinmastodon.org/
[matrix]: https://matrix.org/
[metallb]: https://github.io/metallb/metallb "metallb"
[minio]: https://min.io/
[Nextcloud]: https://github.com/nextcloud/helm
[Netmaker]: https://netmaker.io
[Prometheus Stack]: https://github.com/small-hack/argocd-apps/tree/main/prometheus
[promtail]: https://grafana.com/docs/loki/latest/send-data/promtail/
[seaweedfs]: https://github.com/seaweedfs/seaweedfs
[Vouch]: https://github.com/small-hack/vouch-helm-chart
[ZITADEL]: https://github.com/zitadel/zitadel-charts/tree/main

<!-- k8s tooling reference -->
[`brew`]: https://brew.sh
[k9s]: https://k9scli.io/topics/install/
[restic]: https://restic.readthedocs.io/en/stable/

<!-- smol-k8s-lab dependency lib link references -->
[Bitwarden cli]: https://bitwarden.com/help/cli/
[bcrypt]: https://pypi.org/project/bcrypt/
[click]: https://pypi.org/project/click/
[kubernetes]: https://github.com/kubernetes-client/python
[mkdocs-material]: https://squidfunk.github.io/mkdocs-material/
[mkdocs-video]: https://pypi.org/project/mkdocs-video/
[deptry]: https://pypi.org/project/deptry/
[textual-dev]: https://pypi.org/project/textual/
[pytest-textual-snapshot]: https://pypi.org/project/pytest-textual-snapshot/
[poethepoet]: https://pypi.org/project/poethepoet/
[coqui-tts]: https://pypi.org/project/coqui-tts/
[pydub]: https://pypi.org/project/pydub/
[pyfiglet]: https://pypi.org/project/pyfiglet/
[pygame]: https://www.pygame.org/
[pyjwt]: https://pypi.org/project/PyJWT/
[pyyaml]: https://pypi.org/project/PyYAML
[Poetry]: https://python-poetry.org/
[rich]: https://github.com/Textualize/richP
[ruamel.yaml]: https://pypi.org/project/ruamel.yaml/
[textual]: https://github.com/Textualize/textual
[xdg-base-dirs]: https://pypi.org/project/xdg-base-dirs/
