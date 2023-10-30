from smol_k8s_lab.utils.subproc import subproc
from json import dumps
import logging as log


class Nextcloud():
    """
    nextcloud object for running common occ commands
    """

    def __init__(self, namespace: str = "nextcloud") -> None:
        """ 
        setup base occ commands to run
        """
        # namespace where nextcloud is installed
        self.namespace = namespace
        pod_cmd = (
                f"kubectl get pods -n {self.namespace} -l "
                "app.kubernetes.io/instance=nextcloud-web-app,"
                "app.kubernetes.io/component=app "
                "--no-headers "
                "-o custom-columns=NAME:.metadata.name")
        self.pod = subproc([pod_cmd])
        self.occ_cmd = (f'kubectl exec {self.pod} -- su -s /bin/sh www-data -c '
                        '"php occ')

    def install_apps(self, apps: list) -> None:
        """
        installs a list of apps via nextcloud occ commands
        """
        log.info(f"Attempting to install the following Nextcloud apps: {apps}")

        for app in apps:
            log.info(f"Attempting to install Nextcloud app: {app}")
            subproc([f'{self.occ_cmd} app:install {app}"'])

    def creat_oidc_groups(self) -> None:
        """
        create base nextcloud groups for use with oidc
        """
        log.info("Creating nextcloud groups: nextcloud_admins, nextcloud_users")
        subproc([f'{self.occ_cmd} group:add nextcloud_admins"',
                 f'{self.occ_cmd} group:add nextcloud_users"'])

    def configure_zitadel_social_login(self,
                                       zitadel_host: str,
                                       client_id: str,
                                       client_secret: str) -> None: 
        """ 
        configure the nextcloud social_login app to work with zitadel
        ref: https://zitadel.com/blog/zitadel-as-sso-provider-for-selfhosting
        """
        # make sure the appropriate groups already exist
        self.creat_oidc_groups()

        log.info("Configuring nextcloud Social Login app")
        # this is the blob used to configure the Nextcloud Social Login App
        oidc_json = dumps({
                "custom_oidc": [{
                    "name": "Zitadel",
                    "title": "Zitadel",
                    "authorizeUrl": f"https://{zitadel_host}/oauth/v2/authorize",
                    "tokenUrl": f"https://{zitadel_host}/oauth/v2/token",
                    "userInfoUrl": f"https://{zitadel_host}/oauth/v2/userinfo",
                    "logoutUrl": "", 
                    "clientId": client_id,
                    "clientSecret": client_secret,
                    "scope": "openid",
                    "groupsClaim": "groups",
                    "style": "zitadel",
                    "defaultGroup": "nextcloud_users"
                    }]
                })

        cmd = f" config:app:set sociallogin custom_providers --value='{oidc_json}'"
        subproc([self.occ_cmd + cmd + '"'])
