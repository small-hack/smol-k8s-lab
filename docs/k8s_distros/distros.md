For each K8s distro below, in addition to being a supported install path with `smol-k8s-lab`, you can also check out a full tutorial to get started from scratch, or use a preconfigured BASH script we've created. We always install the latest version of Kubernetes that is available from the distro's startup script.

|  Distro    |         Description                                   |
|:----------:|:------------------------------------------------------|
| [<img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/icons/k3s_icon.ico" width="26">][k3s] <br /> [k3s] | The certified Kubernetes distribution built for IoT & Edge computing |
| [<img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/icons/kind_icon.png" width="32">][KinD] <br /> [KinD] | kind is a tool for running local Kubernetes clusters using Docker container “nodes”. kind was primarily designed for testing Kubernetes itself, but may be used for local development or CI. |

We tend to test on k3s first, then kind.

<!-- k8s distro link references -->
[k3s]: https://k3s.io/
[KinD]: https://kind.sigs.k8s.io/
