# Kubevirt

[Kubevirt](https://kubevirt.io/) allows users to run QEMU virtual machines inside of Kubernetes.

## Installation

- Install via ArgoCD with [Kubevirt Argo CD ApplicationSet](https://github.com/small-hack/argocd-apps/tree/main/kubevirt)

- Install via Helm using [Kubevirt Community Stack](https://github.com/cloudymax/kubevirt-community-stack)

## Components

Kubevirt is made up of several pieces:

1. **Kubervirt Operator**

    The operator controls virtual machine instances and provides the CRDs that define them
</br></br>

2. **Kubevirt CDI**

    The Containerized Data Importer can pull virtual machine images, ISO files, and other types of bootable media from sources like S3, HTTP, or OCI images. This data is then written to PVCs which are mounted as disks. For examples of various ways to use the CDI, see the notes in the [argocd-apps repo](https://github.com/small-hack/argocd-apps/blob/main/kubevirt/examples/disks/Disks.md) </br></br>

3. **Kubevirt Manager**

    This is a community-developed web-ui which allows users to create, manage, and interact with virtual machines running in Kubevirt. See their official docs at [kubevirt-manager.io](https://kubevirt-manager.io/)

<p align="center">
  <a href="../../../images/screenshots/kubevirt-manager.png">
      <img src="../../../images/screenshots/kubevirt-manager.png" alt="Screenshot showing the default page of Kubevirt-manager. The screen is devided into 2 sections. On the left, there is a vertical navigation tab with a grey background. The options in this bar are Dashboard, Virtual Machines, VM Pools, Auto Scaling, Nodes, Data Volumes, Instance Types, and Load Balancers.  On the right, there is a grid of blue rectangular icons each representing one of the option in the navigation tab, but with an icon and text representing metrics about that option." width=500>
  </a>
</p>



## Utilities

1. libvirt-clients

    This utility will audit a host machine and report what virtualisation capabilities are available

    - Installation

        ```bash
        sudo apt-get install -y libvirt-clients
        ```

    - Usage

        ```console
        $ virt-host-validate qemu
        QEMU: Checking for hardware virtualization          : PASS
        QEMU: Checking if device /dev/kvm exists            : PASS
        QEMU: Checking if device /dev/kvm is accessible     : PASS
        QEMU: Checking if device /dev/vhost-net exists      : PASS
        QEMU: Checking if device /dev/net/tun exists        : PASS
        ```

2. virtctl

    virtctl is the command-line utility for managing Kubevirt resources. It can be installed as a standalone CLI or as a Kubectl plugin via krew.

    - Standalone

        ```bash
        export VERSION=v0.41.0
        wget https://github.com/kubevirt/kubevirt/releases/download/${VERSION}/virtctl-${VERSION}-linux-amd64
        ```

    - Plugin

        ```bash
        kubectl krew install virt
        ```

## Uninstall

In the event that Kubevirt does not uninstall gracefully, you may need to perform the following steps:

```bash
export RELEASE=v0.17.0

# --wait=true should anyway be default
kubectl delete -n kubevirt kubevirt kubevirt --wait=true

# this needs to be deleted to avoid stuck terminating namespaces
kubectl delete apiservices v1.subresources.kubevirt.io

# not blocking but would be left over
kubectl delete mutatingwebhookconfigurations virt-api-mutator

# not blocking but would be left over
kubectl delete validatingwebhookconfigurations virt-operator-validator

# not blocking but would be left over
kubectl delete validatingwebhookconfigurations virt-api-validator

kubectl delete -f https://github.com/kubevirt/kubevirt/releases/download/${RELEASE}/kubevirt-operator.yaml --wait=false
```
