import logging as log
import json
import requests
from rich.prompt import Prompt


class Zitadel():
    """
    Python Wrapper for the Zitadel API
    """
    def __init__(self, base_api_url: str = "", api_token: str = ""):
        """
        This is mostly for storing the session token and api base url
        """
        self.base_api_url = base_api_url
        self.api_token = api_token
        self.project_id = self.get_project_id()
        self.headers = {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Authorization': f'Bearer {self.api_token}'
        }

    def get_project_id(self,):
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

        response = requests.request("PUT",
                                    self.base_api_url + "projects/_search",
                                    headers=self.headers, data=payload)

        log.info(response.text) 

    def create_user(self, role_key: str = ""):
        """
        Creates an initial user in zitadel.
        Arguments:
            role_key:   str, key of the role to assign to the user

        prompts a user for username, first name, last name, and email.
        Returns True
        """
        username = Prompt("What would you like your Zitadel username to be?")
        first_name = Prompt("Enter your First name for your Zitadel profile")
        last_name = Prompt("Enter your Last name for your Zitadel profile")
        email = Prompt("Enter your email for your Zitadel profile")
        gender = Prompt("Please select a gender (more genders coming soon)",
                        choices=["GENDER_FEMALE", "GENDER_MALE", "OTHER"])

        # create a new user via the API
        log.info("Creating a new user...")
        payload = json.dumps({
          "userName": username,
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
        response = requests.request("POST", self.base_api_url + 'users/human/_import',
                                    headers=self.headers, data=payload)
        log.info(response.text)
        user_id = response.json['userId']

        # make sure this user has access to the new application role we setup
        # zitadel.com/docs/apis/resources/mgmt/management-service-add-user-grant
        payload = json.dumps({
          "projectId": self.project_id,
          "projectGrantId": "9847026806489455",
          "roleKeys": [role_key]
        })

        response = requests.request(
                "POST",
                self.base_api_url + f"users/{user_id}/grants",
                headers=self.headers, data=payload
                )
        log.info(response.text)


        return True


    def create_application(self, app_name: str = "", redirect_uris: list = [],
                           post_logout_redirect_uris: list = []):
        """
        Create an OIDC Application in Zitadel via the API.
        Arguments:
            api_url:      str, base URL of the API endpoint for zitadel
            app_name:     str, name of the applcation to create
            redirectUris: list, list of redirect Uri strings

        Returns clientSecret of application.
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

        response = requests.request(
                "POST",
                self.base_api_url + f'projects/{self.project_id}/apps/oidc',
                headers=self.headers,
                data=payload
                )
        log.info(response.text)

        return response.json['clientSecret']


    def create_action(self,):
        """ 
        create an action for zitadel. Currently only creates one kind of action,
        a group mapper action.
        """

        payload = json.dumps({
          "name": "groupsClaim",
          "script": "function groupsClaim(ctx, api) { if (ctx.v1.user.grants === undefined || ctx.v1.user.grants.count == 0) { return; } let grants = []; ctx.v1.user.grants.grants.forEach(claim => { claim.roles.forEach(role => { grants.push(role)  }) }) api.v1.claims.setClaim('groups', grants) }",
          "timeout": "10",
          "allowedToFail": True
        })

        response = requests.request("POST", self.base_api_url + "actions",
                                    headers=self.headers, data=payload)
        log.info(response.text)
        return True


    def create_role(self, role_key: str = "",
                            display_name: str = "", group: str = ""):
        """
        create a role in zitadel from given:
            role_key:     name of the role - no spaces allowed!
            display_name: human readable name of the role
            group:        group that this role applies to
        """
        payload = json.dumps({
          "roleKey": role_key,
          "displayName": display_name,
          "group": group
        })

        response = requests.request(
                "POST",
                f"{self.api_url}projects/{self.project_id}/roles",
                headers=self.headers,
                data=payload
                )

        log.info(response.text)
        return True


    def update_project_settings(self, project_name: str = ""):
        """ 
        updates the settings of the role
        """
        payload = json.dumps({
          "name": project_name,
          "projectRoleAssertion": True,
          "projectRoleCheck": True,
          "hasProjectCheck": True,
          "privateLabelingSetting": "PRIVATE_LABELING_SETTING_UNSPECIFIED"
        })

        response = requests.request(
                "PUT",
                self.base_api_url + f"projects/{self.project_id}",
                headers=self.headers,
                data=payload
                )

        log.info(response.text)
        return True


