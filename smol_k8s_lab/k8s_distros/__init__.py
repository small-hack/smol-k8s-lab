from ..k8s_tools.k8s_lib import K8s
from ..utils.rich_cli.console_logging import sub_header, header
from ..utils.subproc import subproc

from .kind import create_kind_cluster, delete_kind_cluster
from .k3d import create_k3d_cluster, delete_k3d_cluster
from .k3s import install_k3s_cluster, uninstall_k3s

from sys import exit


def check_all_contexts() -> list:
    """
    gets current context and if any have smol-k8s-lab returns and dict of 
    {"context": context_name, "cluster": cluster_name, "user": auto_info}

    returns False if there's no clusters with smol-k8s-lab as the context
    """
    contexts = subproc(["kubectl config get-contexts --no-headers"],
                       error_ok=True, quiet=True)

    return_contexts = []

    if contexts:
        # split all contexts outputs into a list of context lines
        for k8s_context in contexts.split('\n'):

            # split each context into fields
            fields = k8s_context.split()

            # HACK: I honestly have no clue why fields is empty sometimes &
            # don't have time to troubleshoot it either 🤦
            if fields:
                # set the cluster name, making sure to not get the * context
                if fields[0] and fields[0] != "*":
                    cluster_name = fields[0]
                else:
                    cluster_name = fields[1]

                # determine the distro of k8s we're using
                for distro_name in "kind", "k3d", "k3s", "gke", "aks", "eks":
                    if distro_name in cluster_name:
                        distro = distro_name
                        break

                context_tuple = (cluster_name, distro)

                return_contexts.append(context_tuple)

    return return_contexts


def check_contexts_for_cluster(cluster_name: str = "smol-k8s-lab",
                               distro: str = "") -> dict:
    """
    gets current context and if any have {cluster_name} and {distro} returns and
    dict of {"context": context_name, "cluster": cluster_name, "user": auto_info}
    returns False if there's no matching clusters as the context
    """
    contexts = subproc(["kubectl config get-contexts --no-headers"],
                       error_ok=True, quiet=True)

    if contexts:
        # split all contexts outputs into a list of context lines
        for k8s_context in contexts.split('\n'):
            # split each context into fields
            fields = k8s_context.split()

            # if clustername is anywhere in the context
            if cluster_name in k8s_context and distro in k8s_context:
                # 5 fields if there's a * denoting the current context
                if len(fields) == 5:
                    return_dict = {"context": fields[1], "cluster": fields[2],
                                   "user": fields[3]}

                # 4 fields if there's no current context ie no cluster is selected
                elif len(fields) == 4:
                    return_dict = {"context": fields[0], "cluster": fields[1],
                                   "user": fields[2]}

                return return_dict
    return {}


def create_k8s_distro(cluster_name: str,
                      k8s_distro: str,
                      distro_metadata: dict = {},
                      metallb_enabled: bool = True,
                      cilium_enabled: bool = False) -> K8s:
    """
    Install a specific distro of k8s

    Arguments:
        cluster_name:     the name to give the cluster in your kubeconfig
        k8s_distro:       options: 'k3s', 'k3d', 'kind'
        distro_metadata:  any extra data objects to be passed to the install funcs
        metallb_enabled:  if we're enabling metallb it requires we disable
                          servicelb for k3s
        cilium_enabled:   if we're enabling cilium it requires we disable flannel
                          for k3s and disable network-policy for all distros

    Returns K8s object with current context selected
    """
    header(f"Initializing your [green]{k8s_distro}[/] cluster", "💙")
    cluster = check_contexts_for_cluster(cluster_name, k8s_distro)
    if cluster:
        sub_header(f'We already have a [green]{k8s_distro}[/] cluster ♡')
        return K8s()

    sub_header('This could take a min ʕ•́ _ •̀ʔっ♡ ', False)

    if k8s_distro == "kind":
        kubelet_args = distro_metadata.get('kubelet_extra_args', None)
        networking_args = distro_metadata['networking_args']

        # if cilium is enabled, we need to disable the default CNI
        if cilium_enabled:
            networking_args["disableDefaultCNI"] = True

        create_kind_cluster(cluster_name,
                            kubelet_args,
                            networking_args,
                            distro_metadata['nodes']['control_plane'],
                            distro_metadata['nodes']['workers'])

    elif k8s_distro == "k3s" or k8s_distro == "k3d":
        # get any extra args the user has passed in
        k3s_args = distro_metadata['k3s_yaml']

        # if metallb is enabled, we need to disable servicelb
        if metallb_enabled:
            if not k3s_args.get('disable', None):
                k3s_args['disable'] = ['servicelb']
            else:
                k3s_args['disable'].append('servicelb')

        # if cilium is enabled, we need to disable flannel and network-policy
        if cilium_enabled:
            k3s_args['flannel-backend'] = 'none'
            k3s_args['disable-network-policy'] = True

        if k8s_distro == "k3s":
            install_k3s_cluster(cluster_name,
                                k3s_args)

        # curently unsupported - in alpha state
        if k8s_distro == "k3d":
            create_k3d_cluster(cluster_name,
                               k3s_args,
                               distro_metadata['nodes']['control_plane'],
                               distro_metadata['nodes']['workers'])

    return K8s()


def delete_cluster(cluster_name: str, k8s_distro: str = "") -> True:
    """
    Delete a k3s, or KinD cluster entirely.
    """
    if 'k3s' in cluster_name or k8s_distro == 'k3s':
        uninstall_k3s(cluster_name)

    if 'k3d' in cluster_name or k8s_distro == 'k3d':
        delete_k3d_cluster(cluster_name)

    elif 'kind' in cluster_name or k8s_distro == 'kind':
        delete_kind_cluster(cluster_name)

    sub_header("[grn]◝(ᵔᵕᵔ)◜ Success![/grn]")

    # exit after deletion
    exit()
