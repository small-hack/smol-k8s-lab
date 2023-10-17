[K3s](https://k3s.io/) is packaged as a single <70MB binary that reduces the dependencies and steps needed to install, run and auto-update a production Kubernetes cluster. Optimized for ARM Both ARM64 and ARMv7 are supported with binaries and multiarch images available for both. If you just want to get quickly started with it, you can do:

```bash
curl -sfL https://get.k3s.io | sh -

# Check for Ready node, takes maybe 30 seconds
k3s kubectl get node
```

## Troubleshooting
### Default directory for Persistent Volumes
Where is your persistent volume data? If you used the local path provisioner it is here:
`/var/lib/rancher/k3s/storage`
