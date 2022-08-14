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

# make sure kind is installed ^_^;
which kind > /dev/null
# if the above command does not return 0...
if [ $? -ne 0 ]; then
    p_echo "Looks like you don't have KIND installed. I'll get this installed for you :3"
    brew install kind
    if [ $? -ne 0 ]; then
        p_echo "Oh no! You don't have brew installed either D: You can install it with this command"
        echo '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        # fail out
        return 1
    fi
fi

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

## add/update helm repo for metallb
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
          - "192.168.42.42"
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

p_echo "Deploying Nginx Ingress Controller..."
echo "kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml"
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

p_echo "Waiting for nginx ingress controller to roll out..."
echo "kubectl rollout status deployment/nginx-ingress-ingress-nginx-controller -n ingress-nginx"
kubectl rollout status deployment/ingress-nginx-controller -n ingress-nginx
kubectl wait --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=90s -n ingress-nginx
