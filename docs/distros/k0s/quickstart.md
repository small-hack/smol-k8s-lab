---
layout: default
title: K0s Quickstart
description: "Smol K8s Homelab BASH scripts Quickstart"
parent: K0s
permalink: /distros/k0s/quickstart
---

## Installing a K0s distro using a pre-configured BASH script

Best distro for large multinode/GPU passthrough.

Still being developed, but will probably look something like....

```bash
# this export can also be set in a .env file in the same dir
export EMAIL="youremail@coolemail4dogs.com"

# From the cloned repo dir, This should set up KinD for you
# Will also launch k9s, like top for k8s, To exit k9s, use type :quit
./k8s_homelab/k0s/bash_quickstart.sh
```

#### Ready to clean up this cluster?
To delete the whole cluster, run:

```bash
???
```
