#!/usr/bin/env python3
# Author: @jessebot jessebot@linux.com
# import psutil
from getpass import getpass
import subprocess
from requests import post, get, put
from util import header
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


class BwRest():
    """
    Python Wrapper for the Bitwarden REST API
    """
    def __init__(self, domain="localhost", port=8087, https=False,
                 serve_local_api=True):
        """
        If serve_local_api=True, serve the bw api temporarily if it's not
        already there. Defaults to running on http://localhost:8087

        Accepts domain str, port int, https bool, and serve_local_api bool

        example cli run: bw serve --hostname bwapi.mydomain.com --port 80
        """
        # Cleanup=False means we don't have to kill any processes after this
        self.cleanup = False

        if serve_local_api:
            # Cleanup means we'll be killing this process when we're done
            self.cleanup = True
            api_cmd = "bw serve"
            if domain != 'localhost':
                api_cmd += " --hostname {domain} "
            if port != 8087:
                api_cmd += " --port {port}"
            self.bw_process = subprocess.Popen(api_cmd.split())

        self.url = f"http://{domain}:{port}"
        if https:
            self.url = f"https://{domain}:{port}"

    def __terminate(self):
        """
        kills the running bitwarden rest api process. if this doesn't run,
        the bitwarden rest api will remain.
        """
        # only kill the process if we created it ourselves
        if self.bw_process:
            print("Killing the bitwarden rest api, since we're done with it.")
            self.bw_process.kill()
        return

    def generate(self):
        """
        generate a new password
        if we get an error, return that whole json blob response
        """
        header('Generating a new password...')
        data_obj = {'length': 18, 'uppercase': True, 'lowercase': True,
                    'number': True}
        res = get(f"{self.url}/generate", json=data_obj).json()

        if res['success']:
            print(res['data']['data'])
            return res['data']['data']

        # in case we get an error
        return res

    def unlock(self):
        """
        unlocks the local bitwarden vault, and returns session token
        if we get an error, return that whole json blob response
        TODO: check local env vars for password or api key
        """
        print("We'll need you to enter your password for bitwarden to unlock"
              "your vault temporarily to add the new password")
        password_prompt = 'Enter your Bitwarden Password: '
        password = getpass(prompt=password_prompt, stream=None)

        header('Unlocking the Bitwarden vault...')
        data_obj = {'password': password}
        res = post(f'{self.url}/unlock', json=data_obj).json()

        if res['success']:
            header(res['data']['title'], False)
            self.data_obj = {'session': res['data']['raw']}

        return res

    def lock(self):
        """
        lock the local bitwarden vault
        """
        header('Locking the Bitwarden vault...')

        res = post(f"{self.url}/lock", json=self.data_obj).json()

        if res['success']:
            header(res['data']['title'], False)
            msg = res['data']['message']
            if msg:
                print(msg)
            self.__terminate()
        else:
            return res

    class loginItem():
        def __init__(self, login_item_name, login_item_url, username, password,
                     organization=None, collection=None):
            """
            Get, modify, and create login items, and only login items
            takes optional organization and collection
            """
            self.item_name = login_item_name
            self.req_url = f"{self.url}/object/item/"
            self.login_data_obj = {"organizationId": organization,
                                   "collectionId": collection,
                                   "folderId": None,
                                   "type": 1,
                                   "name": login_item_url,
                                   "notes": None,
                                   "favorite": False,
                                   "fields": [],
                                   "login": {"uris": [{"match": 0,
                                                       "uri": login_item_url}],
                                             "username": username,
                                             "password": password,
                                             "totp": None},
                                   "reprompt": 0}

        def get_login_item(self):
            """
            get an existing bitwarden login item
            """
            header('Checking if bitwarden login item exists...')
            json_resp = get(self.req_url, json=self.data_obj).json()
            print(json_resp)

        def post_login_item(self):
            """
            create a new bitwarden login item
            """
            header('Creating bitwarden login item...')
            data_obj = {}
            data_obj.update(self.data_obj)
            data_obj.update(self.login_data_obj)

            json_resp = post(self.item_url, json=data_obj).json()
            print(json_resp)

        def edit_login_item(self):
            """
            Edit an existing login, card, secure note, or identity
            in your Vault by specifying a unique object identifier
            (e.g. 3a84be8d-12e7-4223-98cd-ae0000eabdec) in the path and
            the new object contents in the request body.
            """
            header('Editing bitwarden login item...')
            data_obj = {}
            json_resp = put(self.item_url, json=data_obj).json()
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
    bw_instance.unlock()
    bw_instance.generate()
    login_item = bw_instance.loginItem("test mctest",
                                       "nextcloud.vleermuis.tech",
                                       "admin", "fakepassword")
    login_item.post_login_item()
    bw_instance.lock()


if __name__ == '__main__':
    main()
