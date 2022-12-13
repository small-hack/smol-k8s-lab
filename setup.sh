#!/bin/bash -
#=============================================================================
#         USAGE: ./setup.sh
#   DESCRIPTION: Setup the extra dependencies for the Smol K8s Lab
#  REQUIREMENTS: python3.11, brew
#        AUTHOR: @jessebot
#=============================================================================

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

# if kubectl installed then install plugins with krew plugin manager for kubectl
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

# make sure they've set a KUBECONFIG location 
if [ -n "$KUBECONFIG" ]; then
    if [[ "$(uname)" == *"Darwin"* ]]; then
        echo "export KUBECONFIG=~/.kube/kubeconfig" >> ~/.bash_profile
    else
        echo "export KUBECONFIG=~/.kube/kubeconfig" >> ~/.bashrc
    fi
fi

# fin
echo -e "\033[92m\nSetup completed. Don't forget to run:\n"
echo 'echo "export KUBECONFIG=~/.kube/kubeconfig" >> ~/.bashrc'
echo -e "\n(Replace .bashrc with .bash_profile if you are on a mac)"
