#!/usr/bin/env python3.11
"""
       Name: infisical
DESCRIPTION: configures infisical app and secrets operator
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version python3
             Infisical itself is licensed under Apache 2.0 and we at
             smol-k8s-lab do not claim any of their code
"""
import logging as log
from rich.prompt import Prompt
from ..pretty_printing.console_logging import header
from ..k8s_tools.argocd_util import install_with_argocd
from ..k8s_tools.k8s_lib import K8s


def configure_infisical(k8s_obj: K8s, infisical_dict: dict = {}):
    """
    configures the infisical app by asking for smtp credentials
    """
    header("Installing the Infisical app and Secrets operator...")

    if infisical_dict['init']:
        host = Prompt.ask("Please enter your SMTP host for Infisical")
        msg = "Please enter your SMTP from address for Infisical"
        from_address = Prompt.ask(msg)
        username = Prompt.ask("Please enter your SMTP username for Infisical")
        password = Prompt.ask("Please enter your SMTP password for Infisical",
                              password=True)

        secrets_dict = {"SMTP_HOST": host,
                        "SMTP_PORT": '587',
                        "SMTP_SECURE": 'true',
                        "SMTP_FROM_NAME": "Infisical",
                        "SMTP_FROM_ADDRESS": from_address,
                        "SMTP_USERNAME": username,
                        "SMTP_PASSWORD": password}

        k8s_obj.create_secret('infisical-credentials', 'infisical',
                              secrets_dict)

    install_with_argocd(k8s_obj, 'infisical', infisical_dict['argo'])
    return True
