
---
layout: default
title: K0s Tutorial
description: "K0s Tutorial"
parent: K0s
grand_parent: K8s Distros
permalink: /distros/k0s/tutorial
---

# Install K0s from Scratch

k0s is a single-binary, 100% upstream, FOSS() Kuberntes Distro. [Docs](https://docs.k0sproject.io/v1.24.3+k0s.0/)

  - Made by [Mirantis](https://www.mirantis.com/) - who are the [owners of docker](https://www.mirantis.com/company/press-center/company-news/mirantis-acquires-docker-enterprise/), and creators of [Lens](https://k8slens.dev/).
  - Deploy as single-node, multi-node, airgap or Docker
  - Lifecycle management with k0sctl: upgrade, backup and restore
  - Control plane isolation as default
  - Horizontally Scalable
  - (CNI) plugins Kube-Router is the default, Calico is the alternative). No Flannel.
  - Supports all Kubernetes storage options with Container Storage Interface (CSI)
  - Datastore backends: etcd is default for multi-node clusters, SQLite is default for single node clusters. Also supports MySQL, and PostgreSQL.
  - Includes Konnectivity service, CoreDNS and Metrics Server

## Install

* Add Helm Repos

  ```bash
  helm repo add metallb https://metallb.github.io/metallb
  helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
  helm repo add jetstack https://charts.jetstack.io
  helm repo update
  ```

* Install & start a single-node k0s cluster

    ```bash
    curl -sSLf https://get.k0s.sh | sudo sh
    sudo k0s install controller --single
    sudo k0s start
    ```

* Grab an admin kubeconfig and watch the pods come up

    ```bash
    mkdir -p $HOME/.kube/
    sudo k0s kubeconfig admin > $HOME/.kube/k0s
    chown $USER:$USER $HOME/.kube/k0s
    chmod 600 $HOME/.kube/k0s
    export KUBECONFIG=$HOME/.kube/k0s
    ```

    ```bash
    # k0s is a bit slower than k3s. 
    # It can take nearly a minute to see pods start appearing
    watch -n1 'sudo k0s kubectl get pods --all-namespaces'
    ```

* Apply annotations to the `kube-system` namespace

    ```yaml
    cat <<EOF | kubectl apply -f -
    apiVersion: v1
    kind: Namespace
    metadata:
      name: kube-system
      labels:
        pod-security.kubernetes.io/enforce: privileged
        pod-security.kubernetes.io/audit: privileged
        pod-security.kubernetes.io/warn: privileged
    EOF
    ```

* Install MetalLB and create an IP pool.

  ```bash
  helm install metallb metallb/metallb -n kube-system

  # wait until the pods are ready
  cat <<EOF | kubectl apply -f -
  apiVersion: metallb.io/v1beta1
  kind: IPAddressPool
  metadata:
    name: main-pool
    namespace: kube-system
  spec:
    addresses:
      - 192.168.50.101-192.168.50.110
  EOF
  ```

* Install the Nginx-Ingress Controller

  ```bash
  helm install nginx-ingress \
    ingress-nginx/ingress-nginx \
    --namespace kube-system
  ```

* Install Cert-Manager

  * Create a Pod DNS config

    ```bash
    cat <<EOF > cm-values.yaml
    # Optional DNS settings, useful if you have a public and private DNS zone for
    # the same domain on Route 53. What follows is an example of ensuring
    # cert-manager can access an ingress or DNS TXT records at all times.
    # NOTE: This requires Kubernetes 1.10 or `CustomPodDNS` feature gate enabled for
    # the cluster to work.
    # podDnsPolicy: "None"
    podDnsConfig:
      nameservers:
        - "1.1.1.1"
        - "8.8.8.8"
    EOF
    ```

  * Install via helm

    ```bash
    helm install cert-manager \
      jetstack/cert-manager \
      --namespace kube-system \
      --create-namespace \
      --set installCRDs=true \
      --set podDNSPolicy="None" \
      --values cm-values.yaml
    ```

  * Create a Cluster-Issuer

    ```bash
    export EMAIL="you@email.com"

    cat <<EOF | kubectl apply -f -
    apiVersion: cert-manager.io/v1
    kind: ClusterIssuer
    metadata:
      name: letsencrypt-staging
      namespace: kube-system
    spec:
      acme:
        email: $EMAIL
        server: https://acme-staging-v02.api.letsencrypt.org/directory
        privateKeySecretRef:
          name: letsencrypt-staging
        solvers:
          - http01:
              ingress:
                class: nginx
    ---
    apiVersion: cert-manager.io/v1
    kind: Certificate
    metadata:
      name: letsencrypt-staging
      namespace: kube-system
    spec:
      isCA: true
      commonName: letsencrypt-staging
      secretName: letsencrypt-staging
      issuerRef:
        name: letsencrypt-staging
        kind: ClusterIssuer
        group: cert-manager.io
    EOF
    ```  

## Cleanup

  ```bash
  sudo k0s stop
  sudo k0s reset
  sudo reboot now
  ```
