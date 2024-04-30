import logging as log
from os import environ
from smol_k8s_lab.bitwarden.bw_cli import BwCLI


def extract_secret(value: dict = {}) -> str:
    """
    process a value that has a valueFrom dict and return the value

    supported valueFrom methods: env, bitwarden. coming soon: openbao
    """
    if isinstance(value, dict):
        value_dict = value.get('valueFrom', None)
        if not value_dict:
            log.warn(f"{value} has no valueFrom dict, so we're returning empty str")
            return ""
    else:
        log.warn(f"value, {value}, is not a dict, so we're returning it as it came in")
        return value

    # try to get variable from env var
    env_var = value_dict.get('env', None)
    if env_var:
        return environ.get(env_var, "")

    # try to get variable from bitwarden item and field
    bitwarden_item = value_dict.get('bitwarden_item', None)
    if bitwarden_item:
        bitwarden_field = value['valueFrom'].get('bitwarden_field', None)
        bw = BwCLI()
        return bw.get_item(bitwarden_item)[0][bitwarden_field]

    # try to get variable from openbao (or vault) item
    openbao_item = value_dict.get('openbao_item', None)
    if openbao_item:
        log.warn("openbao support not yet implemented")

    log.warn("No secret was found so returning empty string")
    return ""
