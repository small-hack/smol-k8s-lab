---
layout: default
title: coredns
description: "Troubleshooting Core DNS notes"
parent: Troubleshooting
permalink: /troubleshooting/coredns
---


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

---

# Other Notes

Check out the [`optional`](optional) directory for notes on specific apps

e.g. for postgres on k8s notes, go to [`./optional/postgres/README.md`](./optional/postgres/README.md)

Want to get started with argocd? If you've installed it via smol_k8s_homelab, then you can jump to here:
https://github.com/jessebot/argo-example#argo-via-the-gui

Otherwise, if you want to start from scratch, start here: https://github.com/jessebot/argo-example#argocd

Where is your persistent volume data? If you used the local path provisioner it is here:
`/var/lib/rancher/k3s/storage`

### Helpful links
- The k3s knowledge here is in this [kauri.io self hosting guide](https://kauri.io/#collections/Build%20your%20very%20own%20self-hosting%20platform%20with%20Raspberry%20Pi%20and%20Kubernetes/%2838%29-install-and-configure-a-kubernetes-cluster-w/) is invaluable. Thank you kauri.io.

- This [encrypted secrets in helm charts guide](https://www.thorsten-hans.com/encrypted-secrets-in-helm-charts/) isn't the guide we need, but helm secrets need to be stored somewhere, and vault probably makes sense

- Running into issues with metallb assigning IPs, but them some of them not working with nginx-ingress controller? This person explained it really well, but it required hostnetwork to be set on the nginx-ingress chart values.yml. Check out thier guide [here](https://ericsmasal.com/2021/08/nginx-ingress-load-balancer-and-metallb/).

### Why am I getting deprecation notices on certain apps?
If you have the krew deprecations plugin installed, then you might get something like this:
```
Deleted APIs:

PodSecurityPolicy found in policy/v1beta1
	 ├─ API REMOVED FROM THE CURRENT VERSION AND SHOULD BE MIGRATED IMMEDIATELY!!
		-> GLOBAL: metallb-controller
		-> GLOBAL: metallb-speaker
```
For Metallb, that's because of this: https://github.com/metallb/metallb/issues/1401#issuecomment-1140806861
It'll be fixed in October of 2022.

### Troubleshooting hellish networking issues with coredns
Can your pod not get out to the internet? Well, first verify that it isn't the entire cluster with this:
```bash
kubectl run -it --rm --image=infoblox/dnstools:latest dnstools
```

Check the `/etc/resolv.conf` and `/etc/hosts` that's been provided by coredns from that pod with:
```bash
cat /etc/resolv.conf
cat /etc/hosts

# also check if this returns linuxfoundation's info correct
# cross check this with a computer that can hit linuxfoundation.org with no issues
host linuxfoundation.org
```

If it doesn't return [linuxfoundation.org](linuxfoundation.org)'s info, you should first go read this [k3s issue](https://github.com/k3s-io/k3s/issues/53) (yes, it's present in KIND as well).

Then decide, "*does having subdomains on my LAN spark joy?*"

#### Yes it sparks joy
And then update your `ndot` option in your `/etc/resolv.conf` for podDNS to be 1. You can do this in a deployment. You should read this [k8s doc](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/#pod-dns-config) to learn more. The search domain being more than 1-2 dots deep seems to cause all sorts of problems. You can test the `resolv.conf` with the infoblox/dnstools docker image from above. It already has the `vi` text editor, which will allow you to quickly iterate.

#### No, it does not spark joy
STOP USING MULTIPLE SUBDOMAINS ON YOUR LOCAL ROUTER. Get a pihole and use it for both DNS and DHCP.
