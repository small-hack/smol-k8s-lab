from smol_k8s_lab.utils.subproc import subproc
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from json import dumps
import logging as log


class Nextcloud():
    """
    nextcloud object for running common occ commands. occ ref:
    https://docs.nextcloud.com/server/20/admin_manual/configuration_server/occ_command.html
    """

    def __init__(self, k8s_obj: K8s, namespace: str = "nextcloud") -> None:
        """ 
        setup base occ commands to run
        """
        # namespace where nextcloud is installed
        self.namespace = namespace
        self.k8s_obj = k8s_obj
        pod_cmd = (
                f"kubectl get pods -n {self.namespace} -l "
                "app.kubernetes.io/instance=nextcloud-web-app,"
                "app.kubernetes.io/component=app "
                "--no-headers "
                "-o custom-columns=NAME:.metadata.name")
        self.pod = subproc([pod_cmd]).rstrip()
        self.occ_cmd = (
                f'kubectl exec -n {self.namespace} {self.pod} -c nextcloud -- '
                'su -s /bin/sh www-data -c "php occ'
                )

    def install_apps(self, apps: list) -> None:
        """
        installs a list of apps via nextcloud occ commands

        """
        for app in apps:
            log.info(f"Attempting to install Nextcloud app: {app}")

            cmd = f'{self.occ_cmd} app:install {app}"'
            res = subproc([cmd], shell=True, universal_newlines=True)

            log.info(res)

    def creat_oidc_group(self) -> None:
        """
        create base nextcloud groups for use with oidc
        """
        log.info("Creating nextcloud groups: nextcloud_admins, nextcloud_users")

        res = subproc([f'{self.occ_cmd} group:add nextcloud_users"'],
                      shell=True,
                      universal_newlines=True)
        log.info(res)

    def configure_zitadel_social_login(self,
                                       zitadel_host: str,
                                       client_id: str,
                                       client_secret: str) -> None: 
        """ 
        configure the nextcloud social_login app to work with zitadel
        ref: https://zitadel.com/blog/zitadel-as-sso-provider-for-selfhosting
        """
        # make sure the appropriate groups already exist
        self.creat_oidc_group()

        log.info("Configuring nextcloud Social Login app")
        # this is the blob used to configure the Nextcloud Social Login App

        oidc_json = dumps({
                "custom_oidc": [{
                    "name": "ZITADEL",
                    "title": "ZITADEL",
                    "authorizeUrl": f"https://{zitadel_host}/oauth/v2/authorize",
                    "tokenUrl": f"https://{zitadel_host}/oauth/v2/token",
                    "displayNameClaim": "preferred_username",
                    "userInfoUrl": f"https://{zitadel_host}/oidc/v1/userinfo",
                    "logoutUrl": "", 
                    "clientId": client_id,
                    "clientSecret": client_secret,
                    "scope": "openid email profile",
                    "groupsClaim": "groups",
                    "style": "zitadel",
                    "defaultGroup": "",
                    "groupMapping": {
                        "nextcloud_admins": "admin",
                        "nextgcloud_users": "nextcloud_users"
                      }
                    }]
                }).replace('"', '\\"')

        cmd = f" config:app:set sociallogin custom_providers --value='{oidc_json}'"
        final_command = self.occ_cmd + cmd + '"'
        log.info(final_command)
        res = subproc([final_command],
                      shell=True,
                      universal_newlines=True)
        log.info(res)


# this is just for testing the above class and methods
if __name__ == '__main__':
    k8s_obj = K8s()
    nc = Nextcloud(k8s_obj, "nextcloud")
    apps = ["notes", "deck"]
    # nc.install_apps(apps)
    nc.configure_zitadel_social_login(
            "zitadel.yourdomain.com",
            "your-app@your-project",
            "change me to something real")
