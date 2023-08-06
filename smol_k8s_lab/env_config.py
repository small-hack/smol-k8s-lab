#!/usr/bin/env python3.11
"""
NAME: env_config.py
DESC: everything to do with initial configuration of a new environment
"""

from rich.prompt import Confirm, Prompt
from .constants import OS, VERSION, XDG_CONFIG_FILE
from .console_logging import print_panel
from yaml import dump


def check_os_support(supported_os=('Linux', 'Darwin')):
    """
    verify we're on a supported OS and ask to quit if not.
    """
    if OS[0] not in supported_os:
        offical_supported_list = ", ".join(supported_os)
        msg = (f"[ohno]{OS[0]}[/ohno] isn't officially supported in {VERSION}."
               f" We have only tested the following: {offical_supported_list}")
        print_panel(msg, "⚠️  [warn]WARNING")

        quit_y = Confirm.ask("🌊 You're in uncharted waters. Wanna quit?")
        if quit_y:
            print_panel("That's probably safer. Have a safe day, friend.",
                        "Safety Award ☆ ")
            quit()
        else:
            print_panel("[red]Yeehaw, I guess.", "¯\\_(ツ)_/¯")
    else:
        print_panel("Operating System and Architechure [green]supported ♥",
                    "[cornflower_blue]Compatibility Check")


def process_configs(initial_config_file={}):
    """
    process the config in ~/.config/smol-k8s-lab/config.yaml and make sure all
    the correct values are filled in
    """
    passed_in_dict = initial_config_file

    # check to make sure we have recieved sensitive fields for cert-manager
    cert_dict = initial_config_file.get('cert-manager', "")
    if cert_dict:
        if cert_dict.get("enabled", True):
            if not cert_dict.get("email", ""):
                # prompt if we're missing a field
                email = Prompt.ask("Please enter an email for lets-encrypt: ")
                initial_config_file['cert-manager']['email'] = email

    # check to make sure we have recieved sensitive fields for metallb
    metal_dict = initial_config_file.get('metallb', "")
    if metal_dict:
        if metal_dict.get("enabled", True):
            if not metal_dict.get("address_pool", ""):
                # prompt if we're missing a field
                cidr = Prompt.ask("Please enter a CIDR for metallb: ")
                initial_config_file['metallb']['address_pool'] = [cidr]

    # check to make sure we have recieved sensitive fields for argo CD
    argocd_dict = initial_config_file.get('argo_cd', "")
    if argocd_dict:
        if argocd_dict.get("enabled", True):
            if not argocd_dict.get("domain", ""):
                # prompt if we're missing a field
                argo_domain = Prompt.ask("Please enter an FQDN for Argo CD: ")
                initial_config_file['argo_cd']['domain'] = argo_domain

    # check to make sure we have recieved sensitive fields for keycloak
    keycloak_dict = initial_config_file.get('keycloak', "")
    if keycloak_dict:
        if keycloak_dict.get("enabled", True):
            if not keycloak_dict.get("domain", ""):
                # prompt if we're missing a field
                key_domain = Prompt.ask("Please enter an FQDN for Keycloak: ")
                initial_config_file['keycloak']['domain'] = key_domain

    # Write newly aquired YAML data to config file
    if initial_config_file != passed_in_dict:
        print("Writing out your newly generated config file :)")
        with open(XDG_CONFIG_FILE, 'w') as conf_file:
            dump(initial_config_file, conf_file)

    return initial_config_file
