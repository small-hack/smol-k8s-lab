[Home Assistant](https://www.home-assistant.io/) is an open source IoT management solution. We deploy a [small-hack maintained helm chart](https://github.com/small-hack/home-assistant-chart/) by default.

The main variable you need to worry about when setting up home assistant is your `hostname`.

## Example configs

### Using tolerations and node affinity

```yaml
apps:
  home_assistant:
    enabled: false
    description: |
      [link=https://home-assistant.io]Home Assistant[/link] is a home IOT management solution.

      By default, we assume you want to use node affinity and tolerations to keep home assistant pods on certain nodes and keep other pods off said nodes. If you don't want to use either of these features but still want to use the small-hack/argocd-apps repo, first change the argo path to /home-assistant/ and then remove the 'toleration_' and 'affinity' secret_keys from the yaml file under apps.home_assistant.description.
    argo:
      secret_keys:
        hostname: "home-assistant.cooldomainfordogs.biz"
        toleration_key: "iot"
        toleration_operator: "Equals"
        toleration_value: "true"
        toleration_effect: "NoSchedule"
        affinity_key: "iot"
        affinity_value: "true"
      repo: https://github.com/small-hack/argocd-apps
      path: home-assistant/toleration_and_affinity/
      revision: main
      namespace: home-assistant
      directory_recursion: false
      project:
        source_repos:
        - http://jessebot.github.io/home-assistant-helm
        destination:
          namespaces:
          - argocd
```

### Without tolerations and node affinity

```yaml
apps:
  home_assistant:
    enabled: false
    description: |
      [link=https://home-assistant.io]Home Assistant[/link] is a home IOT management solution.
    argo:
      secret_keys:
        hostname: "home-assistant.cooldomainfordogs.biz"
      repo: https://github.com/small-hack/argocd-apps
      path: home-assistant/
      revision: main
      namespace: home-assistant
      directory_recursion: false
      project:
        source_repos:
        - http://jessebot.github.io/home-assistant-helm
        destination:
          namespaces:
          - argocd
```
