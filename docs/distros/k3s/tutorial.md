---
layout: default
title: K3s Tutorial
description: "K3s tutorial"
parent: K3s
grand_parent: K8s Distros
permalink: /distros/k3s/tutorial
---

# K3s

## create the k3s cluster (just one server node)
```bash
# skip install of traefik & servicelb
export INSTALL_K3S_EXEC=" --no-deploy servicelb --no-deploy traefik"

# make the kubeconfig copy-able for later
export K3S_KUBECONFIG_MODE="644"

curl -sfL https://get.k3s.io | sh -
```

### Grab the kubeconfig
Copy the k3s kubeconfig to the right place
```bash
mkdir -p ~/.kube
cp /etc/rancher/k3s/k3s.yaml ~/.kube/kubeconfig
# change the permissions os that it doesn't complain
chmod 600 ~/.kube/kubeconfig
```

## add/update all relevant helm repos
Add/update helm repos for metallb, ingress-nginx, cert-manager, prometheus [operator/alert manager/push gateway], and grafana.
```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add metallb https://metallb.github.io/metallb
helm repo add jetstack https://charts.jetstack.io
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

## MetalLb installation
Learn more about metallb [here](https://github.com/metallb/metallb/tree/main/charts/metallb).
```bash
helm install metallb metallb/metallb -n kube-system --wait
```

Wait on metallb to deploy, because sometimes helm wait doesn't do the trick:
```bash
kubectl rollout status -n kube-system deployment/metallb-controller

kubectl wait --namespace kube-system \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/instance=metallb \
  --timeout=120s

kubectl wait --namespace kube-system \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=speaker \
  --timeout=120s
```

Now we can apply the metallb custom resources.... see: https://metallb.universe.tf/configuration/
Sometimes it still fails, but just keep trying, if you get an error for the custom resource not being available:
```bash
cat <<EOF | kubectl apply -f -
  apiVersion: metallb.io/v1beta1
  kind: IPAddressPool
  metadata:
    name: base-pool
    namespace: kube-system
  spec:
    addresses:
      - "$CIDR"
EOF

cat <<EOF | kubectl apply -f -
  apiVersion: metallb.io/v1beta1
  kind: L2Advertisement
  metadata:
    name: base-pool
    namespace: kube-system
EOF
    sleep 3
done
```

## Installing nginx ingress controller
```bash
helm install nginx-ingress ingress-nginx/ingress-nginx --namespace kube-system --set hostNetwork=true --set hostPort.enabled=true
```

wait on nginx ingress controller to deploy
```bash
kubectl rollout status -n kube-system deployment/nginx-ingress-ingress-nginx-controller

kubectl wait --namespace kube-system \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/name=ingress-nginx \
  --timeout=90s
```

## Installing cert-manager
```bash
helm install cert-manager jetstack/cert-manager --namespace kube-system --version v1.9.1 --set installCRDs=true
```

Wait on cert-manager to deploy
```bash
kubectl rollout status -n kube-system deployment/cert-manager
kubectl rollout status -n kube-system deployment/cert-manager-webhook

kubectl wait --namespace kube-system \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/name=cert-manager \
  --timeout=90s
kubectl wait --namespace kube-system \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=webhook \
  --timeout=90s
```

### Install a ClusterIssuer so that cert-manager can issue certs

#### Self Signed Issuer
```bash
    cat <<EOF | kubectl apply -f -
    apiVersion: cert-manager.io/v1
    kind: ClusterIssuer
    metadata:
      name: selfsigned-cluster-issuer
    spec:
      selfSigned: {}
```
#### lets-encrypt staging Issuer
```bash
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
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
EOF
```

## Installing prometheus

```bash
helm install prometheus prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace \
    --set alertmanager.ingress.enabled=true \
    --set alertmanager.ingress.ingressClassName=nginx \
    --set alertmanager.ingress.hosts[0]=$ALERT_MANAGER_DOMAIN \
    --set grafana.ingress.enabled=true \
    --set grafana.ingress.ingressClassName=nginx \
    --set grafana.ingress.hosts[0]=$GRAFANA_DOMAIN \
    --set prometheus.ingress.enabled=true \
    --set prometheus.ingress.ingressClassName=nginx \
    --set prometheus.ingress.hosts[0]=$PROMETHEUS_DOMAIN
```
