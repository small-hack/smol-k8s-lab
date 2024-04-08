You'll need the [Generic Device Plugin](https://github.com/squat/generic-device-plugin) as a prereq in order to use USB devices with home assistant or any other app on k8s, so we provide a basic Argo CD app for that :)

## Example config

```yaml
apps:
  generic_device_plugin:
    enabled: true
    description: |
      This installs the [link=https://github.com/squat/generic-device-plugin/tree/main]squat/generic-device-plugin[/link], which is recommended for exposing generic devices such as USB devices to your k8s pods. This can useful if you have an IoT coordinator device such as the conbee 2 that you are using with deconz or home assistant. You can read more about device plugins in the [link=https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins/]Kubernetes docs[/link]
    argo:
      secret_keys: {}
      repo: https://github.com/small-hack/argocd-apps
      path: generic-device-plugin/
      revision: main
      namespace: kube-system
      directory_recursion: false
      project:
        name: generic-device-plugin
        source_repos:
          - https://github.com/squat/generic-device-plugin
        destination:
          namespaces:
            - kube-system
```
