---
layout: default
title: metallb
description: "Troubleshooting MetalLB notes"
grand_parent: Notes
parent: Apps on K8s
permalink: /notes/apps/metallb
---

## Assigning IPs 
Running into issues with metallb assigning IPs, but them some of them not working with nginx-ingress controller? This person explained it really well, but it required hostnetwork to be set on the nginx-ingress chart values.yml. Check out thier guide [here](https://ericsmasal.com/2021/08/nginx-ingress-load-balancer-and-metallb/).

## Why am I getting deprecation notices on certain apps?
If you have the krew deprecations plugin installed, then you might get something like this:
```
Deleted APIs:

PodSecurityPolicy found in policy/v1beta1
	 ├─ API REMOVED FROM THE CURRENT VERSION AND SHOULD BE MIGRATED IMMEDIATELY!!
		-> GLOBAL: metallb-controller
		-> GLOBAL: metallb-speaker
```
For Metallb, that's because of [this issue](https://github.com/metallb/metallb/issues/1401#issuecomment-1140806861). It'll be fixed in October of 2022.
