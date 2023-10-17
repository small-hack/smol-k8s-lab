## Help

```bash
# this will show the help text
smol-k8s-lab --help
```

<details>
  <summary>Help text example</summary>

  <a href="/images/screenshots/help_text.svg">
    <img src="/images/screenshots/help_text.svg" alt="Output of smol-k8s-lab --help after cloning the directory and installing the prerequisites.">
  </a>

</details>

## Launching the TUI

```bash
# you can also do smol-k8s-lab -i
smol-k8s-lab --interactive
```

## Install a k8s distro

This command will launch the TUI by default, [unless you have it disabled](http://localhost:8000/tui_config/#disabling-the-tui). If you have the TUI disabled, running this command will run everything via the CLI, unless something in the configuration file is missing or we run into conflicts:

```bash
smol-k8s-lab
```

## Uninstall a distro of k8s

This command assumes `$NAME_OF_YOUR_CLUSTER` is the name of a cluster in your `$KUBECONFIG`.

```bash
# --delete can be replaced with -D
smol-k8s-lab --delete $NAME_OF_YOUR_CLUSTER
```
