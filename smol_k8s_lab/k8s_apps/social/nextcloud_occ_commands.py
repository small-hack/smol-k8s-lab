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
        # TODO: name of the nextcloud pod to run the commands on
        pod = ""
        self.occ_cmd = (f'kubectl exec {pod} -- su -s /bin/sh www-data -c '
                        '"php occ')

    def install_apps(self, apps: list) -> None:
        """
        installs a list of apps via nextcloud occ commands
        """
        log.info(f"Attempting to install the following Nextcloud apps: {apps}")

        for app in apps:
            log.info(f"Attempting to install Nextcloud app: {app}")
            subproc([f'{self.occ_cmd} app:install {app}"'])
