from os import environ as env

def check_env_for_credentials() -> list:
    """
    check if bitwarden credentials are in the environment already
    """
    password = env.get("BW_PASSWORD", None)
    client_id = env.get("BW_CLIENTID", None)
    client_secret = env.get("BW_CLIENTSECRET", None)

    return password, client_id, client_secret
