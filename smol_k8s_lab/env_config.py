#!/usr/bin/env python3.11
"""
NAME: env_config.py
DESC: everything to do with initial configuration of a new environment
"""

from rich.prompt import Confirm, Prompt
from .constants import OS, VERSION, XDG_CONFIG_FILE
from .pretty_printing.console_logging import print_panel, header, sub_header
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


def process_configs(default_config: dict, config: dict):
    """
    process the config in ~/.config/smol-k8s-lab/config.yaml and ensure each
    app has a secret if we're using our default Argo CD repo
    """
    initial_config = config

    # process just the app sections because they're the bulk of the config
    default_apps =  default_config['apps']
    config_apps = config.get('apps', None)

    # if the config doesn't have the apps section, then we initialize a new one
    # and return that to avoid extra computations on comparing the default conf
    if not config_apps or default_config == config:
        sub_header("No application confgiurations found 😮")
        apps_config, secrets = initialize_apps_config(default_config)
    else:
        sub_header("Found existing Application confgiurations 🩵 ")
        apps_config, secrets = process_app_configs(config_apps, default_apps)
    config['apps'] = apps_config

    config['log'] = config.get("log", default_config["log"])

    k8s_distros = config.get('k8s_distros', default_config['k8s_distros'])
    config['k8s_distros'] = process_k8s_distros(k8s_distros)

    # Write newly acquired YAML data to config file
    if initial_config != config:
        print("Writing out your newly updated config file :)")
        with open(XDG_CONFIG_FILE, 'w') as conf_file:
            dump(config, conf_file)

    return config, secrets


def process_app_configs(apps: dict = {}, default_apps: dict = {}):
    """
    process an existing applications config dict and fill in any missing fields
    """
    header("Validating Application Configs")
    # check if argo cd is enabled
    argocd_enabled = apps.get('argo_cd', 'missing')
    # if argo_cd isn't an app in thier config, we create it with defaults
    if argocd_enabled == 'missing':
        argocd_enabled = apps['argo_cd'] = default_apps['argo_cd']

    # this is always the same repo, we're not creative
    default_repo = default_apps['argo_cd']['argo']['repo']

    # these are the secrets we also return, so we can create them all at once
    return_secrets = {}

    for app_key, app in apps.items():
        # grab the default app config to compare to
        default_cfg = default_apps[app_key]
        # anything with an "enabled" field is default enabled
        default_enabled = default_cfg.get('enabled', True)
        # if the user config doesn't have this section we write in defaults
        app_enabled = app.get('enabled', 'missing')
        if app_enabled == 'missing':
            app_enabled = apps[app_key]['enabled'] = default_enabled

        # if app is enabled and Argo CD is enabled
        if app_enabled and argocd_enabled:
            # write in defaults if they're missing this section
            argo_section = app.get('argo', 'missing')
            if argo_section == 'missing':
                apps[app_key]['argo'] = argo_section = default_cfg['argo']

            # verify they're using our default repo config for this app
            if argo_section['repo'] == default_repo:
                # use secret section if exists, else grab from the default cfg
                default_secrets = default_cfg['argo'].get('secret_keys', '')
                secrets = argo_section.get('secret_keys', 'missing')
                if secrets == 'missing':
                    if default_secrets:
                        apps[app_key]['argo']['secret_keys'] = default_secrets
                        secrets = default_secrets
                    # if not secrets or default_secrets, continue apps loop
                    else:
                        continue

                # iterate through each secret for the app
                for secret_key, secret in default_secrets.items():
                    # create app k8s secret key like argocd_hostname
                    k8s_secret_key = "_".join([app_key, secret])

                    # if the secret is empty, prompt for a new one
                    if not secret:
                        m = f"[green]Please enter a {secret_key} for {app_key}"
                        res = Prompt.ask(m)
                        return_secrets[secret_key] = res
                        apps[app_key]['argo']['secrets'][secret_key] = res
                        continue

                    # else just set the secret to the same thing it was
                    return_secrets[k8s_secret_key] = secrets[secret]

    return apps, return_secrets


def initialize_apps_config(config: dict = {}):
    """
    Initializes a fresh apps configuration for smol-k8s-lab by ensuring each
    field is filled out.
    """
    header("Initializing a fresh config file for you!")
    # these are the secrets we also return, so we can create them all at once
    return_secrets = {}

    # key is equal to the name of the of application. app is the dict
    for key, app in config['apps'].items():
        # if the user config doesn't have this section we default to the above
        app_enabled = app.get('enabled', True)

        # if app is enabled
        if app_enabled:
            argo_section = app['argo']

            # use secret section if exists, else grab from the default cfg
            secrets = argo_section.get('secret_keys', None)

            if not secrets:
                # if there's no secrets for this app, continue the loop
                continue

            # iterate through each secret for the app
            for secret in secrets.keys():
                # create app k8s secret key like argocd_hostname
                secret_key = "_".join([key, secret])

                # if the secret is empty, prompt for a new one
                if not secrets[secret]:
                    msg = f"[green]Please enter a {secret} for {key}"
                    res = Prompt.ask(msg)
                    config['apps'][key]['argo']['secret_keys'][secret] = res
                    return_secrets[secret_key] = res
                else:
                    return_secrets[secret_key] = secrets[secret]

    return config, return_secrets


def process_k8s_distros(k8s_distros: list = ['kind']):
    """
    make sure the k8s distro passed into the config is supported and valid for
    the current operating system
    """
    default_distros = ['kind', 'k3s', 'k0s']

    if OS[0] == 'Darwin' and 'k3s' in k8s_distros:
        print("k3s does not run on macOS at this time :(")
        k8s_distros.pop("k3s")

    # verify the distros are supported
    for distro in k8s_distros:
        if distro not in default_distros:
            print(f"{distro} is not supported at this time. :(")
            k8s_distros.pop(distro)

    if not k8s_distros:
        print("Hate to see you leave empty handed. We'll setup kind :)")
        k8s_distros = ["kind"]

    return k8s_distros
