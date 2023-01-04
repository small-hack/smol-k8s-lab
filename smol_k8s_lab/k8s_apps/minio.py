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


def create_values_file(minio_fqdn="", minio_console_fqdn="",
                       minio_password=""):
    """
    creates a values.yaml for the MinIO helm chart.
    Sets specifications loosely based on MinIO's "toy" install guide:
      rootPassword -  str parameter to this function
      replicas     -  1            # w/o this, the default is 10 replicas
      mode         -  standalone   # w/o this, we require more nodes
    This is done for both service and consoleService:
      service.type -  LoadBalancer # w/o this, uses clusterIP
      ingress.enabled          - True
      ingress.ingressClassName - nginx
      ingress.hosts - list of your str parameter fqdn
      ingress.annotations - kubernetes.io/ingress.allow-http: True
                          - nginx.ingress.kubernetes.io/whitelist-source-range
    Args:
      - minio_fqdn - fully qualified domain name to use for your minio endpoint
      - minio_console_fqdn -  fully qualified domain name for yr minio console
      - minio_password - root password for your minio installation

    Returns the full path to file as a str
    """
    cidr = "0.0.0.0/0"
    val = {'replicas': 1,
           'mode': 'standalone',
           'rootUser': 'minio_admin',
           'rootPassword': minio_password,
           'resources': {'requests': {'memory': '1Gi'}},
           'service': {
               'type': 'LoadBalancer'
               },
           'ingress': {
               'enabled': 'true',
               'ingressClassName': "nginx",
               'hosts': [minio_fqdn],
               'annotations': {
                   "kubernetes.io/ingress.allow-http": 'true',
                   "nginx.ingress.kubernetes.io/whitelist-source-range": cidr,
                   }
               },
           'consoleService': {
               'type': 'LoadBalancer'
               },
           'consoleIngress': {
               'enabled': 'true',
               'ingressClassName': "nginx",
               'hosts': [minio_console_fqdn],
               'annotations': {
                   "kubernetes.io/ingress.allow-http": 'true',
                   "nginx.ingress.kubernetes.io/whitelist-source-range": cidr,
                   }
               }
           }

    # this creates a values.yaml from from the val dict above
    values_file_name = path.join(XDG_CACHE_DIR, 'minio_values.yaml')
    with open(values_file_name, 'w') as values_file:
        dump(val, values_file)

    return values_file_name


def install_minio(minio_fqdn="", minio_console_fqdn="",
                  password_manager=False):
    """
    Creates a password for minio, places it in bitwarden, and then
    Does a helm install of minio
    Returns True
    """
    header("Installing 🦩 MinIO...")

    bw = BwCLI()
    # this is to generate a secure password
    minio_password = bw.generate()

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

    # this dumps a yaml file from a python dict
    values = create_values_file(minio_fqdn, minio_console_fqdn, minio_password)
    release = helm.chart(release_name='minio',
                         chart_name='minio/minio',
                         namespace='minio',
                         values_file=values)
    # actual helm install
    release.install()
    return True
