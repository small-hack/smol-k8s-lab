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
