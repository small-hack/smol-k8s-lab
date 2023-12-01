# external libraries
from base64 import b64decode as b64dec
from base64 import standard_b64encode as b64enc
from json import loads
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import logging as log
from os import path
from ruamel.yaml import YAML

# internal libraries
from ..constants import XDG_CACHE_DIR
from ..utils.subproc import subproc, simple_loading_bar


class K8s():
    """
    Class for the kubernetes python client
    """

    def __init__(self):
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
                      labels: dict = {}) -> None:
        """
        Create a Kubernetes secret
        """

        meta = client.V1ObjectMeta(name=name)

        if labels:
            meta = client.V1ObjectMeta(name=name, labels=labels)

        # handles if we need to nest a file's contents in a secret value
        if inline_key:
            # https://pypi.org/project/ruamel.yaml.string/
            safe_yaml = YAML(typ=['rt', 'string'])

            # these are all app secrets we collected at the start of the script
            secret_keys = safe_yaml.dump_to_string(str_data)
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
            log.debug(res)
        except ApiException as e:
            log.error("Exception when calling "
                      f"CoreV1Api->create_namespaced_secret: {e}")
            # delete the secret if it already exists
            try:
                self.core_v1_api.delete_namespaced_secret(name, namespace)
                res = self.core_v1_api.create_namespaced_secret(namespace, body,
                                                                pretty=pretty)
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

    def delete_secret(self, name: str, namespace: str) -> None:
        """
        get an existing k8s secret
        """
        log.debug(f"Deleting secret: {name} in namespace: {namespace}")

        subproc([f"kubectl delete secret -n {namespace} {name}"])

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

    def create_namespace(self, name: str) -> None:
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

    def reload_deployment(self, name: str, namespace: str) -> None:
        """
        restart a deployment's pod scaling it up and then down again
        currently only works with one pod
        """
        # HACK: there's got to be a better way, but I don't have time to fix
        subproc([
            f"kubectl scale deploy -n {namespace} {name} --replicas=0",
            "sleep 3",
            f"kubectl scale deploy -n {namespace} {name} --replicas=1",
            f"kubectl rollout status deployment -n {namespace} {name}"
                 ])

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

    def apply_manifests(self,
                        manifest_file_name: str,
                        namespace: str = "default",
                        deployment: str = "",
                        selector: str = "component=controller"):
        """
        applies a manifest and waits with a nice loading bar if deployment
        """
        cmds = [f"kubectl apply --wait -f {manifest_file_name}"]

        if deployment:
            # these commands let us monitor a deployment rollout
            cmds.append(f"kubectl rollout status -n {namespace} "
                       f"deployment/{deployment}")

            cmds.append("kubectl wait --for=condition=ready pod --selector="
                       f"{selector} --timeout=90s -n {namespace}")

        # loops with progress bar until this succeeds
        subproc(cmds)
        return True

    def apply_custom_resources(self, custom_resource_dict_list: dict):
        """
        Does a kube apply on a custom resource dict, and retries if it fails
        using loading bar for progress
        """
        k_cmd = 'kubectl apply --wait -f '
        commands = {}
        log.debug(custom_resource_dict_list)
        yaml = YAML()

        # Write YAML data to f'{XDG_CACHE_DIR}/{resource_name}.yaml'.
        for custom_resource_dict in custom_resource_dict_list:
            resource_name = "_".join([custom_resource_dict['kind'],
                                      custom_resource_dict['metadata']['name']])
            yaml_file_name = path.join(XDG_CACHE_DIR, f'{resource_name}.yaml')

            with open(yaml_file_name, 'w') as cr_file:
                yaml.dump(custom_resource_dict, cr_file)

            commands[f'Installing {resource_name}'] = k_cmd + yaml_file_name

        # loops with progress bar until this succeeds
        simple_loading_bar(commands)

    def update_secret_key(self,
                          secret_name: str,
                          secret_namespace: str,
                          updated_values_dict: dict,
                          in_line_key_name: str = 'secret_vars.yaml') -> None:
        """
        update a key in a k8s secret
        if in_line_key_name is set to a key name, you can specify a base key in a
        secret that contains an inline yaml block
        """
        secret_data = self.get_secret(secret_name, secret_namespace)['data']

        # if this is a secret with a filename key and then inline yaml inside...
        if in_line_key_name:
            yaml = YAML(typ='safe')
            file_key = secret_data[in_line_key_name]
            decoded_data  = b64dec(str.encode(file_key)).decode('utf8')
            # load the yaml as a python dictionary
            in_line_yaml = yaml.load(decoded_data)
            # for each key, updated_value in updated_values_dict
            for key, updated_value in updated_values_dict.items():
               # update the in-line yaml
               in_line_yaml[key] = updated_value
            self.delete_secret(secret_name, secret_namespace)
            # update the inline yaml for the dict we'll feed back to
            self.create_secret(secret_name,
                               secret_namespace,
                               in_line_yaml,
                               in_line_key_name)
        else:
            for key, updated_value in updated_values_dict.items():
               # update the keys in the secret yaml one by one
               secret_data[key] = b64enc(bytes(updated_value))
            self.delete_secret(secret_name, secret_namespace)
            self.create_secret(secret_name, secret_namespace, secret_data)

    def run_k8s_cmd(self, pod_name: str, namespace: str, command: str,
                    container: str = "") -> str:
        """ 
        run a given command for a given pod in a given namespace and return the result
        """
        print(f"Running: '{command}' on pod: {pod_name} in container {container}"
              f" in namespace: {namespace}")

        run_dict = {'name': pod_name,
                    'namespace': namespace,
                    'command': command}
        if container:
            run_dict['container'] = container

        return self.core_v1_api.connect_get_namespaced_pod_exec(**run_dict)
