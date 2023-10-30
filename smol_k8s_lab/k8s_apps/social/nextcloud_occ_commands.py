from smol_k8s_lab.utils.subproc import subproc
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
