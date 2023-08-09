from rich.prompt import Prompt
from os import remove, path
from yaml import safe_dump
from base64 import standard_b64encode as b64enc
from ..constants import XDG_CACHE_DIR
from ..k8s_tools.kubernetes_util import apply_manifests
from ..console_logging import sub_header


def setup_bweso_secret():
    """
    Creates an initial secret for use with the bitwarden provider for ESO
    """
    note = ("The Bitwarden provider for the External Secrets Operator "
            "requires your credentials and API crdentials to use. You can"
            "get your API clientID and clientSecret using this guide:\n"
            "https://bitwarden.com/help/personal-api-key/")

    sub_header(note)

    ask = "Please enter your Bitwarden "
    bw_host = Prompt.ask(ask + "hostname:", default="https://bitwarden.com")
    bw_pass = Prompt(ask + "password:", password=True)
    bw_client_id = Prompt.ask(ask + "ClientID:", password=True)
    bw_client_secret = Prompt.ask(ask + "ClientSecret:", password=True)

    # this is a standard k8s secrets yaml
    secret_yaml = {'apiVersion': 'v1',
                   'kind': 'Secret',
                   'metadata': {
                       'name': 'appset-secret-vars',
                       'namespace': 'argocd'
                       },
                   'data': {
                       'secret_vars.yaml': {
                           "BW_PASSWORD": b64enc(bw_pass),
                           "BW_CLIENTSECRET": b64enc(bw_client_secret),
                           "BW_CLIENTID": b64enc(bw_client_id),
                           "BW_HOST": b64enc(bw_host)
                           }
                       }
                   }

    secrets_file_name = path.join(XDG_CACHE_DIR, 'bweso_secrets.yaml')

    # write out the file to be applied
    with open(secrets_file_name, 'w') as secret_file:
        safe_dump(secret_yaml, secret_file)

    apply_manifests(secrets_file_name)

    # clean up this file immediately, because it's got real passwords in it
    remove(secrets_file_name)
    return
