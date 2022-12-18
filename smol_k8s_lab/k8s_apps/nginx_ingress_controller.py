#!/usr/bin/env python3.11
"""
       Name: nginx_ingress_controller
DESCRIPTION: install the nginx ingress controller
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from ..k8s_tools.homelabHelm import helm
from ..k8s_tools.kubernetes_util import apply_manifests
import os
from ..subproc import subproc


def configure_ingress_nginx(k8s_distro="k3s", prometheus="true"):
    """
    install nginx ingress controller from manifests for kind and helm for k3s
    # OLD: you need these to access webpages from outside the cluster
    # nginx_chart_opts = {'hostNetwork': 'true','hostPort.enabled': 'true'}
    # set_options=nginx_chart_opts)
    """
    if k8s_distro == 'kind':
        # TODO: Pin this version? 🤷
        url = ('https://raw.githubusercontent.com/kubernetes/ingress-nginx'
               '/main/deploy/static/provider/kind/deploy.yaml')

        # this is to wait for the deployment to come up
        apply_manifests(url, "ingress-nginx", "ingress-nginx-controller",
                        "app.kubernetes.io/component=controller")
    else:
        nginx_chart_opts = {"prometheus.create": prometheus,
                            "prometheus.port": 9901}
        release = helm.chart(release_name='ingress-nginx',
                             chart_name='ingress-nginx/ingress-nginx',
                             chart_version='4.4.0',
                             namespace='ingress-nginx',
                             set_options=nginx_chart_opts)
        release.install()

    # deploy the metrics service
    full_path = os.path.realpath(__file__)
    path, filename = os.path.split(full_path)
    kubeapply = f'kubectl apply -f {path}/nginx-metrics-service.yaml'
    subproc([kubeapply], spinner=True)
    return
