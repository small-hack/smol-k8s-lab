---
layout: default
title: Kind BASH Quickstart
description: "KinD BASH scripts Quickstart"
parent: Kind
permalink: /distros/kind/quickstart
---

## Installing a KinD using a pre-configured BASH script
Best path for non-prod testing across linux and macOS

```bash
# this export can also be set in a .env file in the same dir
export EMAIL="youremail@coolemail4dogs.com"

# From the cloned repo dir, This should set up KinD for you
# Will also launch k9s, like top for k8s, To exit k9s, use type :quit
./k8s_homelab/kind/bash_full_quickstart.sh
```

#### Ready to clean up this cluster?
To delete the whole cluster, run:

```bash
kind delete cluster
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
./k3s/get-remote-k3s-yaml.sh
```
