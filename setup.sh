#!/bin/bash -
#=============================================================================
#         USAGE: ./setup.sh
#   DESCRIPTION: Setup the dependencies for the smol k8s lab
#  REQUIREMENTS: python3.10, brew
#        AUTHOR: Jessebot
#       CREATED: 10/11/2022 08:35:56 AM
#=============================================================================

# Treat unset variables as an error
set -o nounset

# if `which pip3.10` returns a path
if [ -n "$(which pip3.10)" ]; then
    echo -e "\nInstalling python dependencies...\n"
    pip3.10 install -r requirements.txt
else
    echo -e "\nPlease install pip3.10 and rerun the script.\n"
fi

# if `which brew` returns a path
if [ -n "$(which brew)" ]; then
    echo -e "\nInstalling/Updating brew dependencies...\n"
    brew update
    brew bundle --file=./deps/Brewfile
    brew upgrade
    echo -e "\nbrew dependencies installed."
else
    echo -e "\nBrew not installed."
    echo -e "\nPlease install brew by running the following command:"
    echo '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    echo -e "\nThen you can run the setup.sh script again."
fi

# if kubectl installed
if [ -n "$(which kubectl)" ]; then
    echo -e "\nInstalling/Upgrading krew plugins for kubectl...\n"
    echo -e " -------------------------------------------------- "
    echo -e "| Krew Plugin  | Description                       |"
    echo -e "|--------------|-----------------------------------|"
    echo -e "| ctx          | context switching                 |"
    echo -e "| ns           | changing namespaces of context    |"
    echo -e "| example      | outputting example yaml           |"
    echo -e "| deprecations | check which things are deprecated |"
    echo -e " -------------------------------------------------- \n"

    kubectl krew install < deps/kubectl_krew_plugins
    kubectl krew upgrade
else
    echo -e "\nkubectl not installed. Please install kubectl and rerun the script."
fi

if [ -n "$KUBECONFIG" ]; then
    echo "export KUBECONFIG=~/.kube/kubeconfig" > ~/.bashrc
    echo "export KUBECONFIG=~/.kube/kubeconfig" > ~/.bash_profile
fi

# fin
echo -e "\nSetup completed."
