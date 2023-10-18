[k8tz](https://github.com/k8tz/k8tz) exists because try as we might, time is still hard. It is a Kubernetes admission controller and a CLI tool to inject timezones into Pods and CronJobs.

Containers do not inherit timezones from host machines and only access the clock from the kernel. The default timezone for most images is UTC, yet it is not guaranteed and may be different from container to container. With k8tz it is easy to standardize selected timezone across pods and namespaces automatically with minimal effort.

`smol-k8s-lab` uses this to ensure your cronjobs and your backups are all in the same timezone, so that if you have any special cronjobs that need to run as a _specific_ time in a _specific_ timezone, you can rest assured they will actually run at that time.

Please trust us when we say that you very likely want k8tz if you have non-standard backup processes for something like Nextcloud.

`smol-k8s-lab` requires only one variable for our default [k8tz Argo CD Application](https://github.com/small-hack/argocd-apps/tree/main/alpha/k8tz): `timezone`, which should be a timezone from the [TZ database](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List) (in the wikipedia list, you want the second column, TZ Identifier).

## example config

```yaml
apps:
  k8tz:
    enabled: false
    description: |
      k8tz is a kubernetes admission controller and a CLI tool to inject timezones into Pods and CronJobs.

      Containers do not inherit timezones from host machines and have only access to the clock from the kernel. The default timezone for most images is UTC, yet it is not guaranteed and may be different from container to container. With k8tz it is easy to standardize selected timezone across pods and namespaces automatically with minimal effort.

      You can find your timezone identifier here: [link=https://wikipedia.org/wiki/List_of_tz_database_time_zones#List]https://wikipedia.org/wiki/List_of_tz_database_time_zones[/link]

      Learn more: [link=https://github.com/k8tz/k8tz]https://github.com/k8tz/k8tz[/link]
    init:
      enabled: true
    argo:
      secret_keys:
        timezone: "Europe/Amsterdam"
      # git repo to install the Argo CD app from
      repo: "https://github.com/small-hack/argocd-apps"
      # path in the argo repo to point to. Trailing slash very important!
      path: "alpha/k8tz/"
      # either the branch or tag to point at in the argo repo above
      ref: "main"
      # namespace to install the k8s app in
      namespace: "k8tz"
      # source repos for Argo CD App Project (in addition to app.argo.repo)
      project:
        source_repos:
          - "https://k8tz.github.io/k8tz/"
        destination:
          namespaces:
            - argocd
```
