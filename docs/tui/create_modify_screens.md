This will launch the TUI by default, which will guide you through how to proceed via a series of tooltips:

```bash
smol-k8s-lab
```

!!! Note
    More [accessibility features are on the roadmap](https://textual.textualize.io/roadmap/#features) for [textual](https://textual.textualize.io/) down the line, but please drop us a line if you'd like us to help with anything on our end in the meantime.


## Create a New Cluster

To create a new cluster, fill in the name of your cluster (or use the randomized pre-populated name) and either click the `submit` button, or if there is only one box on the screen, you can hit `enter`. If there are two boxes on the screen, and the input is not selected, you also use the `n` key (for new/next).

That will bring you to the [distro configuration](/distro_screen) screen to begin your configuration journey.

[<img src="../../assets/images/screenshots/start_screen.svg" alt="terminal screenshot of the smol-k8s-lab start screen. The screenshot shows smol-k8s-lab spelled out in block letters followed by one box containing two elements: an input field, pre-populated with a random cluster name, and a submit button for that input field.">](../../assets/images/screenshots/start_screen.svg)


## Modify or Delete a Kubernetes Cluster

The start screen will look like this:

[<img src="../../assets/images/screenshots/start_screen_with_existing_clusters.svg" alt="terminal screenshot of the smol-k8s-lab start screen. The screen shows a smol-k8s-lab banner spelled out in blocky letters followed by two boxes. The first box is for modifying or deleting an existing cluster with an example cluster in a table. The example cluster has the following fields: cluster: k3s-lovely-bunny, distro: k3s, version: v1.29.3+k3s1, platform: linux/amd64. The second box shows an input field for the name of a new cluster, which currently says "adorable-wasbeertje". There is a button next to it to submit the cluster name called New cluster ✨">](../../assets/images/screenshots/start_screen_with_existing_clusters.svg)


The top section will only be present if you already have (a) Kubernetes cluster(s) in your [`$KUBECONFIG`](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/#the-kubeconfig-environment-variable).


### Modify an Existing Cluster

To modify an existing cluster, select your cluster from the list of clusters (stored in a [DataTable](https://textual.textualize.io/widgets/data_table/)) in the top box.

!!! Note
    If you don't see a box with your clusters, the cluster is either not available in your `$KUBECONFIG`, not reachable, or you do not have any at this time.

You can use the `tab` key to scroll down the list of clusters and `shift`+`tab` to scroll up the list and then the `enter` key to select a cluster. You can also use your mouse to click on a cluster. After you select a cluster, you should see this "modal" (AKA pop-up) screen:

[<img src="../../assets/images/screenshots/modify_cluster_modal_screen.svg" alt="terminal screenshot showing smol-k8s-lab after selecting a cluster from the list. This shows the previous screen dimmed in the background with an overlaid modal screen featuring the text 'What would you like to do with k3s-lovely-bunny' and 3 buttons. Button 1: ✏️ Modify Apps, Button 2: 🖥️Modify Nodes, Button 3: Delete. At the bottom of the border for the modal screen, it has a link that says cancel.">](../../assets/images/screenshots/modify_cluster_modal_screen.svg)

To exit this screen, can either:

  - select one of the buttons (modify apps, modify nodes, or delete)
  - click the `cancel` link at the bottom of the modal border
  - press ++b++ or ++esc++


#### Delete an existing Cluster

To delete a cluster, you can either click the `Delete` button, or use your `tab` key to select it and then the `enter` key to press the button. Then, you will get another modal screen asking you to confirm the deletion. If you select the `yes` button, which is the first button, smol-k8s-lab will attempt to delete the cluster if it is one of the following distros: k3s, k3d, or kind.


[<img src="../../assets/images/screenshots/delete_cluster_confirmation.svg" alt="terminal screenshot showing smol-k8s-lab after selecting delete button. Shows a deletion confirmation modal screen that says 'Are you sure?' and it has two buttons: button 1: yes, button 2: cancel">](../../assets/images/screenshots/delete_cluster_confirmation.svg)


#### Modify a Cluster's Apps

To modify a cluster's apps, from the start screen, select your cluster from the list in the first box, and then on the modal screen that appears, select the `modify apps` button. This will then automatically send you to the [apps config screen](/apps_screen) where you can modify or add applications to your cluster.

#### Modify a Cluster's Nodes (k3s only)

For k3s clusters, we support deleting nodes, or adding new nodes. To do this, fromt he start screen, select the cluster you'd like to modify from the list in the first box, and then on the modal screen that appears, select `Modify Nodes`. That will launch this screen:


[<img src="../../assets/images/screenshots/modify_nodes_screen.svg" alt="terminal screenshot showing smol-k8s-lab after selecting modify nodes button on cluster modal screen. The screen shows a title that says smol-k8s-lab - Kubernetes nodes config for k3s-lovely-bunny. Below that is a datatable with nodes. There is one node in the table with the following fields: node: smol-node, status: ready, type: worker, ssh port: 2222, ssh key: id_rsa, labels: reserved=iot, taints: reserved=iot:NoSchedule. Below the table is a header that says 🖥️Add a new node. Below that are a series of fields for a new node. The fields are: host input, node type drop down set to worker by default, ssh port input set to 22 by default, ssh key set to id_rsa by default, node labels input, node taints input. Below that is a footer with key binding hints. The hints are B for back, ctrl+n for add a new node, ? for help, c for config, f for hide footer, f5 for speak, and n for new cluster">](../../assets/images/screenshots/modify_nodes_screen.svg)

There you can select a node by clicking on it or hitting the ++enter++ key. When you do that it will display another modal screen like this:
[<img src="../../assets/images/screenshots/modify_node_modal_screen.svg" alt="terminal screenshot showing smol-k8s-lab after selecting a node. It is a small modal overlayed ontop of the previous screen. The text says: What would you like to do with smol-node? Below that text are three buttons. Buttons from the left: modify, delete, cancel.">](../../assets/images/screenshots/modify_node_modal_screen.svg)

You can select the modify or delete buttons to proceed. If you select delete you'll see this screen:
[<img src="../../assets/images/screenshots/delete_node_confirm_modal_screen.svg" alt="terminal screenshot showing smol-k8s-lab after selecting a node to delete. it is a small modal that says are you sure you want to delete smol-node? and below that it has a yes button and a cancel button.">](../../assets/images/screenshots/delete_node_confirm_modal_screen.svg)

To add a new node, just fill in the fields at the bottom and then hit ++ctrl++ + ++n++.
