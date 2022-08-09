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

# skip install of traefik & servicelb, specify flannel backend
# export INSTALL_K3S_EXEC=" --no-deploy servicelb --no-deploy traefik --flannel-backend host-gw"
export INSTALL_K3S_EXEC=" --no-deploy servicelb --no-deploy traefik"
# make the kubeconfig copy-able for later
export K3S_KUBECONFIG_MODE="644"

# create the k3s cluster (just one server node)
echo -e "\033[92m curl -sfL https://get.k3s.io | sh - \033[00m"
curl -sfL https://get.k3s.io | sh -

# Grab the kubeconfig
echo -e "\033[92m cp the k3s kubeconfig to the right place \033[00m"
mkdir -p ~/.kube
cp /etc/rancher/k3s/k3s.yaml ~/.kube/kubeconfig
# change the permissions os that it doesn't complain
chmod 600 ~/.kube/kubeconfig

# add/update all relevant helm repos
echo -e "\033[92m Add/update helm repos for metallb, ingress-nginx, and cert-manager.\033[00m"
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add metallb https://metallb.github.io/metallb
helm repo add jetstack https://charts.jetstack.io
helm repo update

# metal lb installation: https://github.com/metallb/metallb/tree/main/charts/metallb
echo -e "\033[92m helm install metallb metallb/metallb -n kube-system \033[00m"
helm install metallb metallb/metallb -n kube-system

# wait on metallb to deploy
echo -e "\033[92m kubectl rollout status -n kube-system deployment/metallb-controller \033[00m"
kubectl rollout status -n kube-system deployment/metallb-controller

echo -e "\033[92m Waiting on metallb controller and speaker, just to be sure \033[00m"
kubectl wait --namespace kube-system \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/instance=metallb \
  --timeout=120s

kubectl wait --namespace kube-system \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=speaker \
  --timeout=120s

# metallb custom resources.... https://metallb.universe.tf/configuration/
echo -e "\033[92m Applying metallb custom resources \033[00m"
apply_exit_code=1
echo -e "\033[92m while looping on metallb CR applying... \033[00m"
while [ $apply_exit_code -ne 0 ]; do
    sleep 2
    echo -e "\033[92m Trying to do a kube apply on this metallb CR again...\033[00m"
    kubectl apply -f metallb_cr.yml
    apply_exit_code=$?
done

# installing nginx
echo -e "\033[92m helm install nginx-ingress ingress-nginx/ingress-nginx --namespace kube-system \033[00m"
helm install nginx-ingress ingress-nginx/ingress-nginx --namespace kube-system

# wait on nginx ingress controller to deploy
echo -e "\033[92m kubectl rollout status -n kube-system deployment/nginx-ingress-ingress-nginx-controller \033[00m"
kubectl rollout status -n kube-system deployment/nginx-ingress-ingress-nginx-controller

echo -e "\033[92m waiting on nginx \033[00m"
kubectl wait --namespace kube-system \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/name=ingress-nginx \
  --timeout=90s

# Set up cert manager
echo -e "\033[92m helm install cert-manager jetstack/cert-manager --namespace kube-system --version v1.9.1 --set installCRDs=true --set cert-manager_values.yml \033[00m"
helm install cert-manager jetstack/cert-manager --namespace kube-system --version v1.9.1 --set installCRDs=true --set podDnsPolicy="None" --values cert-manager_values.yml

# wait on cert-manager to deploy
echo -e "\033[92m kubectl rollout status -n kube-system deployment/cert-manager \033[00m"
kubectl rollout status -n kube-system deployment/cert-manager
kubectl rollout status -n kube-system deployment/cert-manager-webhook

echo -e "\033[92m waiting on cert-manager \033[00m"
kubectl wait --namespace kube-system \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/name=cert-manager \
  --timeout=90s
kubectl wait --namespace kube-system \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=webhook \
  --timeout=90s

echo -e "\033[92m Installing clusterissuer resource for cert manager to work \033[00m"
echo -e "\033[92m while looping on applying cluster issue CR... \033[00m"
cert_manager_apply_exit_code=1
while [ $cert_manager_apply_exit_code -ne 0 ]; do
    sleep 2
    echo -e "\033[92m Trying to do a kube apply on this clusterissuer CR for cert-manager again...\033[00m"
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

sleep 2

if [ "$1" == "--no-k9s" ]; then
    echo "We're all done!"
    kubectl get pods -A
else
    k9s -A
fi
