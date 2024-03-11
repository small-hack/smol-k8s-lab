[Home Assistant](https://www.home-assistant.io/) is an open source IoT management solution. We deploy a [small-hack maintained helm chart](https://github.com/small-hack/home-assistant-chart/) by default.

The main variable you need to worry about when setting up home assistant is your `hostname`.

## Example config

```yaml
apps:
  home_assistant:
    enabled: false
    description: |
      ⚠️ [magenta]demo Status[/magenta]

      Home Assistant is a home IOT management solution.
    argo:
      secret_keys:
        hostname: "home-assistant.cooldomainfordogs.biz"
      repo: https://github.com/small-hack/argocd-apps
      # note: this path may change after the home assistant app is certified
      # as production ready in the small-hack/argocd-apps repo
      path: demo/home-assistant/
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
