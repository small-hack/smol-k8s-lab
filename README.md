# k8s Homelab

Under construction, but this is where we'll throw some local k8s (kubernetes) testing tools. Currently supported k8s distros, biasing towards small and quick distros:

Distro | k8s Homelab Status |
---|---
[k3s](https://k3s.io/) | in progress - beta | 
[KinD](https://kind.sigs.k8s.io/) | in progress - alpha | 6
[k0s](https://k0sproject.io/) | in progress - alpha coming soon |

# Quickstart

#### Pre-Req

- Install [k9s](https://k9scli.io/topics/install/), which is like `top` for kubernetes clusters, to monitor the cluster.
- Have internet access.

## K3s

All the scripts in this repo should work with the `.env` file in the same directory.
You can copy the `.env_sample` and edit the default values to save some time.

Currently only testing on k3s in the base directory of this repo, but you can run it like this (you probably want to change my default values, but maybe you're a cool admin for dogs too):

```bash
# exports can also be set in .env file
export EMAIL="youremail@coolemailfordogs.com"

# This should set up k3s and some dependencies
cd k3s/ && ./quick-start-k3s.sh
```

## Final Touches

### Port Forwarding
This would forward your app, running on port 80 to 8080 locally, so you can go to http://127.0.0.1:8080/ in your browser

```bash
kubectl port-forward $POD_NAME 80:8080
```

After this, if you want to access this outside of port forwarding to test, you'll need to make sure your app's ingress is setup correctly and then you'll need to setup your router to port forward 80->80 and 443->443 for your WAN. then setup DNS for your domain if you want the wider internet to access this remotely.

## SSL

After SSL is working (if it's not, follow the steps in the [cert-manager common error troubleshooting guide](https://cert-manager.io/docs/faq/acme/#common-errors)), you can also change the `letsencrypt-staging` value to `letsencrypt-prod` for any certs you've installed. 


## Remote cluster administration

You can also copy your remote k3s kubeconfig with a little script in `k3s/`:

```bash
# remote host name or ip address of the k8s cluster
export REMOTE_HOST="192.168.20.2"
# remote port on the host for ssh
export REMOTE_SSH_PORT="22"
# username you use to ssh to that host
export REMOTE_USER="cooluser4dogs"

# this script will totally wipe your kubeconfig :) use with caution
./k3s/get-remote-k3s-yaml.sh
```

---

# Helpful Bits
- The k3s knowledge here is in this [kauri.io self hosting guide](https://kauri.io/#collections/Build%20your%20very%20own%20self-hosting%20platform%20with%20Raspberry%20Pi%20and%20Kubernetes/%2838%29-install-and-configure-a-kubernetes-cluster-w/) is invaluable. Thank you kauri.io.

- This [encrypted secrets in helm charts guide](https://www.thorsten-hans.com/encrypted-secrets-in-helm-charts/) isn't the guide we need, but helm secrets need to be stored somewhere, and vault probably makes sense

# Other Notes

Check out the `optional` directory for notes on specific apps, e.g. for postgres on k8s notes, go to `optional/postgres/README.md`.

## Prometheus notes
Coming soon. Below is kinda broken stuff:
```bash
# install the repo and search it
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

# view the chart details
helm show chart prometheus-community/kube-prometheus-stack
helm show chart prometheus-community/kube-state-metrics

# installation of important charts
helm install prometheus prometheus-community/prometheus
```

## installing cmctl, the cli tool for cert-manager
You'll need to download the tar ball for your OS [here](https://github.com/cert-manager/cert-manager/releases) and then untar it, and move it into a directory in your `$PATH`. MacOS will fail the first time you run it, and you'll need to go into System Preferences > Security & Privacy > Allow apps downloaded from, to allow an exception.
