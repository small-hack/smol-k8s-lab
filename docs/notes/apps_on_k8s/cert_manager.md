---
layout: default
title: cert-manager
description: "cert-manager notes"
grand_parent: Notes
parent: Apps on K8s
permalink: /notes/apps/cert-manager
---

## Cert Manager

After SSL is working (if it's not, follow the steps in the [cert-manager common error troubleshooting guide](https://cert-manager.io/docs/faq/acme/#common-errors)), you can also change the `letsencrypt-staging` value to `letsencrypt-prod` for any domains you own and can configure to point to your cluster via DNS.
