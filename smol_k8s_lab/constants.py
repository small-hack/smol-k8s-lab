#!/usr/bin/env python3.11
"""
       Name:
DESCRIPTION:
     AUTHOR:
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from importlib.metadata import version as get_version
from getpass import getuser
from os import environ, path, uname
from pathlib import Path

from xdg import xdg_cache_home, xdg_config_home, xdg_data_home


# smol-k8s-lab cli info
VERSION = get_version('smol-k8s-lab')
PWD = path.dirname(__file__)

# machine info
SYSINFO = uname()
# this will be something like ('Darwin', 'x86_64')
OS = (SYSINFO.sysname, SYSINFO.machine)

# user info
HOME_DIR = environ["HOME"]
USER = getuser()

# for smol-k8s-lab config dir - created if it doesn't exist
xdg_config_dir = path.join(xdg_config_home(), 'smol-k8s-lab')
Path(xdg_config_dir).mkdir(exist_ok=True)
XDG_CONFIG_FILE = path.join(xdg_config_dir, '/config.yaml')

# KUBECONFIG dir and file - created if they don't exist
XDG_KUBE_FILE = path.join(xdg_config_home(), 'kube/config')
# default to ~/.config/kube/config if there's no KUBECONFIG or XDG_CONFIG set
KUBECONFIG = environ.get("KUBECONFIG", XDG_KUBE_FILE)
Path(path.dirname(KUBECONFIG)).mkdir(exist_ok=True)

# This is where we throw manifests and values files
XDG_CACHE_DIR = path.join(xdg_cache_home(), 'smol-k8s-lab')
Path(XDG_CACHE_DIR).mkdir(exist_ok=True)

# this is where we keep track of clusters we've launched
XDG_DATA_DIR = path.join(xdg_data_home(), 'smol-k8s-lab')
Path(XDG_DATA_DIR).mkdir(exist_ok=True)
