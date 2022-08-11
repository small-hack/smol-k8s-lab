#!/usr/bin/env python3
# AUTHOR: @jessebot
# EXPERIMENTAL - DO NOT USE IF YOU DON'T KNOW k8s and Python fairly well :)
from argparse import ArgumentParser
from collections import OrderedDict
# https://github.com/kubernetes-client/python
from kubernetes import client, config
from lib.homelabHelm import helm
from lib.util import sub_proc, simple_loading_bar, header
import yaml


def parse_args():
    """
    Parse arguments and return dict
    """
    n_help = 'Do NOT run k9s as soon as this script is complete'
    f_help = 'Full path and name of yml to parse, e.g. -f /tmp/config.yml'
    k_help = 'distribution of kubernetes to install: k3s, k0s, KinD'
    p = ArgumentParser(description=main.__doc__)

    p.add_argument('-k', '--k8s', required=True, help=k_help)
    p.add_argument('--no-k9s', action='store_false', default=True, help=n_help)
    p.add_argument('-f', '--file', default='config.yml', type=str, help=f_help)
    return p.parse_args()


def add_default_repos(k8s_distro):
    """
    Add all the default helm chart repos
    # metallb is for loadbalancing and assigning ips, on metal...
    # ingress-nginx allows us to do ingress, so access outside the cluster
    # jetstack is for cert-manager for ssl certs
    # argo is argoCD to manage k8s resources in the future through a gui
    """
    repos = OrderedDict()

    repos['metallb'] = 'https://metallb.github.io/metallb'
    repos['ingress-nginx'] = 'https://kubernetes.github.io/ingress-nginx'
    repos['jetstack'] = 'https://charts.jetstack.io'
    repos['argo'] = 'https://argoproj.github.io/argo-helm'

    # kind has a special install path
    if k8s_distro == 'kind':
        repos.pop('ingress-nginx')

    for repo_name, repo_url in repos.items():
        helm_repo = helm.repo(repo_name, repo_url).add()

    # update any repos that are out of date
    helm_repo.repo.update()


def configure_metallb(api, address_pool):
    """
    metallb is special because it has Custom Resources
    """
    # install chart and wait
    chart = helm.chart('metallb', 'metallb/metallb', namespace='kubesystem')
    chart.install(True)

    ip_pool_cr = {
        'apiversion': 'metallb.io/v1beta1',
        'kind': 'IPAddressPool',
        'metadata': {'name': 'base-pool'},
        'spec': {'addresses': [address_pool]}
    }

    l2_advert_cr = {
        'apiversion': 'metallb.io/v1beta1',
        'kind': 'L2Advertisement',
        'metadata': {'name': 'base-pool'}
    }

    for custom_resource in [ip_pool_cr, l2_advert_cr]:
        install_custom_resource(custom_resource)


def configure_cert_manager(api, email_addr):
    """
    installs cert-manager helm chart and letsencrypt-staging clusterissuer
    """
    # install chart and wait
    chart = helm.chart('cert-manager', 'jetstack/cert-manager',
                       namespace='kube-system',
                       options={'installCRDs': 'true'})
    chart.install(True)

    acme_staging = 'https://acme-staging-v02.api.letsencrypt.org/directory'
    issuer = {'apiversion': 'cert-manager.io/v1',
              'kind': 'ClusterIssuer',
              'metadata': {'name': 'letsencrypt-staging'},
              'spec': {
                  'acme': {'email': email_addr,
                           'server': acme_staging,
                           'privateKeySecretRef': {
                               'name': 'letsencrypt-staging'},
                           'solvers': [
                               {'http01': {'ingress': {'class': 'nginx'}}}]
                           }}}

    install_custom_resource(api, issuer)


def install_custom_resource(api, custom_resource_dict):
    """
    Does a kube apply on a custom resource dict, and retries if it fails
    """
    # loops until this succeeds
    while True:
        try:
            api.create_namespaced_custom_object(
                version='v1',
                namespace='kube-system',
                plural=f"{custom_resource_dict['kind'].lower()}s",
                body=custom_resource_dict)

        except Exception as reason:
            print(f"Hmmm, that didn't work because: {reason}")
            simple_loading_bar(3)
            continue


def install_k8s_distro(k8s_distro):
    """
    install a specific distro of k8s
    options: k3s, kind | coming soon: k0s
    """
    sub_proc(f"./{k8s_distro}/quickstart.sh")


def main():
    """
    Quickly install a k8s distro for a homelab setup.
    installs k3s with metallb, nginx-ingess-controller, cert-manager, and argo
    """
    args = parse_args()
    with open(args.file, 'r') as yaml_file:
        input_variables = yaml.safe_load(yaml_file)

    header(f"Installing {args.k8s}")
    install_k8s_distro(args.k8s)

    header("Adding/Updating help repos")
    add_default_repos(args.k8s)

    # set up the k8s python client. Uses default configured $KUBECONFIG
    config.load_kube_config()
    api = client.CustomObjectsApi()

    # KinD has ingress-nginx install in install_k8s_distro()
    if args.k8s != 'kind':
        header("Configuring metallb so we have an ip address pool")
        configure_metallb(api, input_variables['address_pool'])

        # We wait on all the pods to be up on this so other apps can install
        nginx_chart_opts = {'hostNetwork': 'true', 'hostPort.enabled': 'true'}
        chart = helm.chart('nginx-ingress', 'ingress-nginx/ingress-nginx',
                           namespace='kubesystem', options=nginx_chart_opts)
        chart.install(True)

    configure_cert_manager(api, input_variables['email'])

    # then install argo CD :D
    chart = helm.chart('argo', 'argo/argo', namespace='cicd')
    chart.install(True)

    print("all done")


if __name__ == '__main__':
    main()
