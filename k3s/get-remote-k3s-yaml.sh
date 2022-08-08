#!/bin/bash -
#===============================================================================
#
#         USAGE: ./get-remote-k3s-yaml.sh
#
#   DESCRIPTION: Get the remote k3s kubeconfig and install it for use with lens
#
#        AUTHOR: jesse
#  ORGANIZATION: jessebot
#       CREATED: 04/08/2022 22:24:00
#
#===============================================================================
source .env

echo -e "\033[92m Going to get your k3s.yaml from $REMOTE_USER@$REMOTE_HOST on port $REMOTE_SSH_PORT \033[00m"
echo ""

# can't use mkdir -p on macOS, but this directory often isn't present on any OS
mkdir ~/.kube > /dev/null

# pull the actual file via ssh copy
echo "scp -P $REMOTE_SSH_PORT $REMOTE_USER@$REMOTE_HOST:/etc/rancher/k3s/k3s.yaml ~/.kube/kubeconfig"
scp -P $REMOTE_SSH_PORT $REMOTE_USER@$REMOTE_HOST:/etc/rancher/k3s/k3s.yaml ~/.kube/kubeconfig

# this removes localhost and replaces it with the name of the remote host
echo "doing sed -i on localhost to remote host ip"
sed -i "s/127.0.0.1/${REMOTE_HOST}/g" ~/.kube/kubeconfig

# make permissions correct for use locally via kubectl
echo "chmod 600 ~/.kube/kubeconfig"
chmod 600 ~/.kube/kubeconfig

# print out the kubeconfig to manually add to lens
echo ""
echo -e "\033[92m------------- KUBECONFIG --------------\033[00m"
echo ""
cat ~/.kube/kubeconfig
echo ""
