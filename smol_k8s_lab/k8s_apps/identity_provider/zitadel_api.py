"""
Small Zitadel API wrapper using k8s service accounts
"""

# external libraries
import cryptography
from datetime import datetime, timezone, timedelta
import logging as log
from json import dumps
import jwt
from requests import request
from requests.exceptions import SSLError
from rich.prompt import Prompt
from time import sleep

# internal libraries
from smol_k8s_lab.bitwarden.bw_cli import BwCLI
from smol_k8s_lab.utils.passwords import create_password

class Zitadel():
    """
    Python Wrapper for the Zitadel API
    """
    def __init__(self,
                 hostname: str,
                 service_account_key_obj: dict = {},
                 tls_verify: bool = False,
                 project_id: str = ""):
        """
        This is mostly for storing the session token and api base url
        """
        log.debug("Initializing zitadel API object")
        self.hostname = hostname
        self.api_url = f"https://{hostname}/management/v1/"
        log.debug(f"API URL is [blue]{self.api_url}[/]")

        self.verify = tls_verify

        # verify the api is even up
        self.check_api_health()

        # then get the token
        self.api_token = self.generate_token(hostname, service_account_key_obj)

        self.headers = {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Authorization': f'Bearer {self.api_token}'
        }

        self.user_id = ""
        self.resource_owner = ""

    def check_api_health(self,) -> True:
        """
        Loops and checks https://{self.api_url}healthz for an HTTP status.
        Returns True when the status code is 200 (success).
        """
        res = None
        while True:
            log.debug("checking if api is up by querying the healthz endpoint"
                      f" by querying {self.api_url} using verify={self.verify}")

            try:
                res = request("GET", f"{self.api_url}healthz", verify=self.verify)
            except SSLError:
                log.warn(f"Looks like querying {self.api_url} gave an SSL error,"
                         "but we'll try again")
                pass

            if res:
                if res.status_code == 200:
                    log.info("Zitadel API is up now :)")
                    break
                else:
                    # sleep just a couple of seconds to avoid being locked out or something
                    sleep(2)
                    log.debug("Zitadel API is not yet up :(")
            else:
                sleep(2)

        return True

    def generate_token(self, hostname: str = "", secret_blob: dict = {}) -> str:
        """
        Takes a Zitadel hostname string and service account private key json,
        and generates first a JWT and then an API token.

        For python jwt docs: https://github.com/jpadilla/pyjwt/

        secret_blob dictionary should look like:
        {"type":"serviceaccount",
         "keyId":"100509901696068329",
         "key":"-----BEGIN RSA PRIVATE KEY-----...-----END RSA PRIVATE KEY-----\n",
         "userId":"100507859606888466"}

        https://zitadel.com/docs/guides/integrate/private-key-jwt
        #2-create-a-jwt-and-sign-with-private-key
        """
        # Generating a JWT from a private key
        log.info("Creating a jwt so we can request an Oauth token from zitadel")
        jwt_payload = {
                "iss": secret_blob['userId'],
                "sub": secret_blob['userId'],
                "aud": f"https://{hostname}",
                "iat": datetime.now(tz=timezone.utc),
                "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=30)
                }
        private_key = secret_blob['key']
        encoded = jwt.encode(jwt_payload, private_key, algorithm="RS256",
                             headers={"kid": secret_blob['keyId']})

        # actual creation of API token
        log.info("Requesting an API token from zitadel...")

        scopes = 'openid profile email urn:zitadel:iam:org:project:id:zitadel:aud'

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        payload = {'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
                   'scope': scopes,
                   'assertion': encoded}

        res = request("POST", f"https://{hostname}/oauth/v2/token",
                      headers=headers, data=payload, verify=self.verify)
        log.debug(f"res is {res}")

        # I literally don't know if you should use json or json()
        try:
            json_blob = res.json()
            log.debug(f"json_blob is {json_blob}")
            access_token = json_blob['access_token']
        except Exception as e:
            log.debug(f"there was an error: {e}")
            json_blob = res.json
            log.debug(f"json_blob is {json_blob}")
            access_token = json_blob['access_token']

        return(access_token)

    def create_project(self, project_name: str) -> None:
        """
        Creates a new project and returns the project id and resource owner
        """
        log.info("Creating a new project called [green]Core[/]")
        payload = dumps({
              "name": project_name,
              "projectRoleAssertion": True,
              "projectRoleCheck": True,
              "hasProjectCheck": True,
              "privateLabelingSetting": "PRIVATE_LABELING_SETTING_UNSPECIFIED"
            })

        response = request(
                "POST",
                self.api_url + "projects",
                headers=self.headers,
                data=payload,
                verify=self.verify
                )
        log.debug(response.text)

        json_blob = response.json()
        self.project_id = json_blob['id']
        self.resource_owner = json_blob['details']['resourceOwner']

    def create_user(self,
                    admin_user: str = "",
                    username: str = "",
                    first_name: str = "",
                    last_name: str = "",
                    email: str = "",
                    gender: str = "",
                    bitwarden: BwCLI = None) -> str:
        """
        Creates an initial user in zitadel.
        prompts a user for username, first name, last name, and email if Arguments
        are not passed in

        Returns string of user_id.
        """
        if admin_user:
            username = admin_user
        if not username:
            username = Prompt.ask("[green]Enter a new username for Zitadel")
        if not first_name:
            first_name = Prompt.ask("[green]Enter your First name for your profile")
        if not last_name:
            last_name = Prompt.ask("[green]Enter your Last name for your profile")
        if not email:
            email = Prompt.ask("[green]Enter your email for your profile")
        if not gender:
            gender = Prompt.ask("[green]Please select a gender (more coming soon)",
                                choices=["GENDER_FEMALE", "GENDER_MALE",
                                         "GENDER_DIVERSE", "GENDER_UNSPECIFIED"])

        # create a 32 character password with a randomly placed special character
        password = create_password(True)
        if bitwarden:
            bitwarden.create_login('zitadel_admin', self.api_url, username,
                                   password)

        # create a new user via the API
        log.info("Creating a new user...")
        payload = dumps({"userName": username,
                         "profile": {
                            "firstName": first_name,
                            "lastName": last_name,
                            "nickName": "friend",
                            "displayName": f"{first_name} {last_name}",
                            "preferredLanguage": "en",
                            "gender": gender
                          },
                          "email": {
                            "email": email,
                            "isEmailVerified": True
                          },
                          "password": password,
                          "passwordChangeRequired": True,
                        })
        log.info(f"payload for create user is {payload}")

        # get the user ID from the response
        response = request("POST", self.api_url + 'users/human/_import',
                           headers=self.headers, data=payload, verify=self.verify)
        log.info(response.text)
        return response.json()['userId']

    def create_user_grant(self, role_keys: list, user_id: str = "") -> str:
        """
        Grants a role to non-admin a user.

        Arguments:
            role_key:   key of the role to assign to the user
            user_id:    ID of the user we're grants a role to
        """
        if not user_id:
            user_id = self.user_id

        log.debug(f"Assiging user_id, {user_id} the role(s) of "
                  f"[green]{role_keys}[/] in {self.project_id}")

        # make sure this user has access to the new application role we setup
        # zitadel.com/docs/apis/resources/mgmt/management-service-add-user-grant
        payload = dumps({
          "projectId": self.project_id,
          "roleKeys": role_keys
        })

        response = request("POST",
                           self.api_url + f"users/{user_id}/grants",
                           headers=self.headers,
                           data=payload,
                           verify=self.verify)
        log.info(response.text)

        return response.json()['userGrantId']

    def update_user_grant(self, role_keys: list, user_id: str = "") -> str:
        """
        updates a user's existing grants.

        Arguments:
            role_key:   key of the role to assign to the user
            user_id:    ID of the user we're grants a role to, if not provided,
                        we use self.user_id
        """
        if not user_id:
            user_id = self.user_id

        url = f"{self.api_url}users/grants/_search"

        payload = dumps({
                  "userIdQuery": {
                    "userId": user_id
                  }
            })

        response = request("POST", url, headers=self.headers, data=payload,
                           verify=self.verify)
        log.info(response.text)
        user_roles = response.json()['result'][0]['roleKeys']
        grant_id = response.json()['result'][0]['id']
        log.info(f"{user_id} has grant id {grant_id} with roles: {user_roles}")

        # now we can update the user's roles
        role_keys.extend(user_roles)
        log.debug(f"Assiging user_id, {user_id} the roles of "
                  f"[green]{role_keys}[/] in {self.project_id}")

        url = f"{self.api_url}users/{user_id}/grants/{grant_id}"

        payload = dumps({"roleKeys": role_keys})

        response = request("PUT", url, headers=self.headers, data=payload,
                           verify=self.verify)

    def create_iam_membership(self, user_id: str, role: str):
        """
        iam membership assignment
        """
        url = f"https://{self.hostname}/admin/v1/members"
        payload = dumps({
          "userId": user_id,
          "roles": [role]
        })
        response = request("POST",
                           url,
                           headers=self.headers,
                           data=payload,
                           verify=self.verify)
        log.info(response.text)

    def create_application(self,
                           app_name: str = "",
                           redirect_uri: str = "",
                           post_logout_redirect_uris: list = []) -> dict:
        """
        Create an OIDC Application in Zitadel via the API.
        Arguments:
            app_name:                  name of the applcation to create
            redirect_uris:             list of redirect Uri strings
            post_logout_redirect_uris: list of redirect Uri strings

        Returns dict of application_id, client_id, client_secret
        """
        payload = dumps({
          "name": app_name,
          "redirectUris": [redirect_uri],
          "responseTypes": [
            "OIDC_RESPONSE_TYPE_CODE"
          ],
          "grantTypes": [
            "OIDC_GRANT_TYPE_AUTHORIZATION_CODE"
          ],
          "appType": "OIDC_APP_TYPE_WEB",
          "authMethodType": "OIDC_AUTH_METHOD_TYPE_BASIC",
          "postLogoutRedirectUris": post_logout_redirect_uris,
          "version": "OIDC_VERSION_1_0",
          "devMode": True,
          "accessTokenType": "OIDC_TOKEN_TYPE_BEARER",
          "accessTokenRoleAssertion": True,
          "idTokenRoleAssertion": True,
          "idTokenUserinfoAssertion": True,
          "clockSkew": "1s",
          "additionalOrigins": [
            "scheme://localhost:8080"
          ],
          "skipNativeAppSuccessPage": True
        })
        log.debug(payload)

        log.info(self.api_url)
        log.info(self.project_id)

        url = self.api_url + f'projects/{self.project_id}/apps/oidc'
        log.info(url)

        response = request("POST",
                           url,
                           headers=self.headers,
                           data=payload,
                           verify=self.verify)
        log.info(response.text)
        json_res = response.json()

        try:
            return {"application_id": json_res['appId'],
                    "client_id": json_res['clientId'],
                    "client_secret": json_res['clientSecret']}
        except KeyError:
            log.info(f"zitadel app, {app_name}, already exists")

    def create_groups_claim_action(self) -> None:
        """
        create an action for zitadel. Currently only creates one kind of action,
        a group mapper action.
        """
        payload = dumps({
          "name": "groupsClaim",
          "script": "function groupsClaim(ctx, api) {\n  if (ctx.v1.user.grants === undefined || ctx.v1.user.grants.count == 0) {\n    return;\n  }\n  let grants = [];\n  ctx.v1.user.grants.grants.forEach(claim => {\n    claim.roles.forEach(role => {\n      grants.push(role)\n    })\n  })\n  api.v1.claims.setClaim('groups', grants)\n}",
          "timeout": "10s",
          "allowedToFail": True
        })

        self.create_claim_action(payload)

    def create_is_admin_claim(self, claim_name: str, admin_role_key: str, user_role_key: str) -> None:
        """
        create an action that returns claim_name based on a if a user is has either
        an admin role key or a user role key in zitadel. We only send the claim
        name if the user is in one of those groups

        this is to return a claim name like: nextcloud_admin=True

        Example generated action script:

        function nextcloudAdminClaim(ctx, api) {
          if (ctx.v1.user.grants === undefined || ctx.v1.user.grants.count == 0) {
            return;
          }

          ctx.v1.user.grants.grants.forEach(claim => {
            if (claim.roles.includes('nextcloud_admins') {
                api.v1.claims.setClaim('nextcloud_admin', true)
                return;
                }

            if (claim.roles.includes('nextcloud_users') {
                api.v1.claims.setClaim('nextcloud_admin', false)
                return;
                }
            }
        }
        """
        no_underscore_claim = claim_name.replace("_", "")
        log.info(
            f"Creating Zitadel action, {no_underscore_claim}, to return in OIDC"
            f" responses {claim_name}=true if the user has the role "
            f"{admin_role_key}, and {claim_name}=false if the user has the role "
            f"{user_role_key}."
            )

        payload = dumps({
          "name": f"{no_underscore_claim}Claim",
          "script": "function " + no_underscore_claim + "Claim(ctx, api) {\n  if (ctx.v1.user.grants === undefined || ctx.v1.user.grants.count == 0) {\n    return;\n  }\n\n  ctx.v1.user.grants.grants.forEach(claim => {\n    if (claim.roles.includes('" + admin_role_key + "') {\n        api.v1.claims.setClaim('" + claim_name + "', true)\n        return;\n        }\n\n    if (claim.roles.includes('" + user_role_key + "') {\n        api.v1.claims.setClaim('" + claim_name + "', false)\n        return;\n        }\n    }\n}\n",
          "timeout": "10s",
          "allowedToFail": True
        })
        self.create_claim_action(payload)

    def create_claim_action(self, script: str = "") -> None:
        """
        create an action for zitadel to run before sending user info or
        giving access token
        """
        log.info("Creating action...")
        while True:
            response = request("POST",
                               self.api_url + "actions",
                               headers=self.headers,
                               data=script,
                               verify=self.verify)
            log.debug(response.text)
            # if the response is not 200, just try again 🤷
            if response.status_code == 200:
                break

        log.debug("Creating action flow triggers...")
        action_id = response.json()['id']
        action_payload = dumps({"actionIds": [action_id]})
        log.debug(action_payload)

        # At the moment you have to send the ID of the Trigger Type:
        # PreUserinfoCreation=4, PreAccessTokenCreation=5
        for trigger_type in ['4', '5']:
            url = f"{self.api_url}flows/2/trigger/{trigger_type}"
            log.debug(f"url is {url}")

            while True:
                response = request("POST",
                                   url,
                                   headers=self.headers,
                                   data=action_payload,
                                   verify=self.verify)
                log.debug(f"flows response is {response.text}")

                # if the response is not 200, just try again 🤷
                if response.status_code == 200:
                    break

    def create_role(self,
                    role_key: str = "",
                    display_name: str = "",
                    group: str = "") -> None:
        """
        create a role in zitadel from given:
            role_key:     name of the role - no spaces allowed!
            display_name: human readable name of the role
            group:        group that this role applies to
        """
        payload = dumps({
          "roleKey": role_key,
          "displayName": display_name,
          "group": group
        })
        url = f"{self.api_url}projects/{self.project_id}/roles"
        log.info(f"Creating a role, {role_key} using {url}")

        response = request("POST", url, headers=self.headers, data=payload,
                           verify=self.verify)

        log.info(response.text)

    def set_user_by_login_name(self, user: str) -> None:
        """
        get the user's ID by their login name
        """
        url = f"{self.api_url}global/users/_by_login_name?loginName={user}"

        response = request("GET", url, headers=self.headers, data={},
                           verify=self.verify).json()
        log.debug(response)

        self.user_id = response['user']['id']
        self.resource_owner = response['user']['details']['resourceOwner']

    def set_project_by_name(self, project_name: str) -> str:
        """
        project_name: str - name of the project to use for future app creation

        sets the current self.project_id after searching for the project by name
        """
        url = f"{self.api_url}projects/_search"

        payload = dumps({
          "query": {
            "offset": "0",
            "limit": 100,
            "asc": True
          },
          "queries": [
            {
              "nameQuery": {
                "name": project_name,
                "method": "TEXT_QUERY_METHOD_EQUALS"
              }
            }
          ]
        })
        log.debug("set_project_by_name _search payload ...")
        log.debug(payload)

        self.headers['Content-Type'] = 'application/json'

        response = request("POST", url, headers=self.headers, data=payload,
                           verify=self.verify)

        log.debug(f'response from set_project_by_name for "{project_name}" '
                  f'_search: {response.text}')

        self.project_id = response.json()['result'][0]['id']
        log.debug(f"zitadel api: set project id to {self.project_id}")
