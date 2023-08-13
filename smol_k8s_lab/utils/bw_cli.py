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
from os import environ
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
        self.delete_session = True
        # make sure there's not a password in the environment already
        self.host = environ.get("BW_HOST", default="https://bitwarden.com")
        self.pw = environ.get("BW_PASSWORD")
        self.clientID = environ.get("BW_CLIENTID")
        self.clientSecret = environ.get("BW_CLIENTSECRET")

    def status(self):
        """
        generate a new password. Takes special_characters bool.
        """
        log.info('Checking if you are logged in...')
        vault_status = json.load(subproc(["bw status"], quiet=True))

        return vault_status

    def unlock(self):
        """
        unlocks the local bitwarden vault, and returns session token
        """
        self.session = environ.get("BW_SESSION", None)

        if self.session:
            log.info('Using session token from $BW_SESSION env variable')
            self.delete_session = False
        else:
            log.info('Unlocking the Bitwarden vault...')
            status = self.status()

            # if there's no env var called BW_PASSWORD, ask for one
            if not self.pw:
                pw_prompt = "[cyan]🤫 Enter your Bitwarden vault password"
                self.pw = Prompt.ask(pw_prompt, password=True)

            # default command is unlock
            cmd = "bw unlock --passwordenv BW_PASSWORD --raw"

            # verify we're even logged in :)
            if status == "unauthenticated" and not any([self.clientSecret,
                                                        self.clientID]):
                if not self.clientID:
                    msg = "[cyan]🤫 Enter your Bitwarden client ID"
                    self.clientID = Prompt.ask(msg, password=True)
                if not self.clientSecret:
                    msg = "[cyan]🤫 Enter your Bitwarden client Secret"
                    self.clientSecret = Prompt.ask(msg, password=True)

                # set command to login if we're unauthenticated
                cmd = "bw login --passwordenv BW_PASSWORD --apikey --raw"

            # run either bw login or bw unlock depending on bw status
            self.session = subproc([cmd], quiet=True, spinner=False,
                                   env={"BW_PASSWORD": self.pw,
                                        "BW_CLIENTID": self.clientID,
                                        "BW_CLIENTSECRET": self.clientSecret,
                                        "BW_HOST": self.host})
            log.info('Unlocked the Bitwarden vault.')

    def lock(self) -> None:
        """
        lock bitwarden vault, only if the user didn't have a session env var
        """
        if self.delete_session:
            log.info('Locking the Bitwarden vault...')
            subproc([f"bw lock --session {self.session}"], quiet=True)
            log.info('Bitwarden vault locked.')

    def generate(self, special_characters=False):
        """
        generate a new password. Takes special_characters bool.
        """
        log.info('Generating a new password...')

        command = "bw generate --length 32 --uppercase --lowercase --number"
        if special_characters:
            command += " --special"

        password = subproc([command], quiet=True)
        log.info('New password generated.')
        return password


    def create_login(self, name="", item_url=None, user="", password="", 
                     fields={}, org=None, collection=None):
        """
        Create login item to store a set of credentials for one site.
        Required Args:
            - name - str of the name of the item to create in the vault
            - user - str of username to use for login item
            - password - str of password you want to use for login item
        Optional Args:
            - item_url - str of URL you want to use the credentials for
            - org - str of organization to use for collection
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
            "fields": [fields],
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
