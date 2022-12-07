#!/usr/bin/env python3
# extremely simple bitwarden cli wrapper
# Author: @jessebot jessebot@linux.com
"""
Example:
        bw = BwCLI()
        bw.unlock()
        bw.generate()
        bw.create_login(name="test mctest",
                        item_url="coolhosting4dogs.tech",
                        user="admin",
                        password="fakepassword")
        bw.lock()
"""
import base64
import json
import logging as log
from rich.prompt import Prompt
from .subproc import subproc


class BwCLI():
    """
    Python Wrapper for the Bitwarden cli
    """
    def __init__(self,):
        """
        This is mostly for storing the session
        """
        self.session = None

    def generate(self, special_characters=False):
        """
        generate a new password. Takes special_characters bool.
        """
        log.info('Generating a new password...')

        command = "bw generate --length 24 --uppercase --lowercase --number"
        if special_characters:
            command += " --special"

        password = subproc([command], quiet=True)
        log.info('New password generated.')
        return password

    def unlock(self):
        """
        unlocks the local bitwarden vault, and returns session token
        TODO: check local env vars for password or api key
        """
        log.info('Unlocking the Bitwarden vault...')

        password = Prompt.ask("[cyan]🤫 Enter your Bitwarden vault password",
                              password=True)

        self.session = subproc([f"bw unlock {password} --raw"], quiet=True,
                               spinner=False)
        log.info('Unlocked the Bitwarden vault.')

    def lock(self):
        """
        lock the local bitwarden vault
        """
        log.info('Locking the Bitwarden vault...')
        subproc([f"bw lock --session {self.session}"], quiet=True)
        log.info('Bitwarden vault locked.')
        return

    def create_login(self, name="", item_url="", user="", password="",
                     org=None, collection=None):
        """
        Create login item to store a set of credentials for one site.
        Required Args:
            - name - str of the name of the item to create in the vault
            - item_url - str of URL you want to use the credentials for
            - user - str of username to use for login item
            - password - str of password you want to use for login item
        Optional Args:
            - organization - str
            - collection - str
        """
        log.info('Creating bitwarden login item...')
        login_obj = json.dumps({
            "organizationId": org,
            "collectionIds": collection,
            "folderId": None,
            "type": 1,
            "name": item_url,
            "notes": None,
            "favorite": False,
            "fields": [],
            "login": {"uris": [{"match": 0,
                                "uri": item_url}],
                      "username": user,
                      "password": password,
                      "totp": None},
            "secureNote": None,
            "card": None,
            "identity": None,
            "reprompt": 0})

        encodedBytes = base64.b64encode(login_obj.encode("utf-8"))
        encodedStr = str(encodedBytes, "utf-8")

        subproc([f"bw create item {encodedStr} --session {self.session}"],
                quiet=True)
        log.info('Created bitwarden login item.')
