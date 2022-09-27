#!/usr/bin/env python3.10
"""
AUTHOR: @jessebot email: jessebot(AT)linux(d0t)com
Works with k3s and KinD
"""
import bcrypt
from collections import OrderedDict
from lib.homelabHelm import helm
from lib.util import sub_proc, simple_loading_bar, header
from lib.bw_cli import BwCLI
from os import path
from sys import exit
import yaml


PWD = path.dirname(__file__)


def add_default_repos(k8s_distro, argo=True):
    """
    Add all the default helm chart repos:
    - metallb is for loadbalancing and assigning ips, on metal...
    - ingress-nginx allows us to do ingress, so access outside the cluster
    - jetstack is for cert-manager for TLS certs
    - sealed-secrets - for encrypting k8s secrets files for checking into git
    - argo is argoCD to manage k8s resources in the future through a gui
    """
    repos = OrderedDict()

    repos['metallb'] = 'https://metallb.github.io/metallb'
    repos['ingress-nginx'] = 'https://kubernetes.github.io/ingress-nginx'
    repos['jetstack'] = 'https://charts.jetstack.io'
    repos['sealed-secrets'] = 'https://bitnami-labs.github.io/sealed-secrets'
    repos['external-secrets'] = 'https://charts.external-secrets.io'
    if argo:
        repos['argo-cd'] = 'https://argoproj.github.io/argo-helm'

    # kind has a special install path
    if k8s_distro == 'kind':
        repos.pop('ingress-nginx')

    for repo_name, repo_url in repos.items():
        helm.repo(repo_name, repo_url).add()

    # update any repos that are out of date
    helm.repo.update()


def install_k8s_distro(k8s_distro=""):
    """
    install a specific distro of k8s
    options: k3s, kind | coming soon: k0s
    """
    sub_proc(f"{PWD}/distros/{k8s_distro}/quickstart.sh")


def install_custom_resource(custom_resource_dict):
    """
    Does a kube apply on a custom resource dict, and retries if it fails
    """
    # Write a YAML representation of data to 'k8s_cr.yaml'.
    with open('/tmp/k8s_cr.yml', 'w') as cr_file:
        yaml.dump(custom_resource_dict, cr_file)

    # loops with progress bar until this succeeds
    command = 'kubectl apply -f /tmp/k8s_cr.yml'
    simple_loading_bar(3, command)


def configure_metallb(address_pool):
    """
    metallb is special because it has Custom Resources
    """
    # install chart and wait
    release = helm.chart(chart_name='metallb/metallb',
                         release_name='metallb',
                         namespace='kube-system')
    release.install(True)

    ip_pool_cr = {
        'apiVersion': 'metallb.io/v1beta1',
        'kind': 'IPAddressPool',
        'metadata': {'name': 'base-pool',
                     'namespace': 'kube-system'},
        'spec': {'addresses': [address_pool]}
    }
    print(ip_pool_cr)

    l2_advert_cr = {
        'apiVersion': 'metallb.io/v1beta1',
        'kind': 'L2Advertisement',
        'metadata': {'name': 'base-pool',
                     'namespace': 'kube-system'}
    }

    for custom_resource in [ip_pool_cr, l2_advert_cr]:
        install_custom_resource(custom_resource)


def configure_cert_manager(email_addr):
    """
    installs cert-manager helm chart and letsencrypt-staging clusterissuer
    """
    # install chart and wait
    release = helm.chart(release_name='cert-manager',
                         chart_name='jetstack/cert-manager',
                         namespace='kube-system',
                         set_options={'installCRDs': 'true'})
    release.install(True)

    acme_staging = 'https://acme-staging-v02.api.letsencrypt.org/directory'
    issuer = {'apiVersion': 'cert-manager.io/v1',
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

    install_custom_resource(issuer)


def configure_external_secrets(external_secrets_config):
    """
    configure external secrets and provider. currently only works with gitlab
    Accepts dict as arg:
    dict = {'namespace': 'somenamespace', 'access_token': 'tokenhere'}
    """
    header("Installing External Secrets Operator...")
    release = helm.chart(release_name='external-secrets-operator',
                         chart_name='external-secrets/external-secrets',
                         namespace='external-secrets')
    release.install(True)

    gitlab_access_token = external_secrets_config['access_token']
    gitlab_namespace = external_secrets_config['namespace']

    # create the namespace if does not exist
    sub_proc(f'kubectl create namespace {gitlab_namespace}', True)

    # this currently only works with gitlab
    gitlab_secret = {'apiVersion': 'v1',
                     'kind': 'Secret',
                     'metadata': {'name': 'gitlab-secret',
                                  'namespace': gitlab_namespace,
                                  'labels': {'type': 'gitlab'}},
                     'type': 'Opaque',
                     'stringData': {'token': gitlab_access_token}}

    install_custom_resource(gitlab_secret)


def delete_cluster(k8s_distro="k3s"):
    """
    Delete a KIND or K3s cluster entirely.
    """
    header(f"ヾ(^_^) byebye {k8s_distro}!!")

    if k8s_distro == 'k3s':
        sub_proc('k3s-uninstall.sh')
    elif k8s_distro == 'kind':
        sub_proc('kind delete cluster')
    elif k8s_distro == 'k0s':
        header("┌（・Σ・）┘≡З  Whoops. k0s not YET supported.")


def main():
    """
    Quickly install a k8s distro for a homelab setup. Installs k3s
    with metallb, nginx-ingess-controller, cert-manager, and argocd
    """
    args = parse_args()

    # make sure we got a valid k8s distro
    if args.k8s not in ['k3s', 'kind']:
        print(f'Sorry, {args.k8s} is not a currently supported k8s distro :( '
              'Please try again with either -k k3s or -k kind')
        exit()

    if args.delete:
        delete_cluster(args.k8s)
    else:
        with open(args.file, 'r') as yaml_file:
            input_variables = yaml.safe_load(yaml_file)

        # install the actual KIND or k3s cluster
        if args.k8s == 'kind':
            header('Installing KinD cluster. ' +
                   'This could take 2-3 minutes ʕ•́ᴥ•̀ʔっ♡')
        else:
            header(f"Installing {args.k8s} cluster.")
        install_k8s_distro(args.k8s)

        # this is where we add all the helm repos we're going to use
        header("Adding/Updating helm repos...")
        add_default_repos(args.k8s, args.argo)

        # needed for metal installs
        header("Configuring metallb so we have an ip address pool")
        configure_metallb(input_variables['address_pool'])

        # KinD has ingress-nginx install
        if args.k8s == 'kind':
            url = 'https://raw.githubusercontent.com/kubernetes/' + \
                  'ingress-nginx/main/deploy/static/provider/kind/deploy.yaml'
            sub_proc(f'kubectl apply -f {url}')

            # this is to wait for the deployment to come up
            sub_proc('kubectl rollout status '
                     'deployment/ingress-nginx-controller -n ingress-nginx')
            sub_proc('kubectl wait --for=condition=ready pod '
                     '--selector=app.kubernetes.io/component=controller '
                     '--timeout=90s -n ingress-nginx')
        else:
            # you need this to access webpages from outside the cluster
            header("Installing nginx-ingress-controller...")
            nginx_chart_opts = {'hostNetwork': 'true',
                                'hostPort.enabled': 'true'}
            release = helm.chart(release_name='nginx-ingress',
                                 chart_name='ingress-nginx/ingress-nginx',
                                 namespace='kube-system',
                                 set_options=nginx_chart_opts)
            release.install()

        # this is for manager SSL/TLS certificates via lets-encrypt
        header("Installing cert-manager for TLS certificates...")
        configure_cert_manager(input_variables['email'])

        # this allows you to check your secret files into git
        if args.sealed_secrets:
            header("Installing Bitnami sealed-secrets...")
            release = helm.chart(release_name='sealed-secrets',
                                 chart_name='sealed-secrets/sealed-secrets',
                                 namespace='sealed-secrets',
                                 set_options={'namespace': "sealed-secrets"})
            release.install()
            print("Installing kubeseal with brew...")
            # TODO: check if installed before running this
            sub_proc("brew install kubeseal", True)

        # this is for external secrets, currently only supports gitlab
        if args.external_secret_operator:
            external_secrets = input_variables['external_secrets']['gitlab']
            configure_external_secrets(external_secrets)

        # then install argo CD :D
        if args.argo:
            argo_cd_domain = input_variables['domains']['argo_cd']
            opts = {'dex.enabled': 'false',
                    'server.ingress.enabled': 'true',
                    'server.ingress.ingressClassName': 'nginx',
                    'server.ingress.hosts[0]': argo_cd_domain,
                    'server.extraArgs[0]': '--insecure'}

            # if we're using a password manager, generate a password & save it
            if args.password_manager:
                # if we're using bitwarden...
                bw = BwCLI()
                bw.unlock()
                argo_password = bw.generate()
                bw.create_login(name=argo_cd_domain,
                                item_url=argo_cd_domain,
                                user="admin",
                                password=argo_password)
                bw.lock()
                admin_pass = bcrypt.hashpw(argo_password.encode('utf-8'),
                                           bcrypt.gensalt()).decode()

                # this gets passed to the helm cli, but is bcrypted
                opts['configs.secret.argocdServerAdminPassword'] = admin_pass

            release = helm.chart(release_name='argo-cd',
                                 chart_name='argo/argo-cd',
                                 namespace='argocd',
                                 set_options=opts)
            release.install(True)

    print("Smol K8s Homelab Script complete :)")


if __name__ == '__main__':
    main()
