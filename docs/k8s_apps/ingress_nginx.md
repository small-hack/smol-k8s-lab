[ingress-nginx](https://github.com/kubernetes/ingress-nginx) needs no introduction, but that won't stop us! ingress-nginx is an Ingress controller for Kubernetes using [NGINX](https://nginx.org/) as a reverse proxy and load balancer. We use it, instead of traefik, because we know nginx, you know nginx, and none of us have time to learn traefik (but that could change in the future 🤷).

`smol-k8s-lab` will install ingress-nginx by default with no special options. If you're using kind, we install it initially via manifests, and if you're using k3d/k3s, we initially install it via helm.

No matter the distro, Argo CD takes over managing ingress-nginx using our [ingress Argo CD Application](https://github.com/small-hack/argocd-apps/tree/main/ingress) which also bundles cert manager.

!!! Tip
    Do not confuse [ingress-nginx](https://github.com/kubernetes/ingress-nginx) with [nginx-ingress](https://docs.nginx.com/nginx-ingress-controller/). They are confusingly named, but ingress-nginx is a project by Kubernetes. nginx-ingress is a project by NGINX. They're both Ingress controllers for Kubernetes, but the latter has paid features and the former does not. Googling for docs is a bit awful 🤦
