#!/usr/bin/env python3.11
"""
       Name: nginx_ingress_controller
DESCRIPTION: install the nginx ingress controller
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
# external libraries
from os import path
import yaml

# internal libraries
from smol_k8s_lab.k8s_tools.helm import Helm
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.constants import XDG_CACHE_DIR


def configure_ingress_nginx(k8s_obj: K8s, k8s_distro: str) -> None:
    """
    install nginx ingress controller from manifests for kind and helm for k3s
    """
    url = ('https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/'
           'deploy/static/provider/kind/deploy.yaml')

    if k8s_distro == 'kind':
        # this is to wait for the deployment to come up
        k8s_obj.apply_manifests(
                manifest_file_name=url,
                namespace="ingress-nginx",
                deployment="ingress-nginx-controller",
                selector="app.kubernetes.io/component=controller"
                )
    else:
        values = {
                "controller": {
                    "configAnnotations": {
                        "allow-snippet-annotations": "true",
                        "forwarded-for-header": "X-Forwarded-For",
                        "proxy-real-ip-cidr": "0.0.0.0/0",
                        "real-ip-header": "X-Real-IP",
                        "use-forwarded-headers": "true"
                    },
                    "allowSnippetAnnotations": True,
                    "resources": {
                        "requests": {
                            "cpu": "100m",
                            "memory": "90Mi"
                            }
                    },
                    "service": {
                        "enabled": True,
                        "external": {"enabled": True},
                        "type": "LoadBalancer",
                        "externalTrafficPolicy": "Local"
                    }
                }
        }
        values_file_name = path.join(XDG_CACHE_DIR, 'ingres_nginx_values.yaml')
        with open(values_file_name, 'w') as values_file:
            yaml.dump(values, values_file)

        release = Helm.chart(release_name='ingress-nginx',
                             chart_name='ingress-nginx/ingress-nginx',
                             namespace='ingress-nginx',
                             values_file=values_file_name)
        release.install(wait=True)
