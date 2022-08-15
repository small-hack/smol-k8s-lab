#!/usr/bin/env python3
# Author: @jessebot jessebot@linux.com
# import psutil
import getpass
import subprocess
import requests
from util import header, sub_proc
"""
ref: https://bitwarden.com/help/vault-management-api/
Wrapped for Bitwarden cli, bw, to give a little help for testing in python
bw item template looks like:

{"organizationId":null, "collectionIds":null, "folderId":null, "type":1,
 "name":"Item name",
 "notes":"Some notes about this item.",
 "favorite":false,
 "fields":[],
 "login":null,
 "secureNote":null,
 "card":null,
 "identity":null,
 "reprompt":0}

Note: Item of type "Login" is .type=1
"""


def pure_cli_test():
    """
    testing cli functionality
    """
    header("Authenticating against bitwarden. Please have your "
           "API key ready.")
    print("Follow this guide to get your api key: \n"
          "https://bitwarden.com/help/personal-api-key/")

    sub_proc("bw login --apikey")


class BwRest():
    """
    testing bitwarden rest api
    """
    def __init__(self):
        """
        this is to initialize the bw api temporarily if it's not already there
        Examples: bw serve
                  bw serve --port 8080
                  bw serve --hostname bwapi.mydomain.com --port 80
        Use hostname `all` for no hostname binding?
        TODO: check for existing bw rest api running locally
        """
        self.bw_process = subprocess.Popen(["bw", "serve"])
        print(f"bw serve process ID is: {self.bw_process.pid}")

        # Default port for bw serve is 8087
        self.url = "http://localhost:8087"

        self.bw_main_pass = getpass.getpass(prompt='Password: ', stream=None)

    def kill(self):
        """
        kills the running bitwarden rest api process
        """
        print("Killing the bitwarden rest api, since we're done with it.")
        self.bw_process.kill()

    def generate(self):
        """
        generate a new password
        """
        header("Generating a new password...")
        new_pass = requests.get(f"{self.url}/generate").json()
        if new_pass["success"]:
            print(new_pass['data']['data'])
        return new_pass['data']['data']

    def unlock(self):
        """
        unlocks the local bitwarden vault
        """
        header("Unlocking the Bitwarden vault...")
        data_obj = {"password": self.bw_main_pass}
        json_resp = requests.post(f"{self.url}/unlock", json=data_obj).json()

        if json_resp["success"]:
            header(json_resp['data']["title"], False)
            print(json_resp['data']["message"])
            print(json_resp['data'])

    def lock(self):
        """
        lock the local bitwarden vault
        """
        header("Locking the Bitwarden vault...")
        data_obj = {"password": self.bw_main_pass}
        json_resp = requests.post(f"{self.url}/lock", json=data_obj).json()
        if json_resp["success"]:
            header(json_resp['data']["title"], False)
            msg = json_resp['data']["message"]
            if msg:
                print(msg)

    class loginItem():
        def __init__(self, login_item_name):
            self.login_item_name = login_item_name
            self.item_url = f"{self.url}/object/item/{self.login_item_name}"

        def get_login_item(self):
            """
            get an existing bitwarden login item
            """
            header("Getting bitwarden login item...")
            data_obj = {}
            json_resp = requests.get(self.item_url, json=data_obj).json()
            print(json_resp)

        def edit_login_item(self):
            """
            Edit an existing login, card, secure note, or identity
            in your Vault by specifying a unique object identifier
            (e.g. 3a84be8d-12e7-4223-98cd-ae0000eabdec) in the path and
            the new object contents in the request body.
            """
            header("Editing bitwarden login item...")
            data_obj = {}
            json_resp = requests.put(self.item_url, json=data_obj).json()
            print(json_resp)

        def post_login_item(self):
            """
            create a new bitwarden login item
            """
            header("Creating bitwarden login item...")
            data_obj = {}
            json_resp = requests.post(self.item_url, json=data_obj).json()
            print(json_resp)


def existing_bw_rest_api():
    """
    check for existing bw rest apis running
    """
    # TODO : use psutil to ensure we don't have another rest api running
    return


def main():
    """
    main function to run through a test of every function
    """
    bw_instance = BwRest()
    bw_instance.generate()
    bw_instance.unlock()
    bw_instance.lock()
    bw_instance.kill()


if __name__ == '__main__':
    main()
