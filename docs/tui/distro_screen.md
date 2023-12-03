The "k8s distro config" screen is the first screen you will see in the TUI when creating a new cluster:

[<img src="/images/screenshots/distro_config_screen.svg" alt="terminal screenshot of smol-k8s-lab k8s distro configuration screen . Features three vertically stacked boxes. Box 1: title: 🌱 Select a k8s distro. Contains a drop down menu on the left hand side that defaults to k3d on macOS and k3s on Linux. On the right hand side there is a description of the distro, which in this case is k3d is a lightweight wrapper to run k3s (Rancher Lab's minimal Kubernetes distro) in Docker containers. Subtitle: Inputs below are optional. Box 2: Title: Adjust how many of each node type to deploy. Contains two input fields: input 1: control plane is set to 1. input 2: workers is set to 0. Box 3: Title: Add extra options for the k3s install script. Contains text: Add extra k3s options to pass to the k3s install script via a config file stored in $XDG_CACHE_HOME/smol-k8s-lab/k3s.yml. Box 3 also contains input fields for: secrets encryption: true, disable: traefik, kubelet arg: max_pods=150, node label: ingress-ready=true. Each input field has a 🚮 button next to it. Box 3 subtitle: ➕ k3s option">](/images/screenshots/distro_config_screen.svg)

## Select Kubernetes Distro

To choose a distro, select one from the drop down [Select](https://textual.textualize.io/widgets/select/#select) in the first box. You can do this either with your mouse, or by hitting enter and then using the arrow keys to select a distro before hitting enter.

## Configuring control plane and worker nodes

If you're using `k3d` or `kind`, you can deploy clusters with more than one node. By default we will always deploy one control plane node, but you can adjust this number as well as how many workers we use.

## Extra options for k3s or k3d

If you're using k3d or k3s, you can adjust what [k3s options](https://docs.k3s.io/cli/server#k3s-server-cli-help) are passed into the [k3s config file](https://docs.k3s.io/installation/configuration#configuration-file). 

## Extra options for kind

If you're using kind, you can modify both the networking and kubelet configuration options.

![terminal screenshot showing smol-k8s-lab k8s distro config screen with kind selected this time. The top two boxes are the same as the last screenshot, but the bottom box shows two tabs: networking, kubelet](/images/screenshots/kind_config_screen.svg)

### Modify existing options

To modify an option, just change the text in any of the input boxes (you can click them, or navigate them with the `tab`/`shift`+`tab` keys).

!!! Note
    If you'd like to pass in multiple values for an option, use a comma separated list, e.g. disable: traefik, servicelb

To delete an option, use click the 🚮 button next to the input field.

### Add new options

To add a new option, you can click the "➕ k3s option" link at the bottom of the box, or you can use the `a` hot key. This will bring up a modal screen with an input field for the new option.

![terminal screenshot showing smol-k8s-lab "add new option" modal screen with a blue border. Header: Add *new* k3s option. The second row has an input field with placeholder text that says "new k3s option" with a button on the right hand side that says "➕ add option". The bottom border has a link that says cancel - which can be clicked or you can use the escape key](/images/screenshots/add_k3s_option_screen.svg)

Enter the name of the new option you'd like to add. 

!!! Note
    If you try to input an option that already exists, it will throw an error and make a bell sound. If you want to add an option that is already there, consider instead adding the extra values as a comma separated list.

!!! Tip
    To turn off bells, visit the [TUI config screen](/tui/tui_config.md)
