Coredns ships by default with k3s, so it gets installed, but not really by anything we do by default 😅

### Troubleshooting networking issues with coredns
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
STOP USING MULTIPLE SUBDOMAINS ON YOUR LOCAL ROUTER. Get a pihole and use it for both DNS and DHCP. Message brought to you by two engineers who lost a day to troubleshooting this.
