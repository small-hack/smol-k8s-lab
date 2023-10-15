---
layout: default
parent: Intro
title: Using the TUI (Terminal User Interface)
description: "smol-k8s-lab TUI (terminal user interface) guide"
permalink: /tui
---

This will launch the TUI by default, which will guide you through how to proceed via a series of tooltips:

```bash
smol-k8s-lab
```

Note: more [accessibility features are on the roadmap](https://textual.textualize.io/roadmap/#features) for [textual](https://textual.textualize.io/) down the line, but please drop us a line if you'd like us to help with anything on our end in the meantime.

## Create, Modify, or Delete a Kubernetes Cluster

The start screen will look like this:

![terminal screenshot of the smol-k8s-lab start screen. The screen shows smol-k8s-lab spelled out in blocky letters followed by two boxes. The first box is for modifying or deleting an existing cluster with an example cluster in a table. The second box shows an input field for the name of a new cluster as well as a button next to it to submit the cluster name](./images/screenshots/start_screen_with_existing_clusters.svg)

The top section will only be present if you already have (a) Kubernetes cluster(s) in your [`$KUBECONFIG`]. If you do not have any existing clusters, you will see this instead:

![terminal screenshot of the smol-k8s-lab start screen. The screenshot shows smol-k8s-lab spelled out in block letters followed by one box containing two elements: an input field, pre-populated with a random cluster name, and a submit button for that input field.](./images/screenshots/start_screen.svg)

### Create a New Cluster

To create a new cluster, fill in the name of your cluster (or use the randomized pre-populated name) and either click the `submit` button, or if there is only one box on the screen, you can hit `enter`. If there are two boxes on the screen, and the input is not selected, you also use the `n` key (for new/next).

That will bring you to the [distro configuration]() screen to begin your configuration journey.


### Modify or Delete an Existing Cluster

To modify an existing cluster, select your cluster from the list of clusters (stored in a [DataTable]) in the top box. 

Note: If you don't see a box with your clusters, the cluster is either not available in your `$KUBECONFIG` or you do not have any at this time.

You can use the `tab` key to scroll down the list of clusters and `shift`+`tab` to scroll up the list and then the `enter` key to select a cluster. You can also use your mouse to click on a cluster. After you select a cluster, you should see this "modal" (AKA pop-up) screen:

![terminal screenshot showing smol-k8s-lab after selecting a cluster from the list. This shows the previous screen dimmed in the background with an overlaid "modal" screen featuring the text "How would you like to proceed with $CLUSTER_NAME" and 3 buttons. Button 1: Modify, Button 2: Delete, Button 3: Cancel](./screenshots)

#### Delete a Cluster

To delete a cluster, you can either click the `Delete` button, or use your `tab` key to select it and then the `enter` key to press the button. Then, you will get another modal screen asking you to confirm the deletion. If you select the `yes` button, which is the first button, smol-k8s-lab will attempt to delete the cluster if it is one of the following distros: k3s, k3d, or kind.

![terminal screenshot showing smol-k8s-lab after selecting `delete` button. Shows a deletion confirmation modal screen that says "Are you sure?" and it has two buttons: button 1: `yes` and button 2: `cancel`](./screenshots)

#### Modify a Cluster

To modify a cluster, from the start screen, select your cluster from the list in the first box, and then on the modal screen that appears, select the `modify` button. This will then automatically send you to the [apps config screen](/apps) where you can modify or add applications to your cluster.


## Disabling the TUI

There are two ways to disable the TUI, but both accomplish the same thing: modifying the `$XDG_CONFIG_HOME/smol-k8s-lab/config.yaml`.

### Disable TUI via TUI

