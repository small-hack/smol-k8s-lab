from rich.prompt import Prompt
from ..utils.bw_cli import BwCLI
from ..k8s_tools.kubernetes_util import create_secret


def setup_bweso_secret(bitwarden=BwCLI()):
    """
    Creates an initial secret for use with the bitwarden provider for ESO
    """
    bw_client_id = bitwarden.clientID
    bw_client_secret = bitwarden.clientSecret
    bw_host = bitwarden.host
    bw_pass = bitwarden.pw

    # this is a standard k8s secrets yaml
    create_secret('bweso-login', 'external-secrets',
                  {"BW_PASSWORD": bw_pass,
                   "BW_CLIENTSECRET": bw_client_secret,
                   "BW_CLIENTID": bw_client_id,
                   "BW_HOST": bw_host})
    return True
