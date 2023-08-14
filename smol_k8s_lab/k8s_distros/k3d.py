#!/usr/bin/env python3.11
"""
       Name: k3d
DESCRIPTION: install k3d :D
     AUTHOR: @Jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
import logging as log
from ..pretty_printing.console_logging import sub_header
from ..subproc import subproc


def install_k3d_cluster() -> bool:
    """
    https://k3d.io/v5.5.2/#install-script
    python installation for k3d
    returns true if it worked
    """
    cmd = "kubectl config get-clusters"
    clusters = subproc([cmd])
    if 'smol-k8s-lab-k3d' in clusters:
        log.info("k3d cluster detected in $KUBECONFIG. Checking if it's up.")
        cmd = "kubectl get pods"
        try:
            subproc([cmd])
        except Exception as e:
            log.info(e)
            log.info("Looks like the current k3d cluster is not operational.")
        else:
            # exit this function because k3s is already installed
            return

    sub_header("Creating k3d cluster...")
    subproc(['k3d create cluster smol-k8s-lab-k3d'])
    return True
