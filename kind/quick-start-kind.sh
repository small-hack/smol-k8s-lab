#!/bin/bash -
#===============================================================================
#
#         USAGE: ./quick-start-kind.sh
#
#   DESCRIPTION: Quickly install KIND using the following stack on mac/linux:
#                KinD (kubernetes in docker), nginx-ingress-controller (for remote access),
#                and cert-manager (automatic SSL) :)
#
#        AUTHOR: jesse
#  ORGANIZATION: jessebot
#       CREATED: 02/08/2022 22:24:00
#
#===============================================================================
source .env

# add/update all relevant helm repos
echo -e "\033[92m Add/update helm repos for ingress-nginx, and cert-manager.\033[00m"
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add jetstack https://charts.jetstack.io
helm repo update

# create the cluster
echo -e "\033[92m Creating kind cluster...\033[00m"
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

# KIND only - set up nginx ingress deployment
echo "deploying nginx ingress controller...."
echo -e "\033[92m kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml \033[00m"
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# wait on nginx ingress controller to deploy
echo -e "\033[92m kubectl rollout status deployment/nginx-ingress-ingress-nginx-controller \033[00m"
kubectl rollout status deployment/nginx-ingress-ingress-nginx-controller
kubectl wait --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=90s

# Set up cert manager
echo -e "\033[92m kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.9.1/cert-manager.yaml \033[00m"
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.9.1/cert-manager.yaml

cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1alpha2
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    email: $EMAIL
    server: https://acme-v02.api.letsencrypt.org/directory
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
