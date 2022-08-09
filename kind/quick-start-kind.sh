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

# Set up cert manager
p_echo "helm install cert-manager jetstack/cert-manager --namespace kube-system \ "
p_echo "  --version v1.9.1 --set installCRDs=true --values cert-manager_values.yml"
helm install cert-manager jetstack/cert-manager --namespace kube-system --version v1.9.1 --set installCRDs=true --values cert-manager_values.yml

# wait on cert-manager to deploy
p_echo "kubectl rollout status -n kube-system deployment/cert-manager"
kubectl rollout status -n kube-system deployment/cert-manager
kubectl rollout status -n kube-system deployment/cert-manager-webhook

p_echo "waiting on cert-manager"
kubectl wait --namespace kube-system \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/name=cert-manager \
  --timeout=90s
kubectl wait --namespace kube-system \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=webhook \
  --timeout=90s

p_echo "Installing clusterissuer resource for cert manager to work"
p_echo "while looping on applying cluster issue CR..."
cert_manager_apply_exit_code=1
while [ $cert_manager_apply_exit_code -ne 0 ]; do
    simple_loading_bar 2
    p_echo "Trying to do a kube apply on this clusterissuer CR for cert-manager..."
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
    cert_manager_apply_exit_code=$?
done
