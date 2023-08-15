from __future__ import print_function
from kubernetes import client, config, utils
from client.rest import ApiException
import logging as log


class K8s():
    """
    Python Wrapper for the Bitwarden cli
    """
    def __init__(self,):
        """
        This is mostly for storing the k8s config
        """
        config.load_kube_config()
        self.api_client = client.ApiClient()
        self.api_instance = client.CoreV1Api(self.api_client)

    def create_from_manifest_dict(self, manifest_dict: dict = {}) -> bool:
        """
        creates any resource in k8s from a python dictionary
        """
        utils.create_from_dict(self.api_client, manifest_dict)
        return True

    def create_secret(self, name: str = "", namespace: str = "",
                                            str_data: str = "") -> bool:
        # V1Secret: kubernetes-client/python:kubernetes/docs/V1Secret.md
        body = client.V1Secret(metadata=client.V1ObjectMeta(name=name),
                               string_data=str_data)
        # str | If 'true', then the output is pretty printed. (optional)
        pretty = True

        try:
            res = self.api_instance.create_namespaced_secret(namespace, body,
                                                             pretty=pretty)
            log.info(res)
        except ApiException as e:
            log.error("Exception when calling "
                      f"CoreV1Api->create_namespaced_secret: {e}")
