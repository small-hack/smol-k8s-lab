#!/usr/bin/env python3.11
"""
       Name:
DESCRIPTION:
     AUTHOR:
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from ..env_config import load_yaml, XDG_STATE_HOME

cluster = {"name": "",
           "k8s_distro": "",
           "creation_time": ""}


def get_smol_k8s_clusters():
    """
    get clusters we've created
    """
    load_yaml()
    return
