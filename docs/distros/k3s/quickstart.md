---
layout: default
title: K3s BASH Quickstart
description: "k3s BASH script Quickstart"
parent: K3s
grand_parent: K8s Distros
permalink: /distros/k3s/bash-quickstart
---

## Installing a k3s using a pre-configured BASH script
Best for Linux on metal or a bridged VM

#### Pre-Req
- Have internet access.
- Optional: Install [k9s](https://k9scli.io/topics/install/), which is like `top` for kubernetes clusters, to monitor the cluster.


These can also be set in a .env file in this directory :)

```bash
# IP address pool for metallb, this is where your domains will map
# back to if you use ingress for your cluster, defaults to 8 ip addresses
export CIDR="192.168.42.42-192.168.42.50"

# email address for lets encrypt
export EMAIL="dogontheinternet@coolemails4dogs.com"

# SECTION FOR GRAFANA AND PROMETHEUS
#
# this is for prometheus alert manager
export ALERT_MANAGER_DOMAIN="alert-manager.selfhosting4dogs.com"
# this is for your grafana instance, that is connected to prometheus
export GRAFANA_DOMAIN="grafana.selfhosting4dogs.com"
# this is for prometheus proper, where you'll go to verify exporters are working
export PROMETHEUS_DOMAIN="prometheus.selfhosting4dogs.com"
```

Then you can run the script! :D

```bash
# From the cloned repo dir, This should set up k3s and dependencies
# Will also launch k9s, like top for k8s, To exit k9s, use type :quit
./distros/k3s/bash_full_quickstart.sh
```

#### Ready to clean up this cluster?
To delete the whole cluster, the above k3s install also included an uninstall script that should be in your path already:

```bash
k3s-uninstall.sh
```

## Final Touches

### Port Forwarding
If you want to access an app outside of port forwarding to test, you'll need to make sure your app's ingress is setup correctly and then you'll need to setup your router to port forward 80->80 and 443->443 for your WAN. then setup DNS for your domain if you want the wider internet to access this remotely.

### SSL/TLS

After SSL is working (if it's not, follow the steps in the [cert-manager common error troubleshooting guide](https://cert-manager.io/docs/faq/acme/#common-errors)), you can also change the `letsencrypt-staging` value to `letsencrypt-prod` for any domains you own and can configure to point to your cluster via DNS.


### Remote cluster administration

You can also copy your remote k3s kubeconfig with a little script in `k3s/`:

```bash
# CHANGE THESE TO YOUR OWN DETAILS or not ¯\_(ツ)_/¯
export REMOTE_HOST="192.168.20.2"
export REMOTE_SSH_PORT="22"
export REMOTE_USER="cooluser4dogs"

# this script will totally wipe your kubeconfig :) use with CAUTION
./distros/k3s/get-remote-k3s-yaml.sh
```
