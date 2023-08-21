from __future__ import print_function
from kubernetes import client, config
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
    Class for the kubernetes python client
    """
    def __init__(self,):
        """
        This is mostly for storing the k8s config
        """
        config.load_kube_config()
        self.api_client = client.ApiClient()
        self.core_v1_api = client.CoreV1Api(self.api_client)
        self.custom_obj_api = client.CustomObjectsApi(self.api_client)

    def create_from_manifest_dict(self,
                                  api_group: str = "",
                                  api_version: str = "",
                                  namespace: str = "",
                                  plural_obj_name: str = "",
                                  manifest_dict: dict = {}) -> bool:
        """
        creates any resource in k8s from a python dictionary
        not working!! https://github.com/kubernetes-client/python/issues/2103
        """
        try:
            # create the resource
            self.custom_obj_api.create_namespaced_custom_object(
                    group=api_group,
                    version=api_version,
                    namespace=namespace,
                    plural=plural_obj_name,
                    body=manifest_dict,
                )
        except ApiException as e:
            log.error("Exception when calling CustomObjectsApi->"
                      f"create_namespaced_custom_object: {e}")
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
            res = self.core_v1_api.create_namespaced_secret(namespace, body,
                                                            pretty=pretty)
            log.info(res)
        except ApiException as e:
            log.error("Exception when calling "
                      f"CoreV1Api->create_namespaced_secret: {e}")

    def get_secret(self, name: str = "", namespace: str = "") -> dict:
        """
        get an existing k8s secret
        """
        log.debug(f"Searching for secret: {name}, namespace: {namespace}")
        secrets = self.core_v1_api.list_namespaced_secret(namespace)
        log.debug(secrets)
        for secret in secrets.items:
            if secret.metadata.name == name:
                return secret

    def get_namespace(self, namespace_name: str = "") -> bool:
        """ 
        checks for specific namespace and returns True if it exists,
        returns False if namespace does not exist
        """
        nameSpaceList = self.core_v1_api.list_namespace()
        for nameSpace in nameSpaceList.items:
            if nameSpace.metadata.name == namespace_name:
                return True
        log.debug(f"namespace, {namespace_name}, does not exist yet")
        return False

    def create_namespace(self, namespace_name: str = "") -> True:
        """
        Create namespace with namespace_name
        """
        if not self.get_namespace(namespace_name):
            log.info(f"Creating namespace: {namespace_name}")
            meta = client.V1ObjectMeta(name=namespace_name)
            namespace = client.V1Namespace(metadata=meta)

            self.core_v1_api.create_namespace(namespace)
        else:
            log.debug(f"namespace, {namespace_name}, already exists")
        return True

    def delete_pod_of_deployment(self, name: str = "",
                                 namespace: str = "") -> True:
        """
        restart a deployment's pod by deleting it
        """
        pods = self.core_v1_api.list_namespaced_pod(namespace)
        for pod in pods.items:
            if name in pod.metadata.name:
                log.info(f"Deleting pod, [orange]{pod.metadata.name}[/]")
                self.core_v1_api.delete_namespaced_pod(pod, namespace)
