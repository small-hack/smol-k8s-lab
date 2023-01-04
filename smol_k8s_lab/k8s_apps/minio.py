#!/usr/bin/env python3.11
"""
       Name: minio
DESCRIPTION: install minio, a local S3 compatible object store
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from os import path
from yaml import dump
from ..k8s_tools.homelabHelm import helm
from ..bw_cli import BwCLI
from ..console_logging import header, sub_header, print_msg
from ..env_config import XDG_CACHE_DIR


def install_minio(password_manager=False):
    """
    does a helm install of minio
    """
    header("Installing 🦩 MinIO...")

    bw = BwCLI()
    # this is to generate a secure password
    minio_password = bw.generate()

    CIDR = "0.0.0.0/0"
    # for set options in helm
    val = {'rootUser': 'minio_admin',
           'rootPassword': minio_password,
           'resources': {'requests': {'memory': '1Gi'}},
           'replicas': 1,
           'mode': 'standalone',
           'service': {
               'type': 'LoadBalancer'
               },
           'consoleService': {
               'type': 'LoadBalancer'
               },
           'ingress': {
               'enabled': 'true',
               'ingressClassName': "nginx",
               'hosts': ["minio.vleermuis.tech"],
               'annotations': {
                   "kubernetes.io/ingress.allow-http": 'true',
                   "nginx.ingress.kubernetes.io/whitelist-source-range": CIDR,
                   }
               },
           'consoleIngress': {
               'enabled': 'true',
               'ingressClassName': "nginx",
               'hosts': ["console.minio.vleermuis.tech"],
               'annotations': {
                   "kubernetes.io/ingress.allow-http": 'true',
                   "nginx.ingress.kubernetes.io/whitelist-source-range": CIDR,
                   }
               }
           }

    # if we're using a password manager, generate a password & save it
    if password_manager:
        sub_header(":lock: Creating a new password in BitWarden.")
        # if we're using bitwarden...
        bw.unlock()
        bw.create_login(name='smol-k8s-lab minio',
                        item_url='https://localhost/minio',
                        user="minio_admin",
                        password=minio_password)
        bw.lock()
    else:
        sub_header("Here are MinIO root credentials. [i]Please store them!")
        print_msg(f"rootUser: minio_admin\nrootPassword: {minio_password}")

    # this creates a values.yaml from from the val dict above
    values_file_name = path.join(XDG_CACHE_DIR, 'minio_values.yaml')
    with open(values_file_name, 'w') as values_file:
        dump(val, values_file)

    release = helm.chart(release_name='minio',
                         chart_name='minio/minio',
                         namespace='minio',
                         values_file=values_file_name)
    release.install()
    return True
