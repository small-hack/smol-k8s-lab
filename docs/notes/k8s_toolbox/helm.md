---
layout: default
title: Helm
description: "Notes on helm, a package manager for k8s"
grand_parent: Notes
parent: Toolbox
permalink: /notes/toolbox/helm
---

# Helm
Helm is a popular package manager for k8s and is generally the default standard, alongside kustomize.

## Installation on Debian

```bash
curl https://baltocdn.com/helm/signing.asc | sudo apt-key add -
sudo apt-get install apt-transport-https --yes
echo "deb https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
sudo apt-get update
sudo apt-get install helm
```

## Troubleshooting

### Helm3 template errors
- [no template `x` associated with template "gotpl"](https://stackoverflow.com/questions/70899601/helm3-template-error-calling-include-template-no-template-microservice-labels)
