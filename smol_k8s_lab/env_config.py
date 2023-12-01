#!/usr/bin/env python3.11
"""
NAME: env_config.py
DESC: everything to do with initial configuration of a new environment via the cli
"""
# internal libraries and variables
from .constants import (OS,
                        VERSION,
                        DEFAULT_CONFIG,
                        DEFAULT_APPS,
                        DEFAULT_DISTRO_OPTIONS,
                        DEFAULT_DISTRO,
                        INITIAL_USR_CONFIG,
                        XDG_CONFIG_FILE)
from .utils.rich_cli.console_logging import print_panel, header, sub_header

# external libraries and variables
from os import environ
from rich.prompt import Confirm, Prompt
from ruamel.yaml import YAML


def check_os_support(supported_os=('Linux', 'Darwin')):
    """
    verify we're on a supported OS and ask to quit if not.
    """
    if OS[0] not in supported_os:
        offical_supported_list = ", ".join(supported_os)
        msg = (f"[ohno]{OS[0]}[/ohno] isn't officially supported in {VERSION}."
               f" We have only tested the following: {offical_supported_list}")
        print_panel(msg, "⚠️  [warn]WARNING")

        quit_y = Confirm.ask("🌊 You're in uncharted waters. Do you want to quit?")
        if quit_y:
            print_panel("That's probably safer. Have a safe day, friend.",
                        "Safety Award ☆ ")
            quit()
        else:
            print_panel("[red]Yeehaw, I guess.", "¯\\_(ツ)_/¯")
    else:
        # don't print anything if the OS is supported
        return True


def process_configs(config: dict = INITIAL_USR_CONFIG):
    """
    process the config in ~/.config/smol-k8s-lab/config.yaml and ensure each
    app has a secret if we're using our default Argo CD repo
    """
    k8s_distros = config.get('k8s_distros', None)
    config['k8s_distros'] = process_k8s_distros(k8s_distros)[0]

    initialize = False
    # process just the app sections because they're the bulk of the config
    config_apps = config.get('apps', None)

    header("Checking Application Configuration...")
    # if the config doesn't have the apps section, then we initialize a new one
    # and return that to avoid extra computations on comparing the default conf
    if not config_apps or DEFAULT_APPS == config_apps:
        sub_header("No application configurations found. 🌱 We'll initialize "
                   "them for you")
        initialize = True
        apps_config, secrets = initialize_apps_config()
    else:
        sub_header("🔍 Found existing Application configurations to validate",
                   True, False)
        apps_config, secrets = process_app_configs(config['apps'])
    config['apps'] = apps_config

    # if no logging was configured, use the defaults
    if not config['smol_k8s_lab'].get('log', None):
        config['smol_k8s_lab']['log'] = DEFAULT_CONFIG["log"]

    # set global lets-encrypt clusterIssuer, timezone, and external secrets
    apps_global_cfg = config.get('apps_global_config',
                                 {'cluster_issuer': 'letsencrypt-staging',
                                  'external_secrets': 'true',
                                  'timezone': "Europe/Amsterdam"})
    for secret_key, value in apps_global_cfg.items():
        secrets[f'global_{secret_key}'] = value

    # Write newly updated YAML data to config file
    if initialize or DEFAULT_CONFIG != config:
        sub_header("✏️ Writing out your newly updated config file")
        yaml = YAML()

        with open(XDG_CONFIG_FILE, 'w') as smol_k8s_config:
            yaml.dump(config, smol_k8s_config)

    final_config = add_all_possible_env_vars(config)

    return final_config, secrets


def process_app_configs(apps: dict = {}) -> list:
    """
    process an existing applications config dict and fill in any missing fields
    arguments:
        - apps: applcations dict schema as described:
            {"my_app": {"enabled": true,
                        "init": true,
                        "argo": {"repo": "",
                                 "namespace": "",
                                 "secret_keys": {"hostname": ""},
                                 "source_repos": []}
                        }
             }
    """

    # check if argo cd is enabled and if argo_cd isn't an app in thier config,
    # we create it with defaults
    argocd_enabled = apps.get('argo_cd', DEFAULT_APPS['argo_cd'])['enabled']

    # this is always the same repo, we're not creative
    default_repo = DEFAULT_APPS['argo_cd']['argo']['repo']

    # these are the secrets we also return, so we can create them all at once
    return_secrets = {}

    for app_key, app in apps.items():
        # grab the default app config to compare to
        default_cfg = DEFAULT_APPS.get(app_key, {})
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
                if default_cfg:
                    apps[app_key]['argo'] = argo_section = default_cfg['argo']
                else:
                    raise Exception(
                            f"{app_key} is missing its argo section in your yaml. "
                            "Please add that before re-running smol-k8s-lab. Suggestion"
                            ": use the interactive config with: smol-k8s-lab -i")

            # verify they're using our default repo config for this app
            if argo_section['repo'] == default_repo:
                # use secret section if exists, else grab from the default cfg
                if default_cfg:
                    default_secrets = default_cfg['argo'].get('secret_keys', '')
                else:
                    default_secrets = None
                secrets = argo_section.get('secret_keys', '')

                # if secret keys are not present in existing config or default
                # config, continue the loop to the next app
                if not secrets and not default_secrets:
                    continue

                # if the secret keys don't exist in the existing config but do
                # exist in the default config, use the default config secrets
                if default_secrets and not secrets:
                    apps[app_key]['argo']['secret_keys'] = default_secrets
                    secrets = default_secrets

                # iterate through each secret for the app
                for secret_key, secret in sorted(secrets.items()):
                    # create app k8s secret key like argocd_hostname
                    k8s_secret_key = "_".join([app_key, secret_key])
                    # this is so we don't prompt for values we don't need for
                    # backup types we don't use
                    if secret and k8s_secret_key == 'nextcloud_backup_method':
                        backup_method = secret

                    # if the secret is empty, prompt for a new one
                    if not secret:
                        m = f"[green]Please enter a {secret_key} for {app_key}"

                        # this nextcloud block handles differnet backup types
                        if app_key == 'nextcloud':
                            if k8s_secret_key == 'nextcloud_backup_method':
                                opt = ['s3', 'local']
                                res, backup_method = Prompt.ask(m, choices=opt)
                            elif 'nextcloud_backup_s3' in k8s_secret_key:
                                if backup_method == 'local':
                                    res = '""'
                                else:
                                    res = Prompt.ask(m)
                            elif k8s_secret_key == 'nextcloud_backup_mount_path':
                                if backup_method == 's3':
                                    res = '""'
                                else:
                                    res = Prompt.ask(m)
                        else:
                            res = Prompt.ask(m)

                        return_secrets[secret_key] = res
                        apps[app_key]['argo']['secret_keys'][secret_key] = res
                        continue

                    # else just set the secret to the same thing it was
                    return_secrets[k8s_secret_key] = secret

    return apps, return_secrets


def initialize_apps_config() -> list:
    """
    Initializes a fresh apps configuration for smol-k8s-lab by ensuring each
    field is filled out.
    """
    config = DEFAULT_APPS
    # these are the secrets we also return, so we can create them all at once
    return_secrets = {}

    # key is equal to the name of the of application. app is the dict
    for key, app in config.items():

        # if the user config doesn't have this section we default to the above
        app_enabled = app.get('enabled', True)

        # if app is enabled
        if app_enabled:
            argo_section = app['argo']

            # use secret section if exists, else grab from the default cfg
            secrets = argo_section.get('secret_keys', None)

            if not secrets:
                # if there's no secrets for this app, continue the loop to next app
                continue

            # if secrets are set, but init is disabled, continue the loop to next app
            if app.get('init', None):
                if not app['init']['enabled']:
                    continue

            # iterate through each secret for the app
            for secret in secrets.keys():
                # create app k8s secret key like argocd_hostname
                secret_key = "_".join([key, secret])

                # if the secret is empty, prompt for a new one
                # might need to add this back
                # if not secrets[secret] or type(secrets[secret]) is not str:
                if not secrets[secret]:
                    msg = f"[green]Please enter a {secret} for {key}"
                    res = Prompt.ask(msg)
                    config[key]['argo']['secret_keys'][secret] = res
                    return_secrets[secret_key] = res
                else:
                    config[key]['argo']['secret_keys'][secret] = secrets[secret]
                    return_secrets[secret_key] = secrets[secret]

    return config, return_secrets


def process_k8s_distros(k8s_distros: dict = {}, prompt: bool = True):
    """
    make sure the k8s distro passed into the config is supported and valid for
    the current operating system

    If prompt is set to True, we'll ask the user to select a distro
    """
    # keep track if we even have any enabled
    distros_enabled = False

    if k8s_distros:
        # verify the distros are supported
        for distro, metadata in k8s_distros.items():
            # if distro is enabled, but is not supported on user's OS
            if distro not in DEFAULT_DISTRO_OPTIONS:
                if metadata.get('enabled', False):
                    print(f"{distro} is not supported on {OS[0]} at this time. :(")
                    # disable that distro so we don't run into errors down the line
                    k8s_distros[distro]['enabled'] = False
            else:
              # if distro is enabled
              if metadata.get('enabled', False):
                  distros_enabled = True
                  default = distro

    if not distros_enabled:
        if prompt:
            msg = "[green]Which K8s distro would you like to use for your cluster?"
            distro = Prompt.ask(msg, choices=DEFAULT_DISTRO_OPTIONS)
            k8s_distros[distro]['enabled'] = True
        else:
            k8s_distros[DEFAULT_DISTRO]["enabled"] = True
            default = DEFAULT_DISTRO

    return k8s_distros, default


def add_all_possible_env_vars(config: dict):
    """
    populate all possible env vars from the sensitive values for special apps,
    namely: nextcloud, mastodon, and matrix

    returns updated config dict
    """
    for app in ["nextcloud", "mastodon", "matrix"]:
        init_dict = config['apps'][app]['init']
        if init_dict['enabled']:
            sensitive_values = init_dict['sensitive_values']
            if sensitive_values:
                for value in sensitive_values:
                    env_var = environ.get("_".join([app.upper(), value.upper()]))
                    if env_var:
                        config['apps'][app]['init']['values'][value.lower()] = env_var

    return config
