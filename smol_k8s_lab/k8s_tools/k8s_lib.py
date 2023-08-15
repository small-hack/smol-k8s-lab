from __future__ import print_function
from kubernetes import client, config, utils
from kubernetes.client.rest import ApiException
import logging as log
import yaml


# this lets us do multi line yaml values
yaml.SafeDumper.org_represent_str = yaml.SafeDumper.represent_str


# this too lets us do multi line yaml values
def repr_str(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar(u'tag:yaml.org,2002:str', data,
                                       style='|')
    return dumper.org_represent_str(data)


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

    def create_secret(self,
                      name: str = "",
                      namespace: str = "",
                      str_data: str = "",
                      inline_key: str = "",
                      labels: dict = {}) -> bool:
        """
        Create a Kubernetes secret
        """

        meta = client.V1ObjectMeta(name=name)

        if labels:
            meta = client.V1ObjectMeta(name=name, labels=labels)

        # handles if we need to nest a file's contents in a secret value
        if inline_key:
            # these are all app secrets we collected at the start of the script
            secret_keys = yaml.dump(str_data)
            inline_key_dict = {inline_key: secret_keys}
            # V1Secret: kubernetes-client/python:kubernetes/docs/V1Secret.md
            body = client.V1Secret(metadata=meta, string_data=inline_key_dict)
        else:
            # V1Secret: kubernetes-client/python:kubernetes/docs/V1Secret.md
            body = client.V1Secret(metadata=meta, string_data=str_data)

        # output is pretty printed. (optional)
        pretty = True

        try:
            res = self.api_instance.create_namespaced_secret(namespace, body,
                                                             pretty=pretty)
            log.info(res)
        except ApiException as e:
            log.error("Exception when calling "
                      f"CoreV1Api->create_namespaced_secret: {e}")
