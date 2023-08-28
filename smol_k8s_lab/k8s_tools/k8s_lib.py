from __future__ import print_function
from json import loads
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import logging as log
import yaml
# local imports
from ..utils.subproc import subproc


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

    def create_secret(self,
                      name: str,
                      namespace: str,
                      str_data: str,
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

    def get_secret(self, name: str, namespace: str) -> dict:
        """
        get an existing k8s secret
        """
        log.debug(f"Getting secret: {name} in namespace: {namespace}")

        res = subproc([f"kubectl get secret -n {namespace} {name} -o json"])
        return loads(res)

    def delete_secret(self, name: str, namespace: str) -> dict:
        """
        get an existing k8s secret
        """
        log.debug(f"Deleting secret: {name} in namespace: {namespace}")

        subproc([f"kubectl delete secret -n {namespace} {name}"])
        return True

    def get_namespace(self, name: str) -> bool:
        """
        checks for specific namespace and returns True if it exists,
        returns False if namespace does not exist
        """
        nameSpaceList = self.core_v1_api.list_namespace()
        for nameSpace_obj in nameSpaceList.items:
            if nameSpace_obj.metadata.name == name:
                return True
        log.debug(f"Namespace, {name}, does not exist yet")
        return False

    def create_namespace(self, name: str) -> True:
        """
        Create namespace with name
        """
        if not self.get_namespace(name):
            log.info(f"Creating namespace: {name}")
            meta = client.V1ObjectMeta(name=name)
            namespace = client.V1Namespace(metadata=meta)

            self.core_v1_api.create_namespace(namespace)
        else:
            log.debug(f"Namespace, {name}, already exists")
        return True

    def reload_deployment(self, name: str, namespace: str) -> True:
        """
        restart a deployment's pod scaling it up and then down again
        currently only works with one pod
        """
        subproc([f"kubectl scale deploy -n {namespace} {name} --replicas=0",
                 "sleep 3",
                 f"kubectl scale deploy -n {namespace} {name} --replicas=1"])


    # def create_from_manifest_dict(self,
    #                               api_group: str = "",
    #                               api_version: str = "",
    #                               namespace: str = "",
    #                               plural_obj_name: str = "",
    #                               manifest_dict: dict = {}) -> bool:
    #     """
    #     NOT working! see: https://github.com/kubernetes-client/python/issues/2103
    #     I just don't want to have to write this again if the bug is fixed
    #     creates any resource in k8s from a python dictionary
    #     """
    #     custom_obj_api = client.CustomObjectsApi(self.api_client)
    #     try:
    #         # create the resource
    #         custom_obj_api.create_namespaced_custom_object(
    #                 group=api_group,
    #                 version=api_version,
    #                 namespace=namespace,
    #                 plural=plural_obj_name,
    #                 body=manifest_dict,
    #             )
    #     except ApiException as e:
    #         log.error("Exception when calling CustomObjectsApi->"
    #                   f"create_namespaced_custom_object: {e}")
    #     return True
