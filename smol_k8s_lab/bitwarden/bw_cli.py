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
from shutil import which
from sys import exit
from os import environ as env
from ..utils.run.subproc import subproc
from .tui.bitwarden_existing_item_app import AskUserForDuplicateStrategy


def create_custom_field(custom_field_name: str, value: str) -> dict:
   """
   creates a custom field dict for a bitwarden login item
   """
   custom_field = {"name": custom_field_name,
                   "value": value,
                   "type": 1,
                   "linkedId": None}

   return custom_field


class BwCLI():
    """
    Python Wrapper for the Bitwarden cli
    """
    def __init__(self, password: str, client_id: str, client_secret: str,
                 duplicate_strategy: str = "ask"):
        """
        for storing the session token, credentials, and duplicate_strategy

        duplicate_strategy: str, must be one of: edit, ask, duplicate, no_action
        """
        self.bw_path = str(which("bw"))
        log.debug(f"self.bw_path is {self.bw_path}")

        if not self.bw_path:
            log.error("whoops, looks like bw isn't installed. "
                      "Try [green]brew install bw")
            exit()

        # if we clean up the session when we're done or not
        self.delete_session = True

        # this is used for bweso and logins
        self.host = env.get("BW_HOST", "https://bitwarden.com")
        log.debug(f"Using {self.host} as $BW_HOST")


        # make sure there's not a session token in the env vars already
        self.env = {"BW_SESSION": env.get("BW_SESSION", ""),
                    "PATH": env.get("PATH"),
                    "HOME": env.get("HOME"),
                    "NODE_OPTIONS": "--no-deprecation"}

        self.password = password
        self.client_id = client_id
        self.client_secret = client_secret
        self.duplicate_strategy = duplicate_strategy

    def sync(self) -> None:
        """
        syncs your bitwaren vault on initialize of this class
        """
        res = subproc([f"{self.bw_path} sync"], env=self.env)
        log.info(res)

    def __get_credential__(self, credential: str) -> str:
        """
        prompts a user for a specific credential
        """
        cred_prompt = f"[cyan]🤫 Enter your Bitwarden vault {credential}"
        return Prompt.ask(cred_prompt, password=True)

    def status(self) -> str:
        """
        generate a new password. Takes special_characters bool.
        """
        log.info('Checking if you are logged in...')
        return json.loads(subproc(["bw status"], env=self.env))['status']

    def unlock(self) -> None:
        """
        unlocks the local bitwarden vault, and returns session token
        """
        if self.env['BW_SESSION']:
            log.info('Using session token from $BW_SESSION env variable')
            self.delete_session = False

        status = self.status()
        if status == "locked" or status == "unauthenticated":
            env = {"BW_PASSWORD": self.password,
                   "BW_CLIENTID": self.client_id,
                   "BW_CLIENTSECRET": self.client_secret,
                   "BW_HOST": self.host,
                   "PATH": self.env['PATH'],
                   "HOME": self.env['HOME'],
                   "NODE_OPTIONS": "--no-deprecation"}

        # login if we need to
        if status == "unauthenticated":
            log.info('Logging into the Bitwarden vault...')
            # set command to login if we're unauthenticated
            cmd = f"{self.bw_path} login --passwordenv BW_PASSWORD --apikey --raw"
            subproc([cmd], quiet=True, env=env)

        # we still need to unlock, even if we logged in already
        if status == "locked" or status == "unauthenticated":
            log.info('Unlocking the Bitwarden vault...')
            # set command to unlock if status is locked
            cmd = f"{self.bw_path} unlock --passwordenv BW_PASSWORD --raw"

            # run either bw login or bw unlock depending on bw status
            self.env['BW_SESSION'] = subproc([cmd], quiet=True, env=env)
            log.debug(f"bw unlock session is {self.env['BW_SESSION']}")
            log.info('Unlocked the Bitwarden vault.')
        else:
            log.info(f"[green]bw status[/] returned '{status}', so we won't "
                     "unlock the Bitwarden vault before starting.")

    def lock(self) -> None:
        """
        lock bitwarden vault, only if the user didn't have a session env var,
        so that we don't clean up a session the user didn't intend for
        """
        if self.delete_session:
            log.info('Locking the Bitwarden vault...')
            subproc([f"{self.bw_path} lock"], env=self.env)
            log.info('Bitwarden vault locked.')
        else:
            log.debug("We didn't lock the Bitwarden vault when we were done, "
                      "because we didn't set the BW_SESSION env var, so we don't"
                      " want to be rude.")

    def generate(self, special_characters: bool = False) -> str:
        """
        generate a new password. Takes special_characters bool.
        """
        log.debug('Generating a new password...')

        command = "bw generate --length 32 --uppercase --lowercase --number"
        if special_characters:
            command += " --special"

        password = subproc([command], quiet=True)
        log.debug('New password generated.')
        return password

    def get_item(self, item_name: str, sync_first: bool = True) -> list:
        """
        Get Item and return False if it does not exist else return the item ID

        Required Args:
            - item_name: str of name of item
        """
        # always sync vault before checking anything, unless otherwise stated
        if sync_first:
            self.sync()

        # go get the actual item
        response = json.loads(
                subproc([f'{self.bw_path} get item {item_name} --response'],
                        error_ok=True,
                        quiet=True,
                        env=self.env
                        )
                )

        message = response.get("message", "")

        # if there is no item, just return False
        if message == "Not found.":
            log.debug(response)
            return False, None

        elif 'More than one result was found' in message:
            item_list = response['data']
            log.debug(f"found more than 1 entry for {item_name}: {item_list}")

            # make a list of each full item
            list_for_dialog = []
            for id in item_list:
                list_for_dialog.append(self.get_item(id)[0])

            # ask the user what to do
            user_response = AskUserForDuplicateStrategy(list_for_dialog,
                                                        item_name).run()

            action = user_response[0]
            always_do_action = user_response[1]
            item = user_response[2]

            # if they always want to do this, then set self.duplicate_strategy
            if always_do_action:
                # NOTE: we still always ask if there's more than 1 entry returned
                self.duplicate_strategy = action

            return item, action
        else:
            return response['data'], self.duplicate_strategy

    def create_login(self,
                     name: str = "",
                     item_url: str = "",
                     user: str = "",
                     password: str = "",
                     fields: list = [],
                     org: str = None,
                     collection: str = None,
                     strategy: str = None) -> str:
        """
        Create login item to store a set of credentials for one site.
        Required Args:
            - name:        str of the name of the item to create in the vault
        Optional Args:
            - user:        str of username to use for login item
            - password:    str of password you want to use for login item
            - item_url:    str of URL you want to use the credentials for
            - org:         str of organization to use for collection
            - collection:  str collection inside organization to user
            - fields:      list of {key: value} dicts for custom fields
            - strategy:    str that defaults to self.duplicate_strategy

        Returns string of the item id created or updated
        """
        # don't edit anything by default
        edit = False

        # fix naming for bitwarden items to inlude the url AND name
        if name:
            item_name = name
            if item_url:
                item_name += f"-{item_url}"
        else:
            item_name = item_url

        # go check for existing items
        item_res = self.get_item(item_name)
        item = item_res[0]

        if not strategy:
            strategy = item_res[1]

        if item:
            if strategy == "ask":
                user_response = AskUserForDuplicateStrategy(item,
                                                            item_name).run()
                strategy = user_response[0]

                # if the user set "always do this action"
                if user_response[1] is True:
                   # NOTE: we still always ask if there's more than 1 entry returned
                   self.duplicate_strategy = strategy

            if strategy == 'edit':
                log.info("bitwarden.duplicate_strategy set to edit, so we will "
                         f"edit the existing item: {name}")
                edit = True

            elif strategy == 'duplicate':
                msg = (f"😵 Item named {name} already exists in your Bitwarden"
                       " vault and bitwarden.duplicate_strategy is set to duplicate."
                       " We will create the item anyway, but the Bitwarden ESO "
                       "Provider may have trouble finding it :(")
                log.warn(msg)

            elif strategy == "no_action":
                log.info(
                    "We've encounted an existing entry for the item we were going "
                    " to create. duplicate_strategy is set to 'no_action', so we "
                    "will not replace or edit it nor will we create a new item."
                    f"item: {item}"
                    )
                return

        # create new item
        if not edit:
            if item:
                log.info(f'Not editing Bitwarden item "{item_name}", because we '
                         'were instructed to create a duplicate.')
            else:
                log.info(f'Creating Bitwarden login item "{item_name}"')

            login_obj = json.dumps({
                "organizationId": org,
                "collectionIds": collection,
                "folderId": None,
                "type": 1,
                "name": item_name,
                "notes": None,
                "favorite": False,
                "fields": fields,
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

            cmd = f"{self.bw_path} create item {encodedStr}"

        # edit existing item
        else:
            log.info(f'Updating existing Bitwarden login item "{item_name}"...')
            item['login']['password'] = password
            item['login']['username'] = user
            item['fields'] = fields

            encodedBytes = base64.b64encode(json.dumps(item).encode("utf-8"))
            encodedStr = str(encodedBytes, "utf-8")

            cmd = f"{self.bw_path} edit item {item['id']} {encodedStr}"


        # edit OR create the item
        bitwarden_return_item = subproc([cmd + " --response"], quiet=True, env=self.env)
        log.debug(bitwarden_return_item)

        if edit:
            return item['id']
        else:
            return json.loads(bitwarden_return_item)['data']['id']
