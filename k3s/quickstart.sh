#!/bin/bash -
#===============================================================================
#
#         USAGE: ./quickstart.sh
#
#   DESCRIPTION: Quickly install k3s without traefik and servicelb
#
#        AUTHOR: jesse, max
#  ORGANIZATION: @jessebot + @cloudymax
#       CREATED: 04/08/2022 22:24:00
#
#===============================================================================

# pretty echo so that I don't have ot remember this incantation
function p_echo() {
    echo "--------------------------------ʕ·ᴥ·ʔ---------------------------------"
    echo ""
    echo -e "\t\033[92m$1\033[00m"
    echo ""
}

# skip install of traefik & servicelb, specify flannel backend
export INSTALL_K3S_EXEC=" --no-deploy servicelb --no-deploy traefik"
# make the kubeconfig copy-able for later
export K3S_KUBECONFIG_MODE="644"

# create the k3s cluster (just one server node)
p_echo "curl -sfL https://get.k3s.io | sh -"
curl -sfL https://get.k3s.io | sh -

# Grab the kubeconfig and copy it locally
p_echo "copying the k3s kubeconfig to the right place"
mkdir -p ~/.kube
cp /etc/rancher/k3s/k3s.yaml ~/.kube/kubeconfig
# change the permissions os that it doesn't complain
chmod 600 ~/.kube/kubeconfig
