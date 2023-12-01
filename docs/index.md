## ☁️  *smol k8s lab* 🧸
[<img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/screenshots/help_text.svg" alt="Output of smol-k8s-lab --help after cloning the directory and installing the prerequisites.">](https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/screenshots/help_text.svg)

A project aimed at getting up and running quickly with mostly smaller k8s distros in one small command line script.

### Stack We Install on K8s
Version is the helm chart version, or manifest version.

|           Application           |    Version    |                      Description                      |
|:-------------------------------:|:-------------:|:------------------------------------------------------|
| 🐄 [Local Path Provisioner] |   k3s latest  | Default simple local file storage for persistent data |
| [<img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/icons/nginx.ico" width="32px" alt="nginx logo, white letter N with green background">][nginx-ingress] <br /> [nginx-ingress] | 4.4.0 | The ingress controller allows access to the cluster remotely, needed for web traffic |
| [<img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/icons/cert-manager_icon.png" width="32px" alt="cert manager logo">][cert-manager] <br /> [cert-manager] | 1.10.1 | For SSL/TLS certificates |
| [<img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/icons/k9s_icon.png" alt="k9s logo, outline of dog with ship wheels for eyes" width="32px">][k9s] <br /> [k9s] | latest | Terminal based dashboard for kubernetes |


#### Optionally installed

| Application/Tool |    Version    | Description |
|:----------------:|:-------------:|:------------|
| [<img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/icons/metallb_icon.png" width="32px" alt="metallb logo, blue arrow pointing up, with small line on one leg of arrow to show balance">][metallb] <br /> [metallb] | 0.13.7 | loadbalancer for metal, since we're mostly selfhosting |
| [<img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/icons/argo_icon.png" width="32" alt="argo CD logo, an organer squid wearing a fishbowl helmet">][Argo CD] <br /> [Argo CD] | 5.16.2 | Gitops - Continuous Deployment |
| [<img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/icons/eso_icon.png" width="32" alt="ESO logo, outline of robot with astricks in a screen in it's belly">][ESO] <br /> [ESO] | 0.6.1 | external-secrets-operator integrates external secret management systems like GitLab|
| [<img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/icons/kyverno_icon.png"  width="32" alt="kyvero logo">][Kyverno] <br /> [Kyverno] | latest | Kubernetes native policy management to enforce policies on k8s resources |


### Tooling Used for the CLI itself and interface
smol-k8s-lab is written in Python and built and published using [Poetry]. You can check out the `pyproject.toml` for the versions of each library we install below:

- [rich] (this is what makes all the pretty formatted text)
- [PyYAML] (to handle the k8s yamls and configs)
- [bcrypt] (to pass a password to argocd and automatically update your Bitwarden)
- [click] (handles arguments for the CLI)

We also utilize the [Bitwarden cli], for a password manager so you never have to see/know your argocd password.

## Things we don't handle

### Port Forwarding
If you want to access an app outside of port forwarding to test, you'll need to make sure your app's ingress is setup correctly and then you'll need to setup your router to port forward 80->80 and 443->443 for your WAN. then setup DNS for your domain if you want the wider internet to access this remotely.

### Troubleshooting
If you're stuck, checkout the [Notes section](https://jessebot.github.io/smol-k8s-lab/notes) to see if we also got stuck on the same thing at some point :)


<!-- k8s apps link references -->
[metallb]: https://github.io/metallb/metallb "metallb"
[Local Path Provisioner]: https://github.com/rancher/local-path-provisioner
[nginx-ingress]: https://github.io/kubernetes/ingress-nginx
[cert-manager]: https://cert-manager.io/docs/
[k9s]: https://k9scli.io/topics/install/

<!-- k8s opitonal argocd apps link references -->
[Argo CD]: https://github.io/argoproj/argo-helm
[ESO]: https://external-secrets.io/v0.5.9/
[Kyverno]: https://github.com/kyverno/kyverno/

<!-- smol-k8s-lab dependency lib link references -->
[Poetry]: https://python-poetry.org/
[rich]: https://github.com/Textualize/richP
[PyYAML]: https://pyyaml.org/
[bcrypt]: https://pypi.org/project/bcrypt/
[click]: https://pypi.org/project/click/
[Bitwarden cli]: https://bitwarden.com/help/cli/
