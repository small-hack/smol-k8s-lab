# Migration notice

We are moving this repo to [codeberg.org/open-engineering/smol-k8s-lab](https://codeberg.org/open-engineering/smol-k8s-lab).

Releases after `v6.4.8` happen at codeberg.org, but *no future pushes or releases will happen at github*. We will keep a public archive of this repo.

# original documentation from `v6.4.8`:

<h2 align="center">
  <img
    src="https://raw.githubusercontent.com/catppuccin/catppuccin/main/assets/misc/transparent.png"
    height="30"
    width="0px"
  />
 🧸 <code>smol-k8s-lab</code>
  <a href="https://github.com/open-engineering-nl/smol-k8s-lab/releases">
    <img src="https://img.shields.io/github/v/release/open-engineering-nl/smol-k8s-lab?style=plastic&labelColor=484848&color=3CA324&logo=GitHub&logoColor=white">
  </a>
</h2>
<p align="center">
  A terminal based tool to install slimmer k8s distros on metal, with batteries included!
</p>

<p align="center">
    <img width="800" alt="Screenshot of smol-k8s-lab (on the welcome screen) in a video tutorial on youtube. please click this image, as it is a link to youtube where I explain everything about smol-k8s-lab. The video image screenshot shows the smol-k8s-lab create a cluster feature which is a text input" src="https://github.com/open-engineering-nl/smol-k8s-lab/assets/2389292/ee0ca93b-628e-495f-83ab-70aa9eb52295">
  <br>
</p>


### Features
- Deploys [Argo CD](https://github.com/argoproj/argo-cd) by default, so you can manage your entire lab using files in [open source git repos](https://codeberg.org/open-engineering/argocd-apps)
  - Argo CD ships with a dashboard with a custom theme 💙
- Supports multiple k8s distros
- Specializes in using Bitwarden (though not required) to store sensitive values both locally and on your cluster (OpenBao coming soon!)
- Manages all your authentication needs centrally using Zitadel (self-hosted IAM/SSO) and Vouch (For using OAuth2 on sites that don't it)
- Supports initialization on a range of common self-hosted apps
  - featured initialized apps such as [Zitadel], [Nextcloud](https://codeberg.org/open-engineering/argocd-apps/src/main/nextcloud/), [Matrix](https://codeberg.org/open-engineering/argocd-apps/src/main/matrix/), [Mastodon](https://codeberg.org/open-engineering/mastodon-helm-chart/), and [Home Assistant](https://codeberg.org/open-engineering/argocd-apps/src/main/home_assistant/) include backups and restores
- Lots o' [docs](https://https://codeberg.org/open-engineering/smol-k8s-lab/src/main/docs)

<!-- k8s distro link references -->
[k3s]: https://k3s.io/
[k3d]: https://k3d.io/
[KinD]: https://kind.sigs.k8s.io/

<!-- k8s optional apps link references -->
[ZITADEL]: https://github.com/zitadel/zitadel-charts/tree/main
