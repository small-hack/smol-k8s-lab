import logging as log
from os import environ
from smol_k8s_lab.bitwarden.bw_cli import BwCLI


def extract_secret(value) -> str:
    """
    process a value that has a valueFrom dict and return the value

    supported valueFrom methods: env, bitwarden. coming soon: openbao
    """
    # get variable from env var
    env_var = value['valueFrom'].get('env', None)
    if env_var:
        return environ.get(env_var, "")

    # get variable from bitwarden item and field
    bitwarden_item = value['valueFrom'].get('bitwarden_item', None)
    if bitwarden_item:
        bitwarden_field = value['valueFrom'].get('bitwarden_field', None)
        bw = BwCLI()
        return bw.get_item(bitwarden_item)[0][bitwarden_field]

    # get variable from openbao (vault) item
    openbao_item = value['valueFrom'].get('openbao_item', None)
    if openbao_item:
        log.warn("openbao support not yet implemented")
        return ""
