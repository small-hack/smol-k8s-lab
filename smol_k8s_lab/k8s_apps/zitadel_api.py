import logging as log
from json import dumps
# see for jwt docs: https://github.com/jpadilla/pyjwt/
import jwt
from requests import request
from rich.prompt import Prompt
# from shutil import which
# from ..subproc import subproc


class Zitadel():
    """
    Python Wrapper for the Zitadel API
    """
    def __init__(self, hostname: str = "", service_account_key_obj: dict = {}):
        """
        This is mostly for storing the session token and api base url
        """
        log.debug("Initializing zitadel API object")
        self.api_url = f"https://{hostname}/management/v1/"
        log.debug(f"API URL is [blue]{self.api_url}[/]")

        self.api_token = self.generate_token(hostname, service_account_key_obj)

        self.headers = {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Authorization': f'Bearer {self.api_token}'
        }

        log.debug(self.headers)

        self.project_id = self.get_project_id()
        log.debug(f"project id is {self.project_id}")


    def generate_token(self, hostname: str = "", secret_blob: str = "") -> str:
        """
        Takes a Zitadel hostname string and service account private key secret_blob
        and generates an API token.

        This does the equivelent of this this curl command to get the token:
            curl --request POST \
              --url https://{your_domain}.zitadel.cloud/oauth/v2/token \
              --header 'Content-Type: application/x-www-form-urlencoded' \
              --data grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer \
              --data scope='openid profile email' \
              --data assertion=eyJ0eXAiOiJKV1QiL...
        """
        encoded = jwt.encode(secret_blob, "secret", algorithm="HS256")
        auth_url = f"https://{hostname}.zitadel.cloud/oauth/v2/token"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
                   'scope': 'openid profile email',
                   'assertion': encoded}
        res = request("POST", auth_url, headers=headers, data=dumps(payload),
                      verify=False)
        log.info(res.text)
        return(res.json['access_token'])

    def get_project_id(self,) -> str:
        """
        zitadel.com/docs/apis/resources/mgmt/management-service-list-projects
        """

        payload = dumps({
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

        log.debug("Listing projects to get current project ID via the Zitadel API")
        response = request("PUT", self.api_url + "projects/_search",
                           headers=self.headers, data=payload, verify=False)

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
        payload = dumps({
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
        payload = dumps({
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
        payload = dumps({
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

        payload = dumps({
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
        payload = dumps({
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
        payload = dumps({
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
