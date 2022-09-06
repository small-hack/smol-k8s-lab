---
layout: default
title: Notes
description: "Notes that didn't fit anywhere else"
has_children: true
permalink: /notes
---

# Misc Notes
Here's where I dump various notes on different apps you can host on k8s.


## Helm Installation on Debian
```bash
curl https://baltocdn.com/helm/signing.asc | sudo apt-key add -
sudo apt-get install apt-transport-https --yes
echo "deb https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
sudo apt-get update
sudo apt-get install helm
```

## K3s persistent data
Where is your persistent volume data? If you used the local path provisioner it is here:
`/var/lib/rancher/k3s/storage`
