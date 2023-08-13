#!/usr/bin/env python3.11
"""
NAME: env_config.py
DESC: everything to do with initial configuration of a new environment
"""

from rich.prompt import Confirm, Prompt
from .constants import OS, VERSION, XDG_CONFIG_FILE
from .pretty_printing.console_logging import print_panel
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


def process_app_configs(default_config: dict, config: dict):
    """
    process the config in ~/.config/smol-k8s-lab/config.yaml and ensure each
    app has a secret if we're using our default Argo CD repo
    """
    # we get this once to avoid getting it like a million times in the loops
    argocd_enabled = config['apps']['argocd'].get('enabled', True)
    # this is always the same repo, we're not creative
    default_repo = default_config['apps']['argocd']['argo']['repo']
    # this is the final processed dict we return at the end
    final_cfg = default_config
    # these are the secrets we also return, so we can create them all at once
    return_secrets = {}

    for app_key, app in config['apps'].items():
        # grab the default app config to compare to
        default_cfg = default_config[app_key]
        # anything with an "enabled" field is default enabled
        default_enabled = default_cfg.get('enabled', True)
        # if the user config doesn't have this section we default to the above
        app_enabled = app.get('enabled', default_enabled)

        # if app is enabled and Argo CD is enabled
        if app_enabled and argocd_enabled:
            argo_section = app.get('argo', default_cfg['argo'])

            # verify they're using our default repo config for this app
            if argo_section['repo'] == default_repo:
                # use secret section if exists, else grab from the default cfg
                default_secrets = default_cfg['argo'].get('secret_keys', '')
                secrets = argo_section.get('secret_keys', default_secrets)

                if secrets:
                    # iterate through each secret for the app
                    for secret in default_secrets:
                        # create app k8s secret key like argocd_domain
                        secret_key = "_".join([app_key, secret])

                        # if the secret is empty, prompt for a new one
                        if not secrets[secret]:
                            ask_msg = f"Please enter a(n) {secret} for {app}: "
                            res = Prompt.ask(ask_msg)
                            final_cfg[app]['argo']['secret_keys'][secret] = res
                            return_secrets[secret_key] = res
                        else:
                            return_secrets[secret_key] = secrets[secret]

    # Write newly acquired YAML data to config file
    if config != final_cfg:
        print("Writing out your newly generated config file :)")
        with open(XDG_CONFIG_FILE, 'w') as conf_file:
            dump(final_cfg, conf_file)

    return final_cfg, return_secrets
