#!/usr/bin/env python3.11
"""
       Name: minio
DESCRIPTION: install minio, a local S3 compatible object store
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from ..k8s_tools.homelabHelm import helm
from ..bw_cli import BwCLI
from ..console_logging import header, sub_header, print_msg


def install_minio(password_manager=False):
    """
    does a helm install of minio
    """
    header("Installing 🦩 MinIO...")

    bw = BwCLI()
    # this is to generate a secure password
    minio_password = bw.generate()

    # for set options in helm
    val = {'rootUser': 'minio_admin', 'rootPassword': minio_password}

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

    release = helm.chart(release_name='minio',
                         chart_name='minio/minio',
                         namespace='minio',
                         set_options=val)
    release.install()
    return True
