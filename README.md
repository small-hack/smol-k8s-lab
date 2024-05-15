<h2 align="center">
  <img
    src="https://raw.githubusercontent.com/catppuccin/catppuccin/main/assets/misc/transparent.png"
    height="30"
    width="0px"
  />
 🧸 <code>smol-k8s-lab</code>
  <a href="https://github.com/small-hack/smol-k8s-lab/releases">
    <img src="https://img.shields.io/github/v/release/small-hack/smol-k8s-lab?style=plastic&labelColor=484848&color=3CA324&logo=GitHub&logoColor=white">
  </a>
</h2>
<p align="center">
  A terminal based tool to install slimmer k8s distros on metal, with batteries included!
</p>

<p align="center">
  <a href="https://www.youtube.com/watch?v=UdOQM9n5hyU&t=0s">
    <img width="800" alt="Screenshot of smol-k8s-lab (on the welcome screen) in a video tutorial on youtube. please click this image, as it is a link to youtube where I explain everything about smol-k8s-lab. The video image screenshot shows the smol-k8s-lab create a cluster feature which is a text input" src="https://github.com/small-hack/smol-k8s-lab/assets/2389292/ee0ca93b-628e-495f-83ab-70aa9eb52295">
  </a><br>
  <sup>(Here's the <a href="https://youtu.be/2E9DVJpv440?feature=shared">same video with captions)</a></sup>
</p>


### Features
- Deploys [Argo CD](https://github.com/argoproj/argo-cd) by default, so you can manage your entire lab using files in [open source git repos](https://github.com/small-hack/argocd-apps)
  - Argo CD ships with a dashboard with a custom theme 💙
- Supports multiple [k8s distros](#supported-k8s-distributions)
- Specializes in using Bitwarden (though not required) to store sensitive values both locally and on your cluster
- Manages all your authentication needs centrally using Zitadel and Vouch 💪
- Supports initialization on a [range of common self-hosted apps](https://small-hack.github.io/smol-k8s-lab/k8s_apps/argocd/) 📱
  - featured initialized apps such as [Nextcloud](https://small-hack.github.io/smol-k8s-lab/k8s_apps/nextcloud/), [Matrix](https://small-hack.github.io/smol-k8s-lab/k8s_apps/matrix/), and [Home Assistant](https://small-hack.github.io/smol-k8s-lab/k8s_apps/home_assistant/) include backups
- Lots o' [docs](https://small-hack.github.io/smol-k8s-lab)

-----------------------------

* [Installation](#installation)
    * [pipx](#pipx)
    * [brew (still unstable)](#brew-still-unstable)
    * [Usage](#usage)
        * [Initialization](#initialization)
* [Under the hood](#under-the-hood)
    * [Supported k8s distributions](#supported-k8s-distributions)
    * [Default Installed Applications](#default-installed-applications)
* [Status](#status)


# Installation
B sure to check out our full [installation guide](https://small-hack.github.io/smol-k8s-lab/installation/), but the gist of it is `smol-k8s-lab` can be installed via `pipx` (or `brew` coming soon).

## pipx
`smol-k8s-lab` requires Python 3.11+ (and [pipx](https://github.com/pypa/pipx)). If you've already got both and [other pre-reqs](https://small-hack.github.io/smol-k8s-lab/installation/#prerequisites), you should be able to:

```bash
# install the CLI
pipx install smol-k8s-lab

# Check the help menu before proceeding
smol-k8s-lab --help
```

## brew (still unstable)

[`brew`] is the future preferred installation method for macOS/Debian/Ubuntu, as this will also install any non-python prerequisites you need, so you don't need to worry about them. This method is new, so please [let us know if anything isn't working for you](https://github.com/small-hack/homebrew-tap/issues).

```bash
# tap the special homebrew repo for our formula and install it
brew install small-hack/tap/smol-k8s-lab
```

Then you should be able to check the version and cli options with:

```bash
smol-k8s-lab --help
```

<p align="center">
  <a href="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/assets/images/screenshots/help_text.svg">
      <img src="./docs/assets/images/screenshots/help_text.svg" alt="Output of smol-k8s-lab --help after cloning the directory and installing the prerequisites.">
  </a>
</p>

Checkout our [TUI docs](https://small-hack.github.io/smol-k8s-lab/tui/create_modify_screens/) for more info on how to get started playing with `smol-k8s-lab` :-)

## Usage

### Initialization
After you've followed the installation instructions, if you're *new* to `smol-k8s-lab`,  initialize a new config file:

```bash
# we'll walk you through any configuration needed before
# saving the config and deploying it for you
smol-k8s-lab
```

<details>
  <summary><b>Upgrading config from v4.x to v5.x</b></summary>

If you've installed smol-k8s-lab prior to `v5.0.0`, please backup your old configuration, and then remove the `~/.config/smol-k8s-lab/config.yaml` (or `$XDG_CONFIG_HOME/smol-k8s-lab/config.yaml`) file entirely, then run the following with either pip or pipx:

*if using pip*:
```yaml
# this uninstalls the old smol-k8s-lab for python 3.11
pip3.11 uninstall smol-k8s-lab

# this installs smol-k8s-lab for python 3.12
pip3.12 install --upgrade smol-k8s-lab

# this initializes a new configuration
smol-k8s-lab
```

*or if using pipx*:
```yaml
# this upgrades smol-k8s-lab
pipx upgrade smol-k8s-lab

# this initializes a new configuration
smol-k8s-lab
```

We have done a *masive* upgrade of the config file. You'll need to update your configs based on the details in https://github.com/small-hack/smol-k8s-lab/pull/210 . The main changes are to the following (check each doc link for details):

- [accessibility features](https://small-hack.github.io/smol-k8s-lab/config_file/#tui-and-accessibility-configuration)
- [k3s nodes section](https://small-hack.github.io/smol-k8s-lab/config_file/#k3s)
- [backups and restores](https://small-hack.github.io/smol-k8s-lab/config_file/#backups-and-restores)
- [sensitive values](https://small-hack.github.io/smol-k8s-lab/config_file/#sensitive-values)
- [k9s has been removed in favor of run command](https://small-hack.github.io/smol-k8s-lab/config_file/#run-command) (hint: you can still use k9s via run command)

</details>

<details>
  <summary><b>Upgrading config from v3.7.1 to v4.x</b></summary>

If you've installed smol-k8s-lab prior to `v4.0.0`, please backup your old configuration, and then remove the `~/.config/smol-k8s-lab/config.yaml` (or `$XDG_CONFIG_HOME/smol-k8s-lab/config.yaml`) file entirely, then run the following with either pip or pipx:

*if using pip*:
```yaml
# this upgrades smol-k8s-lab
pip3.11 install --upgrade smol-k8s-lab

# this initializes a new configuration
smol-k8s-lab
```

*or if using pipx*:
```yaml
# this upgrades smol-k8s-lab
pipx upgrade smol-k8s-lab

# this initializes a new configuration
smol-k8s-lab
```

The main breaking changes between `v3.7.1` and `v4.0.0` are that we now default enable metrics on most apps. Because of this, you need to have the Prometheus ServiceMonitor CRD installed ahead of time. Luckily, we now provide that as an app as well :) If you deleted your config and created a new one, it will already be there, but if you want to reuse your old config, you can add the app like this:

```yaml
apps:
  prometheus_crds:
    description: |
      [link=https://prometheus.io/docs/introduction/overview/]Prometheus[/link] CRDs to start with.
      You can optionally disable this if you don't want to deploy apps with metrics.

    enabled: true
    argo:
      # secrets keys to make available to Argo CD ApplicationSets
      secret_keys: {}
      # git repo to install the Argo CD app from
      repo: https://github.com/small-hack/argocd-apps
      # path in the argo repo to point to. Trailing slash very important!
      path: prometheus/crds/
      # either the branch or tag to point at in the argo repo above
      revision: main
      # namespace to install the k8s app in
      namespace: prometheus
      # recurse directories in the provided git repo
      directory_recursion: false
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        name: prometheus
        source_repos:
        - https://github.com/prometheus-community/helm-charts.git
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces:
          - kube-system
          - prometheus
```

If using the default repos, please also disable directory directory_recursion for:
- your prometheus stack app
- zitadel

For all changes, please check out [PR #206](https://github.com/small-hack/smol-k8s-lab/pull/206).

</details>

<details>
  <summary><b>Upgrading config from v2.2.4 to v3.x</b></summary>

If you've installed smol-k8s-lab prior to `v3.0.0`, please backup your old configuration, and then remove the `~/.config/smol-k8s-lab/config.yaml` (or `$XDG_CONFIG_HOME/smol-k8s-lab/config.yaml`) file entirely, then run the following with either pip or pipx:

*if using pip*:
```yaml
# this upgrades smol-k8s-lab
pip3.11 install --upgrade smol-k8s-lab

# this initializes a new configuration
smol-k8s-lab
```

*or if using pipx*:
```yaml
# this upgrades smol-k8s-lab
pipx upgrade smol-k8s-lab

# this initializes a new configuration
smol-k8s-lab
```

The main breaking changes between `v2.2.4` and `v3.0` are as follows:

- *home assistant has graduated from demo app to live app*

You'll need to change `apps.home_assistant.argo.path` to either `home-assistant/toleration_and_affinity/` if you're using node labels and taints, or `home-assistant/` if you're deploying to a single node cluster. Here's an example with no tolerations or node affinity:

```yaml
apps:
  home_assistant:
    enabled: false
    description: |
      [link=https://home-assistant.io]Home Assistant[/link] is a home IOT management solution.

      By default, we assume you want to use node affinity and tolerations to keep home assistant pods on certain nodes and keep other pods off said nodes. If you don't want to use either of these features but still want to use the small-hack/argocd-apps repo, first change the argo path to /home-assistant/ and then remove the 'toleration_' and 'affinity' secret_keys from the yaml file under apps.home_assistant.description.
    argo:
      secret_keys:
        hostname: "home-assistant.coolestdogintheworld.dog"
      repo: https://github.com/small-hack/argocd-apps
      path: home-assistant/
      revision: main
      namespace: home-assistant
      directory_recursion: false
      project:
        source_repos:
        - http://jessebot.github.io/home-assistant-helm
        destination:
          namespaces:
          - argocd
```

And here's an example for labeled and tainted nodes, where your pod can use tolerations and node affinity:

```yaml
apps:
  home_assistant:
    enabled: false
    description: |
      [link=https://home-assistant.io]Home Assistant[/link] is a home IOT management solution.

      By default, we assume you want to use node affinity and tolerations to keep home assistant pods on certain nodes and keep other pods off said nodes. If you don't want to use either of these features but still want to use the small-hack/argocd-apps repo, first change the argo path to /home-assistant/ and then remove the 'toleration_' and 'affinity' secret_keys from the yaml file under apps.home_assistant.description.
    argo:
      secret_keys:
        hostname: "home-assistant.coolestdogintheworld.dog"
        toleration_key: "blutooth"
        toleration_operator: "Equals"
        toleration_value: "True"
        toleration_effect: "NoSchedule"
        affinity_key: "blutooth"
        affinity_value: "True"
      repo: https://github.com/small-hack/argocd-apps
      path: home-assistant/toleration_and_affinity/
      revision: main
      namespace: home-assistant
      directory_recursion: false
      project:
        source_repos:
        - http://jessebot.github.io/home-assistant-helm
        destination:
          namespaces:
          - argocd
```


- *new k3s feature for adding additional nodes*

This feature changes `k8s_distros.k3s.nodes` to be a dictionary so that you can include additional nodes for us to join to the cluster after we create it, but before we install apps. Here's an example of how you can add a new node to k3s on installation:


```yaml
k8s_distros:
  k3s:
    enabled: false
    k3s_yaml:
      # if you enable MetalLB, we automatically add servicelb to the disable list
      # enables encryption at rest for Kubernetes secrets
      secrets-encryption: true
      # disables traefik so we can enable ingress-nginx, remove if you're using traefik
      disable:
      - "traefik"
      node-label:
      - "ingress-ready=true"
      kubelet-arg:
      - "max-pods=150"
    # nodes to SSH to and join to cluster. example:
    nodes:
      # name can be a hostname or ip address
      serverfriend1.lan:
        # change ssh_key to the name of a local private key to use
        ssh_key: id_rsa
        # must be node type of "worker" or "control_plane"
        node_type: worker
        # labels are optional, but may be useful for pod node affinity
        node_labels:
          - iot=true
        # taints are optional, but may be useful for pod tolerations
        node_taints:
          - iot=true:NoSchedule
```

if you don't want to add any nodes, this is what you should change your nodes section to be:

```yaml
k8s_distros:
  k3s:
    enabled: false
    k3s_yaml:
      # if you enable MetalLB, we automatically add servicelb to the disable list
      # enables encryption at rest for Kubernetes secrets
      secrets-encryption: true
      # disables traefik so we can enable ingress-nginx, remove if you're using traefik
      disable:
      - "traefik"
      node-label:
      - "ingress-ready=true"
      kubelet-arg:
      - "max-pods=150"
    # nodes to SSH to and join to cluster. example:
    nodes: {}
```


- *cert-manager now supports DNS01 challenge solver using the Cloudflare provider*

This feature reworks the `apps.cert_manager.init` and `apps.cert_manager.argo.secret_keys` sections.

Here's an example of using the HTTP01 challenge solver, which would be the only previously supported challenge solver, so if you want everything to just work how it did before your config file should look like this:

```yaml
apps:
  cert_manager:
    enabled: true
    description: |
      [link=https://cert-manager.io/]cert-manager[/link] let's you use LetsEncrypt to generate TLS certs for all your apps with ingress.

      smol-k8s-lab supports optional initialization by creating [link=https://cert-manager.io/docs/configuration/acme/]ACME Issuer type[/link] [link=https://cert-manager.io/docs/concepts/issuer/]ClusterIssuers[/link] using either the HTTP01 or DNS01 challenge solvers. We create two ClusterIssuers: letsencrypt-staging and letsencrypt-staging.

      For the DNS01 challange solver, you will need to either export $CLOUDFLARE_API_TOKEN as an env var, or fill in the sensitive value for it each time you run smol-k8s-lab.

      Currently, Cloudflare is the only supported DNS provider for the DNS01 challenge solver. If you'd like to use a different DNS provider or use a different Issuer type all together, please either set one up outside of smol-k8s-lab. We also welcome [link=https://github.com/small-hack/smol-k8s-lab/pulls]PRs[/link] to add these features :)

    # Initialize of the app through smol-k8s-lab
    init:
      # Deploys staging and prod ClusterIssuers and prompts you for
      # values if they were not set. Switch to false if you don't want
      # to deploy any ClusterIssuers
      enabled: true
      values:
        # Used for to generate certs and alert you if they're going to expire
        email: "you@emailsforfriends.com"
        # choose between "http01" or "dns01"
        cluster_issuer_acme_challenge_solver: http01
        # only needed if cluster_issuer_challenge_solver set to dns01,
        # currently only cloudflare is supported
        cluster_issuer_acme_dns01_provider: cloudflare
      sensitive_values: []
    argo:
      secret_keys: {}
      # git repo to install the Argo CD app from
      repo: "https://github.com/small-hack/argocd-apps"
      # path in the argo repo to point to. Trailing slash very important!
      path: "cert-manager/"
      # either the branch or tag to point at in the argo repo above
      revision: main
      # namespace to install the k8s app in
      namespace: "cert-manager"
      # recurse directories in the provided git repo
      directory_recursion: false
      # source repos for cert-manager CD App Project (in addition to argo.repo)
      project:
        source_repos:
          - https://charts.jetstack.io
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces:
            - kube-system
```

And here's how you'd use the new DNS01 feature (keep in mind you need to either provide a sensitive value each time you run `smol-k8s-lab`, OR you need to export `$CLOUDFLARE_API_TOKEN` as an env var prior to running `smol-k8s-lab`):


```yaml
apps:
  cert_manager:
    enabled: true
    description: |
      [link=https://cert-manager.io/]cert-manager[/link] let's you use LetsEncrypt to generate TLS certs for all your apps with ingress.

      smol-k8s-lab supports optional initialization by creating [link=https://cert-manager.io/docs/configuration/acme/]ACME Issuer type[/link] [link=https://cert-manager.io/docs/concepts/issuer/]ClusterIssuers[/link] using either the HTTP01 or DNS01 challenge solvers. We create two ClusterIssuers: letsencrypt-staging and letsencrypt-staging.

      For the DNS01 challange solver, you will need to either export $CLOUDFLARE_API_TOKEN as an env var, or fill in the sensitive value for it each time you run smol-k8s-lab.

      Currently, Cloudflare is the only supported DNS provider for the DNS01 challenge solver. If you'd like to use a different DNS provider or use a different Issuer type all together, please either set one up outside of smol-k8s-lab. We also welcome [link=https://github.com/small-hack/smol-k8s-lab/pulls]PRs[/link] to add these features :)

    # Initialize of the app through smol-k8s-lab
    init:
      # Deploys staging and prod ClusterIssuers and prompts you for
      # values if they were not set. Switch to false if you don't want
      # to deploy any ClusterIssuers
      enabled: true
      values:
        # Used for to generate certs and alert you if they're going to expire
        email: "you@emailsforfriends.com"
        # choose between "http01" or "dns01"
        cluster_issuer_acme_challenge_solver: dns01
        # only needed if cluster_issuer_challenge_solver set to dns01
        # currently only cloudflare is supported
        cluster_issuer_acme_dns01_provider: cloudflare
      sensitive_values:
        # can be passed in as env vars if you pre-pend CERT_MANAGER_
        # e.g. CERT_MANAGER_CLOUDFLARE_API_TOKEN
      - CLOUDFLARE_API_TOKEN
    argo:
      secret_keys: {}
      # git repo to install the Argo CD app from
      repo: "https://github.com/small-hack/argocd-apps"
      # path in the argo repo to point to. Trailing slash very important!
      path: "cert-manager/"
      # either the branch or tag to point at in the argo repo above
      revision: main
      # namespace to install the k8s app in
      namespace: "cert-manager"
      # recurse directories in the provided git repo
      directory_recursion: false
      # source repos for cert-manager CD App Project (in addition to argo.repo)
      project:
        source_repos:
          - https://charts.jetstack.io
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces:
            - kube-system
```

</details>

<details>
  <summary><b>Upgrading config from v1.x to v2.x</b></summary>

If you've installed smol-k8s-lab prior to `v2.0.0`, please backup your old configuration, and then remove the `~/.config/smol-k8s-lab/config.yaml` (or `$XDG_CONFIG_HOME/smol-k8s-lab/config.yaml`) file entirely, then run the following:

```yaml
# this upgrades smol-k8s-lab
pip3.11 install --upgrade smol-k8s-lab

# this initializes a new configuration
smol-k8s-lab
```

The main difference between the old and new config files are for apps, we've added:

- `apps.APPNAME.description` - for adding a custom description, set it to whatever you like
- `apps.APPNAME.argo.directory_recursion` - so you can have bigger nested apps :)
- `apps.APPNAME.argo.project.destination.namespaces` - control what namespaces are allowed for a project

And we've changed:

- `apps.APPNAME.argo.ref` to `apps.APPNAME.argo.revision`
- `apps.APPNAME.argo.project_source_repos` to `apps.APPNAME.argo.project.source_repos`

And we've REMOVED:

- `apps.APPNAME.argo.part_of_app_of_apps` - this was mostly used internally, we think

Here's an example of an updated cert-manager app with the new config:

```yaml
apps:
  cert_manager:
    # ! NOTE: you currently can't set this to false. It is necessary to deploy
    # most of our supported Argo CD apps since they often have TLS enabled either
    # for pod connectivity or ingress
    enabled: true
    description: |
      [link=https://cert-manager.io/]cert-manager[/link] let's you use LetsEncrypt to generate TLS certs for all your apps with ingress.

      smol-k8s-lab supports initialization by creating two [link=https://cert-manager.io/docs/concepts/issuer/]ClusterIssuers[/link] for both staging and production using a provided email address as the account ID for acme.

    # Initialize of the app through smol-k8s-lab
    init:
      # Deploys staging and prod ClusterIssuers and prompts you for
      # cert-manager.argo.secret_keys if they were not set. Switch to false if
      # you don't want to deploy any ClusterIssuers
      enabled: true
    argo:
      secret_keys:
        # Used for letsencrypt-staging, to generate certs
        email: ""
      # git repo to install the Argo CD app from
      repo: "https://github.com/small-hack/argocd-apps"
      # path in the argo repo to point to. Trailing slash very important!
      path: "cert-manager/"
      # either the branch or tag to point at in the argo repo above
      revision: main
      # namespace to install the k8s app in
      namespace: "cert-manager"
      # recurse directories in the provided git repo
      directory_recursion: false
      # source repos for cert-manager CD App Project (in addition to argo.repo)
      project:
        source_repos:
          - https://charts.jetstack.io
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces:
            - kube-system
```

</details>

# Under the hood
Note: this project is not officially affiliated with any of the below tooling or applications.

### Supported k8s distributions
We always install the latest version of Kubernetes that is available from the distro's startup script.

|  Distro    |         Description              |
|:----------:|:------------------------------------------------------|
| [<img src="https://raw.githubusercontent.com/small-hack/smol-k8s-lab/main/docs/assets/images/icons/k3s_icon.ico" width="26">][k3s] <br /> [k3s] | The certified Kubernetes distribution built for IoT & Edge computing |
| [<img src="https://raw.githubusercontent.com/small-hack/smol-k8s-lab/main/docs/assets/images/icons/k3d.png" width="26">][k3d] <br /> [k3d] | **ALPHA - TESTING PHASE** k3s in docker 🐳 |
| [<img src="https://raw.githubusercontent.com/small-hack/smol-k8s-lab/main/docs/assets/images/icons/kind_icon.png" width="32">][KinD] <br /> [KinD] | kind is a tool for running local Kubernetes clusters using Docker container “nodes”. kind was primarily designed for testing Kubernetes itself, but may be used for local development or CI. |

We tend to test first on k3s first, then the other distros. k3d support coming soon.

### Default Installed Applications
All of these can be disabled with the exception of Argo CD, which is optional, but if not installed, `smol-k8s-lab` will <i>only</i> install: MetalLB, nginx-ingress, and cert-manager.

|           Application           |                      Description                      | Initialization Supported |
|:-------------------------------:|:------------------------------------------------------|:------------------------:|
| [<img src="https://raw.githubusercontent.com/small-hack/smol-k8s-lab/main/docs/assets/images/icons/metallb_icon.png" width="32px" alt="metallb logo, blue arrow pointing up, with small line on one leg of arrow to show balance">][metallb] <br /> [metallb] | Loadbalancer and IP Address pool manager for metal | ✅ |
| [<img src="https://raw.githubusercontent.com/small-hack/smol-k8s-lab/main/docs/assets/images/icons/nginx.ico" width="32px" alt="nginx logo, white letter N with green background">][ingress-nginx] <br /> [ingress-nginx] | The ingress controller allows access to the cluster remotely, needed for web traffic | ❌ |
| [<img src="https://raw.githubusercontent.com/small-hack/smol-k8s-lab/main/docs/assets/images/icons/cert-manager_icon.png" width="32px" alt="cert manager logo">][cert-manager] <br /> [cert-manager] | For SSL/TLS certificates | ✅ |
| [<img src="https://raw.githubusercontent.com/small-hack/smol-k8s-lab/main/docs/assets/images/icons/argo_icon.png" width="32" alt="argo CD logo, an organer squid wearing a fishbowl helmet">][Argo CD] <br /> [Argo CD] | Gitops - Continuous Deployment | ✅ |
| [<img src="https://raw.githubusercontent.com/small-hack/smol-k8s-lab/main/docs/assets/images/icons/argo_icon.png" width="32" alt="argo CD logo, an organer squid wearing a fishbowl helmet">][Argo CD Appset Secret Plugin] <br /> [Argo CD Appset Secret Plugin] | Gitops - Continuous Deployment | ✅ |
| [<img src="https://raw.githubusercontent.com/small-hack/smol-k8s-lab/main/docs/assets/images/icons/eso_icon.png" width="32" alt="ESO logo, outline of robot with astricks in a screen in it's belly">][ESO] <br /> [ESO] | external-secrets-operator integrates external secret management systems like Bitwarden or GitLab | ❌ |
| [<img src="https://raw.githubusercontent.com/small-hack/smol-k8s-lab/main/docs/assets/images/icons/eso_icon.png" width="32" alt="ESO logo, again">][Bitwarden ESO Provider] <br /> [Bitwarden ESO Provider] | Bitwarden external-secrets-operator provider  | ✅ |
| [<img src="https://raw.githubusercontent.com/small-hack/smol-k8s-lab/main/docs/assets/images/icons/zitadel.png" width="32" alt="Zitadel logo, an orange arrow pointing left">][ZITADEL] <br /> [ZITADEL] | An identity provider and OIDC provider to provide SSO | ✅ |
| [<img src="https://raw.githubusercontent.com/small-hack/smol-k8s-lab/main/docs/assets/images/icons/vouch.png" width="32" alt="Vouch logo, the letter V in rainbow ">][Vouch] <br /> [Vouch] | Vouch proxy allows you to secure web pages that lack authentication e.g. prometheus | ✅ |
| [<img src="https://raw.githubusercontent.com/small-hack/smol-k8s-lab/main/docs/assets/images/icons/prometheus.png" width="32" alt="Prometheus logo, a torch">][Prometheus Stack] <br /> [Prometheus Stack] | Prometheus monitoring and logging stack using [loki]/[promtail], [alert manager], and [grafana]  | ✅ |

For a complete list of installable applications, checkout the [default apps docs](https://small-hack.github.io/smol-k8s-lab/k8s_apps/). To install your own custom apps, you can check out an [example via the config file](https://small-hack.github.io/smol-k8s-lab/config_file/#applications) or [learn how to do it via the tui](https://small-hack.github.io/smol-k8s-lab/tui/apps_screen/#adding-new-applications).


# Status
Somewhat stable and being actively supported, so if you'd like to [contribute](./CONTRIBUTING.md) or just found a :bug:, feel free to open an issue (and/or pull request), and we'll try to take a look ASAP!

<!-- k8s distro link references -->
[k3s]: https://k3s.io/
[k3d]: https://k3d.io/
[KinD]: https://kind.sigs.k8s.io/

<!-- k8s optional apps link references -->
[ESO]: https://external-secrets.io/v0.8.1/
[alert manager]: https://prometheus.io/docs/alerting/latest/alertmanager/
[Argo CD]:https://argo-cd.readthedocs.io/en/latest/
[Argo CD Appset Secret Plugin]: https://github.com/jessebot/argocd-appset-secret-plugin/
[cert-manager]: https://cert-manager.io/docs/
[cilium]: https://github.com/cilium/cilium/tree/v1.14.1/install/kubernetes/cilium
[Bitwarden ESO Provider]: https://github.com/jessebot/bitwarden-eso-provider
[grafana]: https://grafana.com/
[ingress-nginx]: https://github.io/kubernetes/ingress-nginx
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
[Prometheus Stack]: https://github.com/small-hack/argocd-apps/tree/main/prometheus
[promtail]: https://grafana.com/docs/loki/latest/send-data/promtail/
[Vouch]: https://github.com/jessebot/vouch-helm-chart
[ZITADEL]: https://github.com/zitadel/zitadel-charts/tree/main

<!-- k8s tooling reference -->
[`brew`]: https://brew.sh
[k9s]: https://k9scli.io/topics/install/
[restic]: https://restic.readthedocs.io/en/stable/
