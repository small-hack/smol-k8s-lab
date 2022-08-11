#!/usr/bin/env python3
# AUTHOR: @jessebot
# EXPERIMENTAL - DO NOT USE IF YOU DON'T KNOW k8s and Python fairly well :)
from argparse import ArgumentParser
from collections import OrderedDict
from lib.homelabHelm import helm
# import yaml


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


def install_defaults_repos(k8s_distro):
    """
    Install all the default repos
    """
    print("Add/update helm repos for metallb, ingress-nginx, cert-manager")

    # metallb is always installed
    repos = OrderedDict()
    repos['metallb'] = 'https://metallb.github.io/metallb'

    # kind has a special install path
    if k8s_distro != 'kind':
        repos['ingress-nginx'] = 'https://kubernetes.github.io/ingress-nginx'

    # this is for cert-manager
    repos['jetstack'] = 'https://charts.jetstack.io'

    # this is for argo to manage everything in the future through a gui
    repos['argo'] = 'https://argoproj.github.io/argo-helm'

    for repo_name, repo_url in repos.items():
        helm_repo = helm.repo(repo_name, repo_url).add()

    helm_repo.update()

    print("all done")


def kind_special_nginx():
    """
    kind has a special install path recommended by the kubernetes project
    """
    print("placeholder")


def install_helm_charts():
    """
    install all the needed helm charts
    """
    charts = OrderedDict()
    charts['metallb'] = {'chart': 'metallb/metallb',
                         'namespace': 'kube-system'}

    for release_name, chart in charts.items():
        if chart['options']:
            helm.chart(release_name, chart['chart'], chart['namespace'],
                       chart['options'])
        else:
            helm.chart(release_name, chart['chart'], chart['namespace'])


def main():
    """
    Quickly install a k8s distro for a homelab setup.
    """
    args = parse_args()
    # with open(args.file, 'r') as yaml_file:
    #     input_variables = yaml.safe_load(yaml_file)

    if args.k8s == 'k3s':
        install_defaults_repos('ingress-nginx')

    print("all done")


if __name__ == '__main__':
    main()
