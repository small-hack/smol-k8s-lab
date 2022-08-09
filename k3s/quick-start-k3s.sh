#!/bin/bash -
#===============================================================================
#
#         USAGE: ./quick-start-k3s.sh
#          ARGS: --no-k9s - don't start k9s, top 4 kubernetes, at end of script
#
#   DESCRIPTION: Quickly install k3s using the following stack on Linux:
#                k3s (kubernetes distribution), metallb (load balancer),
#                and cert-manager (automatic SSL)
#
#        AUTHOR: jesse, max
#  ORGANIZATION: @jessebot + @cloudymax
#       CREATED: 04/08/2022 22:24:00
#
#===============================================================================

source .env

# etremely simply loading bar
function simple_loading_bar() {
    echo ""
    for i in $(seq 1 $1); do
        echo -n "   ¯\_(ツ)_/¯";
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

# skip install of traefik & servicelb, specify flannel backend
# export INSTALL_K3S_EXEC=" --no-deploy servicelb --no-deploy traefik --flannel-backend host-gw"
export INSTALL_K3S_EXEC=" --no-deploy servicelb --no-deploy traefik"
# make the kubeconfig copy-able for later
export K3S_KUBECONFIG_MODE="644"

# create the k3s cluster (just one server node)
p_echo "curl -sfL https://get.k3s.io | sh -"
curl -sfL https://get.k3s.io | sh -

# Grab the kubeconfig
p_echo "cp the k3s kubeconfig to the right place"
mkdir -p ~/.kube
cp /etc/rancher/k3s/k3s.yaml ~/.kube/kubeconfig
# change the permissions os that it doesn't complain
chmod 600 ~/.kube/kubeconfig

# add/update all relevant helm repos
p_echo "Add/update helm repos for metallb, ingress-nginx, cert-manager, prometheus [operator/alert manager/push gateway], and grafana."
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add metallb https://metallb.github.io/metallb
helm repo add jetstack https://charts.jetstack.io
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# metal lb installation: https://github.com/metallb/metallb/tree/main/charts/metallb
p_echo "helm install metallb metallb/metallb -n kube-system"
helm install metallb metallb/metallb -n kube-system

# wait on metallb to deploy
p_echo "kubectl rollout status -n kube-system deployment/metallb-controller"
kubectl rollout status -n kube-system deployment/metallb-controller

p_echo "Waiting on metallb controller and speaker, just to be sure"
kubectl wait --namespace kube-system \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/instance=metallb \
  --timeout=120s

kubectl wait --namespace kube-system \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=speaker \
  --timeout=120s

# metallb custom resources.... https://metallb.universe.tf/configuration/
p_echo "Applying metallb custom resources"
kubectl apply -f metallb_cr.yml
apply_exit_code=$?
while [ $apply_exit_code -ne 0 ]; do
    p_echo "Kube apply failed. Will loop on applying the metallb CR..."
    p_echo "Sleeping 3 seconds before trying again."
    simple_loading_bar 3
    p_echo "kubectl apply -f metallb_cr.yml"
    kubectl apply -f metallb_cr.yml
    apply_exit_code=$?
done

# installing nginx
p_echo "helm install nginx-ingress ingress-nginx/ingress-nginx --namespace kube-system"
helm install nginx-ingress ingress-nginx/ingress-nginx --namespace kube-system

# wait on nginx ingress controller to deploy
p_echo "kubectl rollout status -n kube-system deployment/nginx-ingress-ingress-nginx-controller"
kubectl rollout status -n kube-system deployment/nginx-ingress-ingress-nginx-controller

p_echo "waiting on nginx"
kubectl wait --namespace kube-system \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/name=ingress-nginx \
  --timeout=90s

# Set up cert manager
p_echo "helm install cert-manager jetstack/cert-manager --namespace kube-system --version v1.9.1 --set installCRDs=true --set podDnsPolicy='None' --values cert-manager_values.yml"
helm install cert-manager jetstack/cert-manager --namespace kube-system --version v1.9.1 --set installCRDs=true --set podDnsPolicy="None" --values cert-manager_values.yml

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

p_echo "Deploying prometheus so that we can monitor the cluster later:"
p_echo "helm install prometheus prometheus-community/prometheus --create-namespace --namespace monitoring"
helm install prometheus prometheus-community/prometheus --create-namespace --namespace monitoring

p_echo "helm install grafana grafana/grafana  -–namespace monitoring -–set persistence.enabled=true –-set adminPassword="niceP@ssword4Dog5" --values grafana_values.yml"
helm install grafana grafana/grafana --namespace monitoring --values grafana_values.yml

if [ "$1" == "--no-k9s" ]; then
    echo "We're all done!"
    kubectl get pods -A
else
    k9s -A
fi
