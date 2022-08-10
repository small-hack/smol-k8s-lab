#!/bin/bash -
#===============================================================================
#
#         USAGE: ./quick-start.sh [k3s|k0s|KinD]
#
#   DESCRIPTION: Quickly install a k8s distro for a homelab setup. Takes required
#                argument of which distro and optional argument for --no-k9s to
#                NOT launch k9s at finish
#
#        AUTHOR: @jessebot + @cloudymax
#       CREATED: 08/10/22 19:45:55
#
#===============================================================================
. .env

# extremely simply loading bar
function simple_loading_bar() {
    p_echo "Sleeping for $1 second(s)."
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

if [ "$1" == "k3s" ]; then
    cd k3s
    ./quick-start-k3s.sh
    cd ..
elif [ "$2" == "kind" ]; then
    cd kind
    ./quick-start-kind.sh
    cd ..
elif [ "$2" == "k0s" ]; then
    p_echo "k0s still not operational, but you can check out the tutorial!"
else
    p_echo "Please pass in an argument of k3s, kind, or k0s"
fi
