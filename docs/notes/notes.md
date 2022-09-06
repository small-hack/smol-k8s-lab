---
layout: default
title: Notes
description: "Notes that didn't fit anywhere else"
has_children: true
permalink: /notes
---

# Misc Notes
Here's where I dump various notes on different apps you can host on k8s.

### K3s persistent data
Where is your persistent volume data? If you used the local path provisioner it is here:
`/var/lib/rancher/k3s/storage`
