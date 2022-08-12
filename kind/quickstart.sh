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
# extremely simply loading bar
function simple_loading_bar() {
    echo ""
    echo "          "
    for i in $(seq 1 $1); do
        echo -n "    ❤︎"
        echo -n "   ☕"
        sleep 1
    done
    echo ""
}

# pretty echo so that I don't have ot remember this incantation
function p_echo() {
    echo ""
    echo -e "\033[92m  $1 \033[00m"
    echo ""
}

# add/update all relevant helm repos
p_echo " Add/update helm repos for ingress-nginx, and cert-manager."
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add jetstack https://charts.jetstack.io
helm repo update

# create the cluster
p_echo " Creating kind cluster..."
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
p_echo " kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml "
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# wait on nginx ingress controller to deploy
p_echo " kubectl rollout status deployment/nginx-ingress-ingress-nginx-controller "
kubectl rollout status deployment/ingress-nginx-controller -n ingress-nginx
kubectl wait --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=90s -n ingress-nginx
