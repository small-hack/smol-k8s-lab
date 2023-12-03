[SeaweedFS](https://github.com/seaweedfs/seaweedfs) is:

> a fast distributed storage system for blobs, objects, files, and data lake, for billions of files! Blob store has O(1) disk seek, cloud tiering. Filer supports Cloud Drive, cross-DC active-active replication, Kubernetes, POSIX FUSE mount, S3 API, S3 Gateway, Hadoop, WebDAV, encryption, Erasure Coding. 

`smol-k8s-lab` uses SeaweedFS for spinning up isolated file systems with s3 endpoints.

Check out our [SeaweedFS Argo CD Application](https://github.com/small-hack/argocd-apps/tree/main/seaweedfs).

## Security

We enable encryption by default.

## Example config

```yaml
apps:
  seaweedfs:
    enabled: false
    description: |
      [link=https://github.com/seaweedfs/seaweedfs]seaweedfs[/link] is a filesystem with an exposable S3 endpoint.

      This is mostly meant to be for testing, but have at it :D

      If directory_recursion is set to true, we will also deploy the csi driver.
    init:
      enabled: true
      values:
        root_user: admin
    argo:
      # secrets keys to make available to Argo CD ApplicationSets
      secret_keys:
        hostname: ''
        s3_endpoint: 'seaweedfs.cooldogs.com'
        s3_region: eu-west-1
      # git repo to install the Argo CD app from
      repo: https://github.com/small-hack/argocd-apps
      # path in the argo repo to point to. Trailing slash very important!
      path: seaweedfs/app_of_apps/
      # either the branch or tag to point at in the argo repo above
      revision: main
      # namespace to install the k8s app in
      namespace: seaweedfs
      # recurse directories in the provided git repo
      # if set to false, we will not deploy the CSI driver
      directory_recursion: true
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        source_repos:
        - https://seaweedfs.github.io/seaweedfs/helm
        - https://seaweedfs.github.io/seaweedfs-csi-driver/helm
        - https://github.com/seaweedfs/seaweedfs
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces: []
```
