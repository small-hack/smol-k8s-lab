# Kubevirt Community Stack

This app deploys all the resources you need to get started with Kubevirt on your existing cluster: see https://github.com/cloudymax/kubevirt-community-stack.

The Kubevirt-Community-Stack may be of interest if you:

- operate one or more physical computers which you would like to split into smaller virtual machines.
- are already running kubernetes to orchestrate container workloads
- are already in the <a href="https://argoproj.github.io/cd/">ArgoCD</a> or <a href="https://github.com/kubevirt/kubevirt-tekton-tasks?tab=readme-ov-file">Tekton</a> ecosystem and/or work primarily with some other Helm-based tooling.
- want/need fully-featured VMs for things like hardware emulation, hardware-passthrough, Virtual Desktops, vGPU, etc... which are not suppoted by Micro-VMs such as <a href="https://firecracker-microvm.github.io/">Firecracker</a>.
- want to integrate Kubevirt into your existing infrastructure without needing to adopt a full platform like <a href="https://www.redhat.com/en/technologies/cloud-computing/openshift/virtualization">OpenShift Virtuazation</a>, <a href="https://harvesterhci.io/">HarvesterHCI</a>, <a href="https://www.starlingx.io/">StarlingX</a>, or <a href="">KubeSphere</a> etc...
- want to install and operate Kubevirt on an existing system withhout needing to re-image it with an installer ISO.
- desire tight integration with cloud-init while respecting git-ops best practices
- prefer to use cloud-init for system configuration over ansible & packer based workflows

## Components

<details>
  <summary>Kubervirt</summary>
  <br>
  <a href="https://github.com/kubevirt/kubevirt">Kubevirt</a> is a Kubernetes Virtualization API and runtime which controls QEMU/KVM virtual machine instances and provides the CRDs that define them. It's distrubuted as a Kubernetes Operator which is install via the <a href="https://github.com/kubevirt/kubevort">kubevirt</a> chart.
  <br>
  <br>
</details>

<details>
  <summary>Kubevirt CDI</summary>
  <br>
  The <a href="https://github.com/kubevirt/containerized-data-importer">Containerized Data Importer</a> can pull virtual machine images, ISO files, and other types of bootable media from sources like S3, HTTP, or OCI images. This data is then written to PVCs which are mounted as disks. For examples of various ways to use the CDI, see the notes in <a href="https://github.com/small-hack/argocd-apps/blob/main/kubevirt/examples/disks/Disks.md">Argocd-Apps</a>
  <br>
  <br>
</details>

<details>
  <summary>Cloud-Init</summary>
  <br>
  The <a href="https://github.com/cloudymax/kubevirt-community-stack/tree/main/charts/cloud-init">Cloud-init helm chart</a> allows the user to define the specification of a linux-based vm's operating system as code. In addition to basec cloud-init functions, his chart provides some extra functionality via an initjob that makes cloud-init more GitOps friendly.
  <br>
  <br>
Additional Features:

  - Regex values using existing secrets or environmental variables via envsubst
  - Create random user passwords or use an existing secret
  - Download files from a URL
  - Base64 encode + gzip your `write_files` content
  - Populate Wireguard configuration values from an existsing secret
  - Track the total size of user-data and check file for valid syntax
  <br>
  <br>
</details>

<details>
  <summary>Kubevirt VM</summary>
  <br>
  The <a href="https://github.com/cloudymax/kubevirt-community-stack/tree/main/charts/kubevirt-vm">Kubevirt-VM Chart</a> allows a user to easily template a Kubevirt VirtualMachine or VirtualMachinePool and its associated resources sudch as Disks, DataVolumes, Horizontal Pod Autoscaler, Network Policies, Service, Ingres, Probes, and Cloud-init data (via bundled cloud-init subchart).
  <br>
  <br>
</details>

<details>
  <summary>Kubevirt Manager</summary>
  <br>
      This is a community-developed web-ui which allows users to create, manage, and interact with virtual machines running in Kubevirt. See their official docs at <a href="https://kubevirt-manager.io/">kubevirt-manager.io</a>
  <br>
  <br>

  <p align="center">
  <a href="https://github.com/cloudymax/kubevirt-community-stack/assets/84841307/eeb87969-4dd6-49ce-b25e-37404e05fa72">
      <img src="https://github.com/cloudymax/kubevirt-community-stack/assets/84841307/eeb87969-4dd6-49ce-b25e-37404e05fa72" alt="Screenshot showing the default page of Kubevirt-manager. The screen is devided into 2 sections. On the left, there is a vertical navigation tab with a grey background. The options in this bar are Dashboard, Virtual Machines, VM Pools, Auto Scaling, Nodes, Data Volumes, Instance Types, and Load Balancers.  On the right, there is a grid of blue rectangular icons each representing one of the option in the navigation tab, but with an icon and text representing metrics about that option." width=500>
  </a>
  </p>
  <br>
  <br>
</details>

<details>
  <summary>Cluster API Operator & Addons</summary>
  <br>
   <a href="https://cluster-api.sigs.k8s.io/">Cluster API</a> provides a standardised kubernetes-native interface for creating k8s clusters using a wide variety of providers. The combined chart can install the <a href="https://cluster-api-operator.sigs.k8s.io/">Cluster API Operator</a> as well as bootstrap the <a href="https://github.com/kubernetes-sigs/cluster-api-provider-kubevirt">Cluster API Kubevirt Provider</a> which allows creating k8s clusters from the CLI or as YAML using Kubevirt VMs. Cluster-api-provider-kubevirt also includes <a href="https://github.com/kubevirt/cloud-provider-kubevirt">cloud-provider-kubevirt</a> which enables the exposeure of LoadBalancer type services within tenant clusters to the host cluster. This negates the need for a dedicated loadbalancer such as <a href="https://metallb.io/">MetalLB</a> inside the tenant cluster.
  <br>
  <br>
See <a href="https://github.com/cloudymax/kubevirt-community-stack/blob/main/CAPI.md">CAPI.md</a> for a basic walkthrough of creating a CAPI-based tenant cluster.
  <br>
  <br>
</details>

<details>
  <summary>CAPI Cluster</summary>
  <br>
  The CAPI Cluster helm chart provides a way to create workload clusters using the Kubevirt infrastructure, Kubeadm Bootstrap + ControlPlane, and Helm providers.
  <br>
  <br>
</details>


Example Config:

```yaml
  kubevirt:
    description: |
      [link=https://kubevirt.io/]kubevirt[/link] lets you manage virtual machines via Kubernetes.
    # default disabled while a helm chart is being actively developed
    enabled: false
    argo:
      # secret keys to provide for the argocd secret plugin app, none by default
      secret_keys:
        webui_hostname: kubevirt.example.com
      # git repo to install the Argo CD app from
      repo: https://github.com/small-hack/argocd-apps
      # path in the argo repo to point to. Trailing slash very important!
      path: kubevirt/
      # either the branch or tag to point at in the argo repo above
      revision: main
      # kubernetes cluster to install the k8s app into, defaults to Argo CD default
      cluster: https://kubernetes.default.svc
      # namespace to install the k8s app in
      namespace: kubevirt
      # recurse directories in the provided git repo
      directory_recursion: false
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        name: kubevirt
        source_repos:
          - https://github.com/small-hack/argocd-apps
          - https://cloudymax.github.io/kubevirt-community-stack/
          - https://github.com/cloudymax/kubevirt-community-stack.git
          - https://cloudymax.github.io/kubevirt-community-stack
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces:
            - kubevirt-manager
            - kube-system
            - kubevirt
            - prometheus
            - default
            - windows10
            - debian12
            - cdi
            - capi-operator-system
            - kubeadm-bootstrap-system
            - kubevirt-infrastructure-system
            - kubeadm-control-plane-system
            - capi-system
```
