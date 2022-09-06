# Smol K8s Homelab

Currently in a beta state. We throw local k8s (kubernetes) testing tools in this repo, mainly [`smol-k8s-homelab.py`](./smol-k8s-homelab.py). This project is aimed at getting up and running quickly with mostly smaller k8s distros in one small command line script, but there's also full tutorials to manually set up each distro in the [docs we maintain](https://jessebot.github.io/smol_k8s_homelab/distros) as well as BASH scripts for basic automation of each k8s distro in each directory under `./distro/[NAME OF K8S DISTRO]/bash_full_quickstart.sh`.

### Currently supported k8s distros

| Distro | [smol-k8s-homelab.py](./smol-k8s-homelab.py) Support|
|:---:|:---:|
|[k3s](https://k3s.io/)            | ✅   | 
|[KinD](https://kind.sigs.k8s.io/) | ✅   | 
|[k0s](https://k0sproject.io/)     | soon |

### Stack We Install on K8s
We tend to test first one k3s and then kind and then k0s.
| Application/Tool | What is it? |
|:-----------:|:--------------|
| [metallb](https://github.io/metallb/metallb) | loadbalancer for metal, since we're mostly selfhosting |
| [nginx-ingress-controller](https://github.io/kubernetes/ingress-nginx) | Ingress allows access to the cluster remotely, needed for web traffic |
| [cert-manager](https://cert-manager.io/docs/) | For SSL/TLS certificates |
| [k9s](https://k9scli.io/topics/install/) | Terminal based dashboard for kubernetes |
| [local path provisioner]() | Default simple local file storage |

#### Optionally installed
| Application/Tool | What is it? |
|:-----------:|:--------------| 
| [sealed-secrets](https://github.com/bitnami-labs/sealed-secrets) | Encrypts secrets files so you can check them into git |
| [external-secrets-operator](https://external-secrets.io/v0.5.9/) | integrates external secret management systems like GitLab|
| [argo-cd](https://github.io/argoproj/argo-helm) | Gitops - Continuous Deployment |

If you install argocd, and you use bitwarden, we'll generate an admin password and automatically place it in your vault if you pass in the `-p` option. Curently only works with Bitwarden.

Want to get started with argocd? If you've installed it via smol_k8s_homelab, then you can jump to here:
https://github.com/jessebot/argo-example#argo-via-the-gui

Otherwise, if you want to start from scratch, start here: https://github.com/jessebot/argo-example#argocd

#### Other important tools we install

- [k9s](https://k9scli.io/topics/install/): Terminal based dashboard for kubernetes


## Quickstart
This is aimed at being a much more scalable experience, but is still being worked on. So far, it works for k3s and kind.

#### Pre-Req
- Have Python 3.9 or higher installed as well as pip3
- [brew](https://brew.sh)
- **:bell: change the values in `config_sample.yml` to your own**
- Have internet access.

```bash
# Make sure you have brew installed (https://brew.sh)
brew bundle --file=./deps/Brewfile

# install the requirements
pip3 install -r ./deps/requirements.txt

# change the values in config_sample.yml to your own values then rename it
mv config_sample.yml config.yml

# test to make sure the script loads
./smol-k8s-homelab.py --help
```

The help should return this:
```bash
usage: smol-k8s-homelab.py [-h] [-a] [-d] [-e] [-f FILE] [-k] [-p] [-s] k8s

Quickly install a k8s distro for a homelab setup. Installs k3s with metallb, nginx-ingess-controller, cert-manager, and argocd

positional arguments:
  k8s                   distribution of kubernetes to install: k3s or kind. k0s coming soon

optional arguments:
  -h, --help            show this help message and exit
  -a, --argo            Install Argo CD as part of this script, defaults to False
  -d, --delete          Delete the existing cluster, REQUIRES -k/--k8s [k3s|kind]
  -e, --external_secret_operator
                        Install the external secrets operator to pull secrets from somewhere else, so far only supporting gitlab
  -f FILE, --file FILE  Full path and name of yml to parse, e.g. -f /tmp/config.yml
  -k, --k9s             Run k9s as soon as this script is complete, defaults to False
  -p, --password_manager
                        Store generated admin passwords directly into your password manager. Right now, this defaults to Bitwarden and
                        requires you to input your vault password to unlock the vault temporarily.
  -s, --sealed_secrets  Install bitnami sealed secrets, defaults to False
```

### Install k8s distro with `./smol-k8s-homelab.py`
Currently only being tested with k3s and kind, but soon you can do other distros listed above. In the meantime, use the tutorial above for k0s.
```bash
# you can replace k3s with kind
./smol-k8s-homelab.py k3s
```

#### Install some kubectl plugins (Optional)
These together make namespace switching better. Learn more about kubectx + kubens [here](https://github.com/ahmetb/kubectx).
```bash
kubectl krew update
kubectl krew install ctx
kubectl krew install ns
```
To install plugins from my newline-delimited krew file, run:
```bash
kubectl krew install < deps/kubectl_krew_plugins
```

#### Install @jessebot's `.bashrc_k8s` (optional)
You can copy over the rc file for some helpful aliases:
```bash
# copy the file to your home directory
cp deps/.bashrc_k8s ~

# load the file for your current shell
source ~/.bashrc_k8s
```
To have the above file sourced every new shell, copy this into your `.bashrc` or `.bash_profile`:
```
# include external .bashrc_k8s if it exists
if [ -f $HOME/.bashrc_k8s ]; then
    . $HOME/.bashrc_k8s
fi
```

### Uninstall distro with python script
```bash
# you can replace k3s with kind
./smol-k8s-homelab.py k3s --delete
```

## Final Touches

### Port Forwarding
If you want to access an app outside of port forwarding to test, you'll need to make sure your app's ingress is setup correctly and then you'll need to setup your router to port forward 80->80 and 443->443 for your WAN. then setup DNS for your domain if you want the wider internet to access this remotely.

### SSL/TLS

After SSL is working (if it's not, follow the steps in the [cert-manager common error troubleshooting guide](https://cert-manager.io/docs/faq/acme/#common-errors)), you can also change the `letsencrypt-staging` value to `letsencrypt-prod` for any domains you own and can configure to point to your cluster via DNS.


### Remote cluster administration (k3s only)
You can also copy your remote k3s kubeconfig with a little script in `./distros/k3s/`:

```bash
# CHANGE THESE TO YOUR OWN DETAILS or not ¯\_(ツ)_/¯
export REMOTE_HOST="192.168.20.2"
export REMOTE_SSH_PORT="22"
export REMOTE_USER="cooluser4dogs"

# this script will totally wipe your kubeconfig :) use with CAUTION
./distros/k3s/get-remote-k3s-yaml.sh
```

---

# Other Notes

Check out the [`optional`](optional) directory for notes on specific apps

e.g. for postgres on k8s notes, go to [`./optional/postgres/README.md`](./optional/postgres/README.md)

# Contributions and maintainers
- @cloudymax

If you'd like to contribute, feel free to open an issue or pull request and we'll take a look and try to get back to you asap!

# TODO
- install helm for the user. We do it for them. :blue-heart:
- look into https://kubesec.io/
