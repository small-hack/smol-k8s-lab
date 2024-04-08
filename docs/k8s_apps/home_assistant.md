[Home Assistant](https://www.home-assistant.io/) is an open source IoT management solution. We deploy a [small-hack maintained helm chart](https://github.com/small-hack/home-assistant-chart/) by default.

<img src="../../assets/images/screenshots/home-assistant_screenshot.png" alt="screenshot of the home-assistant-app in Argo CD showing a tree featuring a configmap, pvc, service, service account, deployment, and ingress resource all called home-assistant.">

The main variable you need to worry about when setting up home assistant is your `hostname`.

*NOTE*: You'll need to enable the [Generic Device Plugin](/k8s_apps/generic-device-plugin.md) as a prereq in order to use USB devices with home assistant.

## Example configs

### Using tolerations and node affinity

```yaml
apps:
    description: |
      [link=https://home-assistant.io]Home Assistant[/link] is a home IOT management solution.

      By default, we assume you want to use node affinity and tolerations to keep home assistant pods on certain nodes and keep other pods off said nodes. If you don't want to use either of these features but still want to use the small-hack/argocd-apps repo, first change the argo path to /home-assistant/ and then remove the 'toleration_' and 'affinity' secret_keys from the yaml file under apps.home_assistant.description.

      [b]NOTE[/b]: If you want to pass in a USB device, you will need the generic device plugin (which is available as a default Argo CD app via smol-k8s-lab 💙)

      This app takes one sensitive value, password for the initial owner user. You can also pass it in as an enviornment variable called $HOME_ASSISTANT_PASSWORD.
    # Initialization of the app through smol-k8s-lab
    init:
      # enable the creation of an initial owner user
      enabled: true
      values:
        # -- owner user's name
        name: "admin"
        # -- owner user's username
        user_name: "admin"
        # -- owner user's language, default is english
        language: "en"
      sensitive_values:
        - PASSWORD
    argo:
      secret_keys:
        hostname: ""
        # name of your home assistant area, users often just use "home"
        name: "home"
        # default alpha-2 country code, default is NL which is The Netherlands
        country: "NL"
        # currency code to use for calculating costs, defaults to EUR for euro
        currency: "EUR"
        # other option is "imperial"
        unit_system: "metric"
        # set to F for USA imperialist tempurature
        temperature_unit: "C"
        # latitude of your personal coordinates
        latitude: ""
        # longitude of your personal coordinates
        longitude: ""
        # the elevation of your house?
        elevation: ""
        # you can delete these if you're not using tolerations/affinity
        toleration_key: ""
        toleration_operator: ""
        toleration_value: ""
        toleration_effect: ""
        # these are for node affinity, delete if not in use
        affinity_key: ""
        affinity_value: ""
        # these are for passing in a USB device such as the conbee II
        usb_device_path: ""
        usb_device_mount_path: "/dev/ttyACM0"
        usb_device_index: "1"
        # these are for passing in a bluetooth device
        bluetooth_device_path: /run/dbus
        bluetooth_device_mount_path: /run/dbus
        bluetooth_device_index: '2'
      repo: https://github.com/small-hack/argocd-apps
      path: home-assistant/toleration_and_affinity/
      revision: main
      namespace: home-assistant
      directory_recursion: false
      project:
        name: home-assistant
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
    init:
      enabled: true
      values:
        # -- owner user's name
        name: "admin"
        # -- owner user's username
        user_name: "admin"
        # -- owner user's language, default is english
        language: "en"
      sensitive_values:
        - PASSWORD
    argo:
      secret_keys:
        hostname: ""
        # name of your home assistant area, users often just use "home"
        name: "home"
        # default alpha-2 country code, default is NL which is The Netherlands
        country: "NL"
        # currency code to use for calculating costs, defaults to EUR for euro
        currency: "EUR"
        # other option is "imperial"
        unit_system: "metric"
        # set to F for USA imperialist tempurature
        temperature_unit: "C"
        # latitude of your personal coordinates
        latitude: ""
        # longitude of your personal coordinates
        longitude: ""
        # the elevation of your house?
        elevation: ""
      repo: https://github.com/small-hack/argocd-apps
      path: home-assistant/
      revision: main
      namespace: home-assistant
      directory_recursion: false
      project:
        name: home-assistant
        source_repos:
          - https://small-hack.github.io/home-assistant-chart
        destination:
          namespaces:
            - argocd
```
