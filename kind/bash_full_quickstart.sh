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
# IP address pool for metallb, this is where your domains will map
# back to if you use ingress for your cluster, defaults to 8 ip addresses
# export CIDR="192.168.42.42-192.168.42.50"

# email address for lets encrypt
# export EMAIL="dogontheinternet@coolemails4dogs.com"

# this is for argocd
# ARGOCD_DOMAIN="argocd.selfhostingfordogs.com"

# this is for prometheus alert manager
# export ALERT_MANAGER_DOMAIN="alert-manager.selfhostingfordogs.com"
# this is for your grafana instance, that is connected to prometheus
# export GRAFANA_DOMAIN="grafana.selfhostingfordogs.com"
# this is for prometheus proper, where you'll go to verify # exporters are working
# export PROMETHEUS_DOMAIN="prometheus.selfhostingfordogs.com"

. .env

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

# add/update relevant helm repo
p_echo " Add/update helm repos for cert-manager."
helm repo add jetstack https://charts.jetstack.io
helm repo add metallb https://metallb.github.io/metallb
helm repo update

## MetalLb installation
p_echo "helm install metallb metallb/metallb -n kube-system --wait"
helm install metallb metallb/metallb -n kube-system --wait

p_echo "Wait on metallb to deploy, because sometimes helm wait doesn't do the trick"
kubectl rollout status -n kube-system deployment/metallb-controller

kubectl wait --namespace kube-system \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/instance=metallb \
  --timeout=120s

kubectl wait --namespace kube-system \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=speaker \
  --timeout=120s

apply_exit_code=1
while [ $apply_exit_code -ne 0 ]; do
    p_echo "Running 'kubectl apply -f' for metallb IPAddressPool"
    echo $CIDR
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
    apply_exit_code=$?
    p_echo "Running 'kubectl apply -f' for metallb L2Advertisement"
    cat <<EOF | kubectl apply -f -
      apiVersion: metallb.io/v1beta1
      kind: L2Advertisement
      metadata:
        name: base-pool
        namespace: kube-system
EOF
    simple_loading_bar 3
done


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


if [ "$1" == "--no-k9s" ]; then
    echo "We're all done!"
    kubectl get pods -A
else
    k9s -A
fi
