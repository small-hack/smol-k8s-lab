# internal libraries
from smol_k8s_lab.bitwarden.bw_cli import BwCLI, create_custom_field
from smol_k8s_lab.k8s_tools.argocd_util import ArgoCD
from smol_k8s_lab.utils.passwords import create_password
from smol_k8s_lab.utils.rich_cli.console_logging import sub_header, header

# external libraries
import logging as log


def configure_libretranslate(argocd: ArgoCD,
                             cfg: dict,
                             bitwarden: BwCLI = None) -> str:
    """
    creates a libretranslate app and initializes it with secrets if you'd like :)

    required:
        argocd      - ArgoCD() object for argo operations
        cfg - dictionary with at least argocd key and init key

    optional:
        bitwarden   - BwCLI() object with session token to create bitwarden items

    Returns api key for libretranslate for programatic access
    """
    # check immediately if this app is installed
    app_installed = argocd.check_if_app_exists('libretranslate')

    # get any secret keys passed in
    secrets = cfg['argo']['secret_keys']
    if secrets:
        libretranslate_hostname = secrets['hostname']

    # verify if initialization is enabled
    init_enabled = cfg['init']['enabled']

    # process restore dict
    restore_dict = cfg['init'].get('restore', {"enabled": False})
    restore_enabled = restore_dict['enabled']
    if restore_enabled:
        header_start = "Restoring"
    else:
        if app_installed:
            header_start = "Syncing"
        else:
            header_start = "Setting up"

    header(f"{header_start} [green]libretranslate[/], for selfhosting your own languages translation",
           '📖')

    # we need namespace no matter the install type
    libre_translate_namespace = cfg['argo']['namespace']

    # api key for programatic access to libretranslate: set it to blank just in case
    api_key = ""

    # if the user has chosen to use smol-k8s-lab initialization
    if not app_installed and init_enabled:
        # immediately create namespace
        argocd.k8s.create_namespace(libre_translate_namespace)

        # if bitwarden is enabled, we create login items for each set of credentials
        if bitwarden and not restore_enabled:
            api_key = setup_bitwarden_items(argocd,
                                            libretranslate_hostname,
                                            bitwarden)
        # these are standard k8s secrets
        else:
            # libretranslate admin credentials and smtp credentials
            argocd.k8s.create_secret('libretranslate-credentials',
                                     'libretranslate',
                                     {"api_key": create_password(),
                                      "api_origin": libretranslate_hostname,
                                      })

    if not app_installed:
        # then install the app as normal
        argocd.install_app('libretranslate', cfg['argo'])
    else:
        log.info("libretranslate already installed 🎉")

        # if bitwarden and init are enabled, make sure we populate appset secret
        # plugin secret with bitwarden item IDs
        if bitwarden and init_enabled:
            api_key = refresh_bitwarden(argocd, libretranslate_hostname, bitwarden)

    return api_key


def setup_bitwarden_items(argocd: ArgoCD,
                          libretranslate_hostname: str,
                          bitwarden: BwCLI) -> str:
    """
    setup initial bitwarden items for libretranslate

    returns the api key used for libretranslate so you can use it in other apps
    """
    sub_header("Creating libretranslate items in Bitwarden")
    api_key = bitwarden.generate()

    # admin credentials for initial owner user
    origin = create_custom_field('origin', libretranslate_hostname)
    api_id = bitwarden.create_login(
            name=f'libretranslate-credentials-{libretranslate_hostname}',
            item_url=libretranslate_hostname,
            user="n/a",
            password=api_key,
            fields=[origin]
            )

    # update the libretranslate values for the argocd appset
    argocd.update_appset_secret({'libretranslate_credentials_bitwarden_id': api_id})

    return api_key


def refresh_bitwarden(argocd: ArgoCD,
                      libretranslate_hostname: str,
                      bitwarden: BwCLI) -> str:
    """
    refresh bitwardens item in the appset secret plugin

    returns the api key used for libretranslate so you can use it in other apps
    """
    log.debug("Making sure libretranslate Bitwarden item IDs are in appset "
              "secret plugin secret")

    try:
        api_item = bitwarden.get_item(
                f"libretranslate-credentials-{libretranslate_hostname}"
                )[0]
        api_id = api_item['id']
    except TypeError:
        return setup_bitwarden_items(argocd,
                                     libretranslate_hostname,
                                     bitwarden)

    argocd.update_appset_secret({'libretranslate_credentials_bitwarden_id': api_id})
    api_key = api_item['login']['password']
    return api_key
