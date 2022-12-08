#!/usr/bin/env python3.11
"""
       Name: nginx_ingress_controller
DESCRIPTION: install the nginx ingress controller
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from ..k8s_tools.homelabHelm import helm
from ..k8s_tools.kubernetes_util import apply_manifests


def configure_ingress_nginx(k8s_distro="k3s"):
    """
    install nginx ingress controller from manifests for kind and helm for k3s
    # OLD: you need these to access webpages from outside the cluster
    # nginx_chart_opts = {'hostNetwork': 'true','hostPort.enabled': 'true'}
    # set_options=nginx_chart_opts)
    """
    url = ('https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/'
           'deploy/static/provider/kind/deploy.yaml')

    if k8s_distro == 'kind':
        # this is to wait for the deployment to come up
        apply_manifests(url, "ingress-nginx", "ingress-nginx-controller",
                        "app.kubernetes.io/component=controller")
    else:
        release = helm.chart(release_name='ingress-nginx',
                             chart_name='ingress-nginx/ingress-nginx',
                             chart_version='4.4.0',
                             namespace='ingress-nginx')
        release.install()
    return
