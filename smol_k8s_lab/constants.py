#!/usr/bin/env python3.11
"""
NAME: constants.py
DESC: everything to do with initial configuration of a new environment
"""

from importlib.metadata import version as get_version
from getpass import getuser
from os import environ, path, uname
from pathlib import Path

from sys import exit
import yaml
from .console_logging import print_panel
from xdg_base_dirs import xdg_cache_home, xdg_config_home

# env
SYSINFO = uname()
# this will be something like ('Darwin', 'x86_64')
OS = (SYSINFO.sysname, SYSINFO.machine)

HOME_DIR = environ["HOME"]
USER = getuser()

# pathing
PWD = path.dirname(__file__)

# for smol-k8s-lab configs and cache
XDG_CACHE_DIR = path.join(xdg_cache_home(), 'smol-k8s-lab')
XDG_CONFIG_DIR = path.join(xdg_config_home(), 'smol-k8s-lab/config.yaml')

# for specifically the kubeconfig file
XDG_KUBE_FILE = path.join(xdg_config_home(), 'kube/config')
# default to ~/.config/kube/config if no KUBECONFIG or XDG_CONFIG set
KUBECONFIG = environ.get("KUBECONFIG", XDG_KUBE_FILE)
KUBE_DIR = path.dirname(KUBECONFIG)
# create the directory if it doesn't exist
Path(KUBE_DIR).mkdir(exist_ok=True)

# version of smol-k8s-lab
VERSION = get_version('smol-k8s-lab')


def load_yaml(yaml_config_file=XDG_CONFIG_DIR):
    """
    load config yaml files for smol-k8s-lab and return as dicts
    """
    if path.exists(yaml_config_file):
        with open(yaml_config_file, 'r') as yaml_file:
            return yaml.safe_load(yaml_file)
    else:
        print_panel(f"😱 Config file does not exist: {yaml_config_file}\n\n"
              "Please check the documentatation here:\nhttps://small-hack."
              "github.io/smol-k8s-lab/quickstart#configuration")
        exit()


# defaults
USR_CONFIG_FILE = load_yaml()
