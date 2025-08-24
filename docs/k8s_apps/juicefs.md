# JuiceFS

JuiceFS is a S3-backed distributed file-system which uses a local Valkey instance to provide higher levels of read/write performance than NFS or SeaweedFS-CSI-Driver. Max uses it to mount SeaweedFS buckets containing video-games and virtual-machine disks which are too latency-sensitive to work well with other network-backed file systems. Valkey is used as a database here, so it's PVCs need to be backed up or you will lose data.
There are a few really nice write-up's by SmartMore outlining the organizations use of SeaweedFS + JuiceFS here:
- https://juicefs.com/en/blog/usage-tips/seaweedfs-tikv
- https://juicefs.com/en/blog/user-stories/ai-training-storage-selection-seaweedfs-juicefs
- https://juicefs.com/en/blog/user-stories/deep-learning-ai-storage#Why-choose-SeaweedFS-for-object-storage


Features:
- POSIX Compatible: JuiceFS can be used like a local file system, making it easy to integrate with existing applications.
- HDFS Compatible: JuiceFS is fully compatible with the HDFS API, which can enhance metadata performance.
- S3 Compatible: JuiceFS provides an S3 gateway to implement an S3-compatible access interface.
- Cloud-Native: It is easy to use JuiceFS in Kubernetes via the CSI Driver.
- Distributed: Each file system can be mounted on thousands of servers at the same time with high-performance concurrent reads and writes and shared data.
- Strong Consistency: Any changes committed to files are immediately visible on all servers.
- Outstanding Performance: JuiceFS achieves millisecond-level latency and nearly unlimited throughput depending on the object storage scale (see performance test results).
- Data Security: JuiceFS supports encryption in transit and encryption at rest (view Details).
- File Lock: JuiceFS supports BSD lock (flock) and POSIX lock (fcntl).
- Data Compression: JuiceFS supports the LZ4 and Zstandard compression algorithms to save storage space.

## Depenencies

1. JuiceFS assumes you already have an existing S3 proivder + bucket to store your files in.
2. You'll also need a bucket for for the Valkey PVC backups.


Example Config:

```yaml
  juicefs:
    enabled: false
    description: |
      [link=https://github.com/juicedata/juicefs]juicefs[/link] JuiceFS is a distributed POSIX file system built on top of Redis and S3 (but we use Valkey and SeaweedFS).
    init:
      enabled: false
      restore:
        # set to true to run a restic restore via a k8up job for:
        # seaweedfs pvcs and nextcloud files pvc
        enabled: false
        # for Cloudnative Postgres operator "cluster" CRD type resources
        cnpg_restore: true
        # restic snapshot ID for each PVC
        restic_snapshot_ids:
          # juicefs-valkey-primary volume pvc snapshot id
          juicefs_primary: "latest"
          # juicefs-valkey-replica volume pvc snapshot id
          juicefs_replica: "latest"
      values: []
    backups:
      # cronjob syntax schedule to run nextcloud pvc backups
      pvc_schedule: 10 0 * * *
      # cronjob syntax (with SECONDS field) for nextcloud postgres backups
      # must happen at least 10 minutes before pvc backups, to avoid corruption
      # due to missing files. This is because the cnpg backup shows as completed
      # before it actually is, due to the wal archive it lists as it's end not
      # being in the backup yet
      postgres_schedule: 0 0 0 * * *
      s3:
        # these are for pushing remote backups of your local s3 storage, for speed and cost optimization
        endpoint: ""
        bucket: ""
        region: ""
        secret_access_key:
          value_from:
            env: JUICEFS_S3_BACKUP_SECRET_KEY
        access_key_id:
          value_from:
            env: JUICEFS_S3_BACKUP_ACCESS_ID
      restic_repo_password:
        value_from:
          env: JUICEFS_RESTIC_REPO_PASSWORD
    argo:
      # secrets keys to make available to Argo CD ApplicationSets
      secret_keys:
        valkey_url: valkey.juicefs.svc.cluster.local
        valkey_port: "6379"
        valkey_password:
          value_from:
            env: JUICEFS_VALKEY_PASSWORD
        s3_bucket_url: ""
        s3_key_id:
          value_from:
            env: JUICEFS_S3_KEY_ID
        s3_secret_key:
          value_from:
            env: JUICEFS_S3_SECRET_KEY
        s3_dshboard_url: juicefs.vleermuis.tech
      # git repo to install the Argo CD app from
      repo: https://github.com/small-hack/argocd-apps
      # path in the argo repo to point to. Trailing slash very important!
      path: demo/juicefs/app_of_apps/
      # either the branch or tag to point at in the argo repo above
      revision: finish-juicefs
      # kubernetes cluster to install the k8s app into, defaults to Argo CD default
      cluster: https://kubernetes.default.svc
      # namespace to install the k8s app in
      namespace: juicefs
      # recurse directories in the provided git repo
      # if set to false, we will not deploy the CSI driver
      directory_recursion: true
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        name: juicefs
        source_repos:
          - https://juicedata.github.io/charts/
          - oci://registry-1.docker.io/
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces: []
```
