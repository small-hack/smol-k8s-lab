Sometimes you need a very generic app quickly to test something. This Argo CD ApplicationSet does just that: creates a basic deployment for you to use for testing a docker image that has no helm chart.

We have a few options in our Argo CD ApplicationSets collection:

- [deploy a deployment](https://github.com/small-hack/argocd-apps/tree/main/generic-app)
- [deploy a deployment with ingress](https://github.com/small-hack/argocd-apps/tree/main/generic-app/deployment-ingress)
- [deploy a job and no deployment](https://github.com/small-hack/argocd-apps/tree/main/generic-app/job)
- [deployment AND job](https://github.com/small-hack/argocd-apps/tree/main/generic-app/deployment-and-job)

## Example configurations

## Using a deployment with a custom app

```yaml
apps:
  generic_app:
    enabled: false
    description: |
      A generic Argo CD ApplicationSet using a generic app helm chart:
      [link=https://github.com/small-hack/generic-app-helm]https://github.com/small-hack/generic-app-helm[/link]

      You can also use this as a template and change the name of the app to your own app name.
    argo:
      secret_keys:
        # the name of the release, namespace, and project for the argocd app
        app_name: "generic-app"
        # change only if you need to use another image registry instead of docker.io
        image_registry: "docker.io"
        # change this to the image repo you want to deploy
        image_repo: "nginx"
        # change this the image tag you want to deploy
        image_tag: "latest"
      repo: https://github.com/small-hack/argocd-apps
      path: generic-app/
      revision: main
      # you could change this to your app name
      namespace: generic-app
      directory_recursion: false
      project:
        # you could change this to your app name
        name: generic-app
        source_repos:
          - https://small-hack.github.io/generic-app-helm
        destination:
          # you could change this to your app name
          namespaces:
            - generic-app
```

### deployment with ingress

```yaml
apps:
  generic_app:
    enabled: false
    description: |
      A generic Argo CD ApplicationSet using a generic app helm chart:
      [link=https://github.com/small-hack/generic-app-helm]https://github.com/small-hack/generic-app-helm[/link]

      You can also use this as a template and change the name of the app to your own app name.
    argo:
      secret_keys:
        # the name of the release, namespace, and project for the argocd app
        app_name: "generic-app"
        # change only if you need to use another image registry instead of docker.io
        image_registry: "docker.io"
        # change this to the image repo you want to deploy
        image_repo: "nginx"
        # change this the image tag you want to deploy
        image_tag: "latest"
        # the hostname you want to use for this app
        hostname: cooldogsonline.biz
      repo: https://github.com/small-hack/argocd-apps
      path: generic-app/deployment-ingress/
      revision: main
      # you could change this to your app name
      namespace: generic-app
      directory_recursion: false
      project:
        # you could change this to your app name
        name: generic-app
        source_repos:
          - https://small-hack.github.io/generic-app-helm
        destination:
          # you could change this to your app name
          namespaces:
            - generic-app
```

### job AND deployment

```yaml
apps:
  generic_app:
    enabled: false
    description: |
      A generic Argo CD ApplicationSet using a generic app helm chart:
      [link=https://github.com/small-hack/generic-app-helm]https://github.com/small-hack/generic-app-helm[/link]

      You can also use this as a template and change the name of the app to your own app name.
    argo:
      secret_keys:
        # the name of the release, namespace, and project for the argocd app
        app_name: "generic-app"
        # change only if you need to use another image registry instead of docker.io
        image_registry: "docker.io"
        # change this to the image repo you want to deploy
        image_repo: "nginx"
        # change this the image tag you want to deploy
        image_tag: "latest"
        # change only if you need to use another image registry instead of docker.io
        job_image_registry: "docker.io"
        # change this to the image repo you want to deploy
        job_image_repo: "nginx"
        # change this the image tag you want to deploy
        job_image_tag: "latest"
      repo: https://github.com/small-hack/argocd-apps
      path: generic-app/job/
      revision: main
      # you could change this to your app name
      namespace: generic-app
      directory_recursion: false
      project:
        # you could change this to your app name
        name: generic-app
        source_repos:
          - https://small-hack.github.io/generic-app-helm
        destination:
          # you could change this to your app name
          namespaces:
            - generic-app
```

### job instead of a deployment

```yaml
apps:
  generic_app:
    enabled: false
    description: |
      A generic Argo CD ApplicationSet using a generic app helm chart:
      [link=https://github.com/small-hack/generic-app-helm]https://github.com/small-hack/generic-app-helm[/link]

      You can also use this as a template and change the name of the app to your own app name.
    argo:
      secret_keys:
        # the name of the release, namespace, and project for the argocd app
        app_name: "generic-app"
        # change only if you need to use another image registry instead of docker.io
        job_image_registry: "docker.io"
        # change this to the image repo you want to deploy
        job_image_repo: "nginx"
        # change this the image tag you want to deploy
        job_image_tag: "latest"
      repo: https://github.com/small-hack/argocd-apps
      path: generic-app/job/
      revision: main
      # you could change this to your app name
      namespace: generic-app
      directory_recursion: false
      project:
        # you could change this to your app name
        name: generic-app
        source_repos:
          - https://small-hack.github.io/generic-app-helm
        destination:
          # you could change this to your app name
          namespaces:
            - generic-app
```
