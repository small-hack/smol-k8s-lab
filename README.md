# Smol K8s Homelab

Under construction, but this is where we'll throw some local k8s (kubernetes) testing tools. This is aimed at getting up and running quickly, but there's also full tutorials linked in `README.md` for each distro's directory, if you'd like to learn the commands at your terminal. These tutorials assume you're on Linux or macOS.

Currently supported k8s distros, biasing towards small and quick distros.

| Distro                           | Smol K8s Homelab Support|          Tutorial               |           Quickstart BASH script             |
|:--------------------------------:|:-----------------------:|:-------------------------------:|:--------------------------------------------:|
|[k3s](https://k3s.io/)            | beta                    | [Working](./k3s/README.md)      |   [Working](./k3s/bash_full_quickstart.sh)   |
|[KinD](https://kind.sigs.k8s.io/) | beta                    | [coming soon](./kind/README.md) |        [beta](./kind/bash_full_quickstart.sh)|
|[k0s](https://k0sproject.io/)     | soon                    | [available](./k0s/README.md)    |      coming soon                             |


## Quickstart in Python
This is aimed at being a much more scalable experience, but is still being worked on. So far, it works for k3s.

#### Pre-Req
- Install [k9s](https://k9scli.io/topics/install/), which is like `top` for kubernetes clusters, to monitor the cluster.
- Have Python 3.9 or higher installed as well as pip3
- Have internet access.

```bash
# install the requirements
pip3 install -r requirements.txt

# test to make sure the script loads
./smol-k8s-homelab.py --help
```

### Install distro with python script
Currently only being tested with k3s, but soon you can do other distros listed above. In the meantime, use the tutorials and BASH scripts linked above
```
# you can replace k3s with kind in the future
./smol-k8s-homelab.py --k8s k3s
```

## Quickstart in BASH
#### Pre-Req
- Install [k9s](https://k9scli.io/topics/install/), which is like `top` for kubernetes clusters, to monitor the cluster.
- Have internet access.

## Choose a k8s distro 
  
<details>
  <summary>K3s - (Best for Linux on metal or a bridged VM)</summary>

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
    export ALERT_MANAGER_DOMAIN="alert-manager.selfhostingfordogs.com"
    # this is for your grafana instance, that is connected to prometheus
    export GRAFANA_DOMAIN="grafana.selfhostingfordogs.com"
    # this is for prometheus proper, where you'll go to verify exporters are working
    export PROMETHEUS_DOMAIN="prometheus.selfhostingfordogs.com"
  ```

  Then you can run the script! :D

  ```bash
    # From the cloned repo dir, This should set up k3s and dependencies
    # Will also launch k9s, like top for k8s, To exit k9s, use type :quit
    ./k8s_homelab/k3s/bash_quickstart.sh
  ```

  #### Ready to clean up this cluster?
  To delete the whole cluster, the above k3s install also included an uninstall script that should be in your path already:

  ```bash
    k3s-uninstall.sh
  ```

</details>

<details>
  <summary>KinD - (Best path for non-prod testing across linux and macOS)</summary>

  ```bash
    # this export can also be set in a .env file in the same dir
    export EMAIL="youremail@coolemailfordogs.com"

    # From the cloned repo dir, This should set up KinD for you
    # Will also launch k9s, like top for k8s, To exit k9s, use type :quit
    ./k8s_homelab/kind/bash_quickstart.sh
  ```

  #### Ready to clean up this cluster?
  To delete the whole cluster, run:

  ```bash
    kind delete cluster
  ```

</details>

<details>
  <summary>K0s - (best for large multinode/GPU passthrough)</summary>

  Still being developed, but will probably look something like....

  ```bash
    # this export can also be set in a .env file in the same dir
    export EMAIL="youremail@coolemailfordogs.com"
    
    # From the cloned repo dir, This should set up KinD for you
    # Will also launch k9s, like top for k8s, To exit k9s, use type :quit
    ./k8s_homelab/k0s/bash_quickstart.sh
  ```

  #### Ready to clean up this cluster?
  To delete the whole cluster, run:

  ```bash
    ???
  ```

</details>

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

### Helpful links
- The k3s knowledge here is in this [kauri.io self hosting guide](https://kauri.io/#collections/Build%20your%20very%20own%20self-hosting%20platform%20with%20Raspberry%20Pi%20and%20Kubernetes/%2838%29-install-and-configure-a-kubernetes-cluster-w/) is invaluable. Thank you kauri.io.

- This [encrypted secrets in helm charts guide](https://www.thorsten-hans.com/encrypted-secrets-in-helm-charts/) isn't the guide we need, but helm secrets need to be stored somewhere, and vault probably makes sense

- Running into issues with metallb assigning IPs, but them some of them not working with nginx-ingress controller? This person explained it really well, but it required hostnetwork to be set on the nginx-ingress chart values.yml. Check out thier guide [here](https://ericsmasal.com/2021/08/nginx-ingress-load-balancer-and-metallb/).

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
STOP USING SUBDOMAINS ON YOUR LOCAL ROUTER. Get a pihole and use it for both DNS and DHCP.



