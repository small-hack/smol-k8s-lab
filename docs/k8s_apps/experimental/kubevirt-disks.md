# Kubevirt Disks

Disk management is a critical part of Kubevirt operations. There are many types of disks and many ways to create them. Which type/method is best will depend entirely upon your use-case. For example, Kubevirt only supports live-migration and snapshot backups when disks are created using the `ReadWriteMany` StorageClass.

## Standard PVC Disks

Defining disks a PVCs is the most common way to create disks in Kubevirt. PVCs can hold cloud-images, ISO files, full machine snapshots and more. However, once you have attached a PVC to a VM, any changes to the data inside the PVC is permanent.

Standard PVC disks may not be ideal when creating multiple VMs since you would need to re-download the image file and create a whole new PVC each time you create a new VM. </br></br>

A standard PVC disk manifest:

```yaml
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: debian12-pvc
  labels:
    app: containerized-data-importer
  annotations:
    cdi.kubevirt.io/storage.bind.immediate.requested: "true"
    cdi.kubevirt.io/storage.import.endpoint: "https://cloud.debian.org/images/cloud/bookworm/daily/latest/debian-12-generic-amd64-daily.qcow2"
spec:
  storageClassName: local-path
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 32Gi
```

## DataVolumes

DataVolumes are a shortcut for creating new PVC disks. Instead of mounting the PVC directly to the VM, a DataVolume manifest tells the CDI to first create a unique copy of the target PVC. This copy will then be mounted to the VM leaving the original unchanged. DataVolumes can be sourced from PVCs in other namespaces and also be re-sized before mounting.

While DataVolumes can avoid the cost of downloading and converting the image, there is a copy action that takes place during their creation which takes some time depending on your disk speed and the image size.

In addition to the above, DataVolumes can also be created from HTTP, S3, and OCI targets. While that is not any faster than using a standard PVC workflow, it does save quite a few lines of code.</br></br>

A manifest for DataVolume which copies a PVC:

```yaml
---
# The datavolume is the VM's harddrive
apiVersion: cdi.kubevirt.io/v1alpha1
kind: DataVolume
metadata:
  name: vm0-dv
  namespace: vm0
spec:
  source:
    pvc:
      namespace: default
      name: debian12-pvc
  pvc:
    accessModes:
      - ReadWriteOnce
    resources:
      requests:
        storage: 120Gi
```

## Ephemeral Disks

Ephemeral disks are similar to a DataVolumes in that they create a unique copy of an image, however they do not provide any persistence and are deleted upon termination of the VM. Without the backing of a PVC there is no copy action at instantiation time which makes ephemeral disks very fast to create.

Ephemeral disks are great for use with VM Pools, CICD Runners, and other use-cases which do not require persistence beyond the life-cycle of the workload.

- 

## Pre-Creating Images

For users who want their VM to be created as quickly as possible, the best option is to pre-create any disks you may need prior to creating a VM. This negates the need to wait for images to download and be converted before the VM can start (30-60 seconds). Images can either be manually uploaded to the CDI or defined as manifests for the CDI to consume.


1. Below we will pre-create a PVC which contains a cloud-image by downloading the image locally, and then pushing it to the CDI within our cluster.


    ```bash
    export VOLUME_NAME=debian12-pvc
    export NAMESPACE="default"
    export STORAGE_CLASS="local-path"
    export ACCESS_MODE="ReadWriteOnce"
    export IMAGE_URL="https://cloud.debian.org/images/cloud/bookworm/daily/latest/debian-12-generic-amd64-daily.qcow2"
    export IMAGE_PATH=debian-12-generic-amd64-daily.qcow2
    export VOLUME_TYPE=pvc
    export SIZE=32Gi
    export PROXY_ADDRESS=$(kubectl get svc cdi-uploadproxy -n cdi -o json | jq --raw-output '.spec.clusterIP')
    
    time wget -O $IMAGE_PATH $IMAGE_URL && \
    time virtctl image-upload $VOLUME_TYPE $VOLUME_NAME \
        --size=$SIZE \
        --image-path=$IMAGE_PATH \
        --uploadproxy-url=https://$PROXY_ADDRESS:443 \
        --namespace=$NAMESPACE \
        --storage-class=$STORAGE_CLASS \
        --access-mode=$ACCESS_MODE \
        --insecure --force-bind
    ```

2. The same process can also be used with ISO images which we would like to use as boot-media for VMs

    ```bash
    export VOLUME_NAME="windows10-iso-pvc"
    export NAMESPACE="default"
    export STORAGE_CLASS="local-path"
    export ACCESS_MODE="ReadWriteOnce"
    export IMAGE_URL="https://www.itechtics.com/?dl_id=173"
    export IMAGE_PATH="Win10_22H2_EnglishInternational_x64.iso"
    export VOLUME_TYPE="pvc"
    export SIZE="8Gi"
    export PROXY_ADDRESS=$(kubectl get svc cdi-uploadproxy -n cdi -o json | jq --raw-output '.spec.clusterIP')
    
    time wget -O $IMAGE_PATH $IMAGE_URL && \
    time virtctl image-upload $VOLUME_TYPE $VOLUME_NAME \
        --size=$SIZE \
        --image-path=$IMAGE_PATH \
        --uploadproxy-url=https://$PROXY_ADDRESS:443 \
        --namespace=$NAMESPACE \
        --storage-class=$STORAGE_CLASS \
        --access-mode=$ACCESS_MODE \
        --insecure --force-bind
    ```

3. In this example we define the same Debian12 cloud-image as in the first example, except this time we define it as a manifest which the CDI can consume directly.

    ```yaml
    ---
    apiVersion: v1
    kind: PersistentVolumeClaim
    metadata:
      name: "debian12"
      labels:
        app: containerized-data-importer
      annotations:
        cdi.kubevirt.io/storage.bind.immediate.requested: "true"
        cdi.kubevirt.io/storage.import.endpoint: "https://cloud.debian.org/images/cloud/bookworm/daily/latest/debian-12-generic-amd64-daily.qcow2"
    spec:
      storageClassName: local-path
      accessModes:
        - ReadWriteOnce
      resources:
        requests:
          storage: 32Gi
    ```

## Creation at Runtime

Disks can also be created at runtime via a manifest. This will trigger the CDI to download the image and convert it to a PVC before starting the VM. It is more convenient than manually pre-creating the image but increases the time a user must wait before their VM is ready.

- In the following example we define the disk and a VM as manifests which will be applied at the same time. The VM will not start until the cloud-image has been downloaded and written to a PVC.


    ```yaml
    # The PVC holds the original copy of the cloud-image
    ---
    apiVersion: v1
    kind: PersistentVolumeClaim
    metadata:
      name: debian12
      labels:
        app: containerized-data-importer
      annotations:
        cdi.kubevirt.io/storage.bind.immediate.requested: "true"
        cdi.kubevirt.io/storage.import.endpoint: "https://cloud.debian.org/images/cloud/bookworm/daily/latest/debian-12-generic-amd64-daily.qcow2"
    spec:
      storageClassName: local-path
      accessModes:
        - ReadWriteOnce
      resources:
        requests:
          storage: 32Gi
    ---
    # Create the VM
    apiVersion: kubevirt.io/v1
    kind: VirtualMachine
    metadata:
      generation: 1
      labels:
        kubevirt.io/os: linux
        metallb-service: vm0
      name: vm0
    spec:
      runStrategy: "RerunOnFailure"
      template:
        metadata:
          creationTimestamp: null
          labels:
            kubevirt.io/domain: vm0
            metallb-service: vm0
        spec:
          domain:
            cpu:
              sockets: 1
              cores: 2
              threads: 1
            firmware:
              bootloader:
                efi: {}
            devices:
              autoattachPodInterface: true
              autoattachSerialConsole: true
              autoattachGraphicsDevice: true
              disks:
              - name: harddrive
                disk:
                  bus: virtio
                bootOrder: 2
              - name: cloudinitvolume
                cdrom:
                  bus: sata
                  readonly: true
                bootOrder: 1
              interfaces:
                - masquerade: {}
                  name: default
            machine:
              type: q35
            resources:
              limits:
                memory: 2Gi
          networks:
          - name: default
            pod: {}
          volumes:
            - name: harddrive
              persistentVolumeClaim:
                claimName: debian12
            - name: cloudinitvolume
              cloudInitNoCloud:
                userData: |
                  #cloud-config
                  hostname: debian
                  ssh_pwauth: True
                  disable_root: false
                  users:
                   - name: friend
                     groups: users, admin, sudo
                     sudo: ALL=(ALL) NOPASSWD:ALL
                     shell: /bin/bash
                     lock_passwd: false
                     passwd: "$6$rounds=4096$saltsaltlettuce$Lp/FV.2oOgew7GbM6Nr8KMGMBn7iFM0x9ZwLqtx9Y4QJmKvfcnS.2zx4MKmymCPQGpHS7gqYOiqWjvdCIV2uN."
    ```
