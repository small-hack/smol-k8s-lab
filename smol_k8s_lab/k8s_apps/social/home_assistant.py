# function for creating the initial home assistant user

# internal libraries
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_tools.argocd_util import (install_with_argocd,
                                                check_if_argocd_app_exists,
                                                update_argocd_appset_secret)
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.utils.rich_cli.console_logging import sub_header, header
from smol_k8s_lab.utils.passwords import create_password

# external libraries
import logging as log


def configure_home_assistant(k8s_obj: K8s,
                             config_dict: dict,
                             api_tls_verify: bool = False,
                             bitwarden: BwCLI = None) -> None:
    """
    creates a home-assistant app and initializes it with secrets if you'd like :)

    required:
        k8s_obj     - K8s() object with cluster credentials
        config_dict - dictionary with at least argocd key and init key

    optional:
        bitwarden   - BwCLI() object with session token to create bitwarden items
    """
    # check immediately if this app is installed
    app_installed = check_if_argocd_app_exists('home-assistant')

    # get any secret keys passed in
    secrets = config_dict['argo']['secret_keys']
    if secrets:
        home_assistant_hostname = secrets['hostname']

    # verify if initialization is enabled
    init_enabled = config_dict['init']['enabled']

    # if the user has chosen to use smol-k8s-lab initialization
    if not app_installed and init_enabled:
        k8s_obj.create_namespace(config_dict['argo']['namespace'])
        header("Setting up [green]home-assistant[/], to self host your home automation",
               '🏡')

        # grab all possile init values
        init_values = config_dict['init'].get('values', None)
        if init_values:
            admin_name = init_values.get('name', 'admin')
            admin_user = init_values.get('user_name', 'admin')
            admin_password = init_values.get('password', create_password())
            admin_language = init_values.get('language', 'en')

        # if bitwarden is enabled, we create login items for each set of credentials
        if bitwarden:
            sub_header("Creating home-assistant items in Bitwarden")
            # determine if using https or http for home assistant api calls
            if api_tls_verify:
                external_url = 'https://' + home_assistant_hostname + '/'
            else:
                external_url = 'http://' + home_assistant_hostname + '/'
            external_url_field = create_custom_field('externalurl', external_url)

            # admin credentials for initial owner user
            admin_name_field = create_custom_field('name', admin_name)
            admin_lang_field = create_custom_field('language', admin_language)
            admin_password = bitwarden.generate()
            admin_id = bitwarden.create_login(
                    name=f'home-assistant-admin-credentials-{home_assistant_hostname}',
                    item_url=home_assistant_hostname,
                    user=admin_user,
                    password=admin_password,
                    fields=[admin_name_field, admin_lang_field, external_url_field]
                    )

            # update the home-assistant values for the argocd appset
            update_argocd_appset_secret(
                    k8s_obj,
                    {'home_assistant_admin_credentials_bitwarden_id': admin_id}
                    )

        # these are standard k8s secrets
        else:
            # home-assistant admin credentials and smtp credentials
            k8s_obj.create_secret('home-assistant-credentials', 'home-assistant',
                                  {"ADMIN_USERNAME": admin_user,
                                   "ADMIN_NAME": admin_name,
                                   "ADMIN_PASSWORD": admin_password,
                                   "ADMIN_LANGUAGE": admin_language,
                                   "EXTERNAL_URL": home_assistant_hostname
                                   })

    if not app_installed:
        install_with_argocd(k8s_obj, 'home-assistant', config_dict['argo'])
    else:
        log.info("home-assistant already installed 🎉")

        # if bitwarden and init are enabled, make sure we populate appset secret
        # plugin secret with bitwarden item IDs
        if bitwarden and init_enabled:
            log.debug("Making sure home-assistant Bitwarden item IDs are in appset "
                      "secret plugin secret")

            admin_id = bitwarden.get_item(
                    f"home-assistant-admin-credentials-{home_assistant_hostname}"
                    )[0]['id']

            update_argocd_appset_secret(
                    k8s_obj,
                    {'home_assistant_admin_credentials_bitwarden_id': admin_id}
                    )
