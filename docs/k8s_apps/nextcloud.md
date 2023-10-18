[Nextcloud](https://nextcloud.com/) is an Open Source and self hosted personal cloud. We optionally deploy it for you to save you some time in testing.

To use the default `smol-k8s-lab` Argo CD Application, you'll need to provide one time init values for:
- `admin_user`
- `smtp_user`

And you'll also need to provide the following values to be templated for your personal installation:
- `hostname`
- `backup_method`

After you select which backup method you want to use, you need to provide either:
- `backup_s3_endpoint`
- `backup_s3_bucket`

Or:
- `backup_mount_path`

You can then remove the options unrelated to the backup method you chose by removing them from the yaml. Here's an example of a correctly filled out Nextcloud app section in the `smol-k8s-lab` yaml:

```yaml
apps:
  nextcloud:
    enabled: true
    description: |
      Nextcloud Hub is the industry-leading, fully open-source, on-premises content collaboration platform. Teams access, share and edit their documents, chat and participate in video calls and manage their mail and calendar and projects across mobile, desktop and web interfaces

      Learn more: [link=https://nextcloud.com/]https://nextcloud.com/[/link]

      smol-k8s-lab supports initialization by setting up your admin username, password, and SMTP username and password, as well as your redis and postgresql credentials

      Note: smol-k8s-lab is not officially affiliated with nextcloud or vis versa
    # initialize the app by setting up new k8s secrets and/or bitwarden items
    init:
      enabled: true
      values:
        admin_user: 'mycooladminuser'
        smtp_user: 'mycoolsmtpusername'
    argo:
      # secrets keys to make available to ArgoCD ApplicationSets
      # notice that backup_mount_path has been removed
      secret_keys:
        hostname: 'cloud.coolfilesfordogs.com'
        backup_method: 's3'
        backup_s3_endpoint: 'http://minio:9000'
        backup_s3_bucket: 'nextcloudbucket'
      # git repo to install the Argo CD app from
      repo: https://github.com/small-hack/argocd-apps
      # path in the argo repo to point to. Trailing slash very important!
      path: nextcloud/
      # either the branch or tag to point at in the argo repo above
      ref: main
      # namespace to install the k8s app in
      namespace: nextcloud
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        source_repos:
        - registry-1.docker.io
        - https://nextcloud.github.io/helm
        destination:
          namespaces:
          - argocd
```

Part of the `smol-k8s-lab` init process is that we will put the following into your Bitwarden vault:
- admin credentials
- smtp credentials
- postgresql credentials

You can learn more about how the Nextcloud Argo CD ApplicationSet is installed at [small-hack/argocd-apps/nextcloud](https://github.com/small-hack/argocd-apps/tree/main/nextcloud).
