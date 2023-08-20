import logging as log
import json
from requests import request
from rich.prompt import Prompt
from shutil import which
from ..subproc import subproc


class Zitadel():
    """
    Python Wrapper for the Zitadel API
    """
    def __init__(self, api_url: str = "", private_key: str = ""):
        """
        This is mostly for storing the session token and api base url
        """
        log.debug("Initializing zitadel API object")
        self.api_url = api_url
        log.debug(f"API URL is [blue]{api_url}[/]")
        api_token = generate_token(private_key)
        self.api_token = api_token
        # log.debug(f"private key is {private_key}")

        self.headers = {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Authorization': f'Bearer {self.api_token}'
        }

        self.project_id = self.get_project_id()
        log.debug(f"project id is {self.project_id}")

    def get_project_id(self,) -> str:
        """
        zitadel.com/docs/apis/resources/mgmt/management-service-list-projects
        """

        payload = json.dumps({
          "query": {
            "offset": "0",
            "limit": 100,
            "asc": True
          },
          "queries": [
            {
              "nameQuery": {
                "name": "ZITADEL",
                "method": "TEXT_QUERY_METHOD_EQUALS"
              }
            }
          ]
        })

        response = request("PUT", self.api_url + "projects/_search",
                           headers=self.headers, data=payload)

        log.info(response.text)
        return response.json['result'][0]['id']

    def create_user(self,) -> str:
        """
        Creates an initial user in zitadel.
        prompts a user for username, first name, last name, and email.

        Returns string of user_id.
        """
        user = Prompt("[green]Enter a new username for Zitadel")
        first_name = Prompt("[Green]Enter your First name for your profile")
        last_name = Prompt("[Green]Enter your Last name for your profile")
        email = Prompt("[Green]Enter your email for your profile")
        gender = Prompt("[Green]Please select a gender (more coming soon)",
                        choices=["GENDER_FEMALE", "GENDER_MALE", "OTHER"])

        # create a new user via the API
        log.info("Creating a new user...")
        payload = json.dumps({
          "userName": user,
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
          "password": "string",
          "passwordChangeRequired": True,
        })

        # get the user ID from the response
        response = request("POST", self.api_url + 'users/human/_import',
                           headers=self.headers, data=payload)
        log.info(response.text)
        return response.json['userId']


    def create_user_grant(self, user_id: str = "", role_key: str = ""):
        """
        Grants a role to a user.

        Arguments:
            user_id:    ID of the user we're grants a role to
            role_key:   key of the role to assign to the user
        """

        # make sure this user has access to the new application role we setup
        # zitadel.com/docs/apis/resources/mgmt/management-service-add-user-grant
        payload = json.dumps({
          "projectId": self.project_id,
          "roleKeys": [role_key]
        })

        response = request("POST",
                           self.api_url + f"users/{user_id}/grants",
                           headers=self.headers, data=payload)
        log.info(response.text)

        return response.json['userId']


    def create_application(self,
                           app_name: str = "",
                           redirect_uris: list = [],
                           post_logout_redirect_uris: list = []) -> dict:
        """
        Create an OIDC Application in Zitadel via the API.
        Arguments:
            app_name:                  name of the applcation to create
            redirect_uris:             list of redirect Uri strings
            post_logout_redirect_uris: list of redirect Uri strings

        Returns dict of application_id, client_id, client_secret
        """
        payload = json.dumps({
          "name": app_name,
          "redirectUris": redirect_uris,
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

        response = request("POST",
                           f'{self.api_url}projects/{self.proj_id}/apps/oidc',
                           headers=self.headers, data=payload)
        log.info(response.text)
        json_res = response.json

        return {"application_id": json_res['appId'],
                "client_id": json_res['clientId'],
                "client_secret": json_res['clientSecret']}


    def create_action(self, name: str = "") -> bool:
        """
        create an action for zitadel. Currently only creates one kind of action,
        a group mapper action. Returns True on success.
        """

        payload = json.dumps({
          "name": "groupsClaim",
          "script": "function groupsClaim(ctx, api) { if (ctx.v1.user.grants === undefined || ctx.v1.user.grants.count == 0) { return; } let grants = []; ctx.v1.user.grants.grants.forEach(claim => { claim.roles.forEach(role => { grants.push(role)  }) }) api.v1.claims.setClaim('groups', grants) }",
          "timeout": "10",
          "allowedToFail": True
        })

        response = request("POST", self.api_url + "actions",
                           headers=self.headers, data=payload)
        log.info(response.text)
        return True


    def create_role(self,
                    role_key: str = "",
                    display_name: str = "",
                    group: str = "") -> bool:
        """
        create a role in zitadel from given:
            role_key:     name of the role - no spaces allowed!
            display_name: human readable name of the role
            group:        group that this role applies to

        Returns True on success.
        """
        payload = json.dumps({
          "roleKey": role_key,
          "displayName": display_name,
          "group": group
        })

        response = request("POST",
                           f"{self.api_url}projects/{self.project_id}/roles",
                           headers=self.headers, data=payload)

        log.info(response.text)
        return True


    def update_project_settings(self, project_name: str = "") -> bool:
        """
        updates the settings of the role
        Returns True on success
        """
        payload = json.dumps({
          "name": project_name,
          "projectRoleAssertion": True,
          "projectRoleCheck": True,
          "hasProjectCheck": True,
          "privateLabelingSetting": "PRIVATE_LABELING_SETTING_UNSPECIFIED"
        })

        response = request("PUT",
                           self.api_url + f"projects/{self.project_id}",
                           headers=self.headers,
                           data=payload)

        log.info(response.text)
        return True


def create_token(private_key: str = "") -> str:
    """
    Takes a Zitadel service account private key and generates an API token.
    """
    if not which("zitadel-tools"):
        msg = ("Installing [green]zitadel-tools[/], a cli tool to generate an "
               "API token from a private key.")
        log.info(msg)
        cmd = "go install github.com/zitadel/zitadel-tools@latest"
        subproc([cmd])
