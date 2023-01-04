---
name: "\U0001F41B Bug report"
about: "Create a report to help us improve published features that are broken. \U0001F494"
title: "\U0001F41B ..."
labels: ":bug: bug"
assignees: ''

---

## Describe the Bug
A clear and concise description of what the bug is.
_Example: argocd is unreachable at the configured fqdn after install._

### Steps to Reproduce Bug
1. run command (please include debug flag): _example_: `smol-k8s-lab k3s -a -e -p -l debug`
2. check resource command: _example_: `kubectl get --namespace argocd pods`

### Output from Above Steps
any output from your above commands

#### Expected behavior
A clear and concise description of what you expected to happen.

### Screenshots
If applicable, add screenshots to help explain your problem.

## User info (please complete the following information):
 - OS release: [e.g. Debian Bookworm]
 - Kubernetes distro: `k0s`, `k3s`, or `kind`
 - Version of `smol-k8s-lab` (You can get this with `smol-k8s-lab --version`): vx.x.x
 - Config file contents (`~/.config/smol-k8s-lab/config.yml`; If you're using XDG Base Directory Spec env variables, this could be under `$XDG_CONFIG_HOME/smol-k8s-lab/`) PLEASE REMOVE SENSITIVE DATA:
   ```yaml
   paste config here
   ```

**If it's related to the install of something on k8s**:
- output of `helm list -a`
- any temp files related to your install under `$HOME/.cache/smol-k8s-lab/` (If you're using XDG Base Directory Spec env variables, this could be under `$XDG_CACHE_HOME/smol-k8s-lab/`)

## Additional context, if any
Add any other context about the problem here.
