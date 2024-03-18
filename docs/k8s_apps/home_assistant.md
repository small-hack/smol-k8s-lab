[Home Assistant](https://www.home-assistant.io/) is an open source IoT management solution. We deploy a [small-hack maintained helm chart](https://github.com/small-hack/home-assistant-chart/) by default.

<img src="../../assets/images/screenshots/home-assistant_screenshot.png" alt="screenshot of the home-assistant-app in Argo CD showing a tree featuring a configmap, pvc, service, service account, deployment, and ingress resource all called home-assistant.">

The main variable you need to worry about when setting up home assistant is your `hostname`.

You'll need the [Generic Device Plugin](/k8s_apps/generic-device-plugin.md) as a prereq in order to use USB devices with home assistant.

## Example configs

### Using tolerations and node affinity

```yaml
apps:
  home_assistant:
    enabled: true
    description: |
      [link=https://home-assistant.io]Home Assistant[/link] is a home IOT management solution.

      By default, we assume you want to use node affinity and tolerations to keep home assistant pods on certain nodes and keep other pods off said nodes. If you don't want to use either of these features but still want to use the small-hack/argocd-apps repo, first change the argo path to /home-assistant/ and then remove the 'toleration_' and 'affinity' secret_keys from the yaml file under apps.home_assistant.description.
    argo:
      secret_keys:
        hostname: "home-assistant.cooldomainfordogs.biz"
        unit_system: "metric"
        temperature_unit: "C"
        # tolerate taints
        toleration_key: "iot"
        toleration_operator: "Equal"
        toleration_value: "true"
        toleration_effect: "NoSchedule"
        # make the node attractive
        affinity_key: "iot"
        affinity_value: "true"
        # these are for passing in a USB device such as the conbee II
        # this is the path on the node
        usb_device_path: "/dev/serial/by-id/usb-ITEAD_SONOFF_Zigbee_3.0_USB_Dongle_Plus_V2_20230509111242-if00"
        # this is the path on the container
        usb_device_mount_path: "/dev/ttyACM0"
        # this is the generic device plugin device index
        usb_device_index: "1"
      repo: https://github.com/small-hack/argocd-apps
      path: home-assistant/toleration_and_affinity/
      revision: main
      namespace: home-assistant
      directory_recursion: false
      project:
        source_repos:
          - https://small-hack.github.io/home-assistant-chart
        destination:
          namespaces:
            - argocd
```

### Without tolerations and node affinity

```yaml
apps:
  home_assistant:
    enabled: true
    description: |
      [link=https://home-assistant.io]Home Assistant[/link] is a home IOT management solution.
    argo:
      secret_keys:
        hostname: "home-assistant.cooldomainfordogs.biz"
        unit_system: "metric"
        temperature_unit: "C"
      repo: https://github.com/small-hack/argocd-apps
      path: home-assistant/
      revision: main
      namespace: home-assistant
      directory_recursion: false
      project:
        source_repos:
          - http://small-hack.github.io/home-assistant-chart
        destination:
          namespaces:
            - argocd
```
