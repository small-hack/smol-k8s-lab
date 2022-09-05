---
layout: default
title: Kind Tutorial
description: "Kind Tutorial"
parent: Kind
permalink: /distros/kind/tutorial
---

# Quickly install KIND using the following stack on mac/linux
- KinD (kubernetes in docker)
- nginx-ingress-controller (for remote access)
- cert-manager (automatic SSL)

#### PreReq
- [Install KIND](https://formulae.brew.sh/formula/kind#default) (`brew install kind`)

**Optional:**
- [k9s](https://k9scli.io/) (`brew install k9s`)

## add/update metallb and cert-manager helm repos
```bash
helm repo add metallb https://metallb.github.io/metallb
helm repo add jetstack https://charts.jetstack.io
helm repo update
```

## Create the kind cluster
```bash
cat <<EOF | kind create cluster --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
EOF
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

## Deploy the Nginx Ingress Controller

Kind has a special deploy.yml maintained by the kuberentes project that makes this really easy:

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
```

Wait on nginx ingress controller to deploy:

```bash
kubectl rollout status deployment/ingress-nginx-controller -n ingress-nginx
kubectl wait --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=90s -n ingress-nginx
```

## Set up cert manager

*Don't forget the `--set installCRDs=true`!*
```bash
helm install cert-manager jetstack/cert-manager \
    --namespace kube-system \
    --version v1.9.1 \
    --set installCRDs=true 
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

You can also use [k9s]() to monitor the cluster and wait for resources to come up.

### Installing ClusterIssuer Resource
After cert-manager is completely up, you can apply this if you're going to test with external internet facing hosts:
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

That's it :)
