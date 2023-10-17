## Toolbox

Notes on tools for interacting with k8s.

### Install kubectl plugins with krew
[Krew](https://krew.sigs.k8s.io/) is a plugin manager for `kubectl` plugins. You can install it with `brew` and update plugins with `kubectl krew update`

These together make namespace switching better. [Learn more about kubectx + kubens](https://github.com/ahmetb/kubectx).

```bash
kubectl krew install ctx
kubectl krew install ns
```

This will help with generating example k8s resources:

```bash
kubectl krew install example
```

This one helps find deprecated stuff in your cluster:

```bash
kubectl krew install deprecations
```

To install plugins from a krew file, you just need a file with one plugin per line. You can use [this one](https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/deps/kubectl_krew_plugins):

```bash
curl -O https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/deps/kubectl_krew_plugins

kubectl krew install < kubectl_krew_plugins
```

### k8s shell aliases

Add some [helpful k8s aliases](https://github.com/jessebot/dot_files/blob/main/.bashrc_k8s):

```bash
# copy the file
curl -O https://raw.githubusercontent.com/jessebot/dot_files/main/.bashrc_k8s

# load the file for your current shell
source ~/.bashrc_k8s
```

To have the above file sourced every new shell, copy this into your `.bashrc` or `.bash_profile`:

```bash
# include external .bashrc_k8s if it exists
if [ -f "$HOME/.bashrc_k8s" ]; then
    . $HOME/.bashrc_k8s
fi
```
