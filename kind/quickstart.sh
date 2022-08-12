#!/bin/bash -
#===============================================================================
#
#         USAGE: ./quick-start-kind.sh
#
#   DESCRIPTION: Quickly install KIND using the following stack on mac/linux:
#                - KinD (kubernetes in docker)
#                - nginx-ingress-controller (for remote access)
#
#
#        AUTHOR: jesse
#  ORGANIZATION: jessebot
#       CREATED: 02/08/2022 22:24:00
#
#===============================================================================
source .env

# pretty echo so that I don't have ot remember this incantation
function p_echo() {
    echo ""
    echo -e "\t\033[92m❤︎ $1 ❤︎\033[00m"
    echo ""
}

# create the cluster
p_echo "Creating kind cluster..."
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

p_echo "Deploying Nginx Ingress Controller..."
echo "kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml"
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

p_echo "Waiting for nginx ingress controller to roll out..."
echo "kubectl rollout status deployment/nginx-ingress-ingress-nginx-controller -n ingress-nginx"
kubectl rollout status deployment/ingress-nginx-controller -n ingress-nginx
kubectl wait --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=90s -n ingress-nginx
