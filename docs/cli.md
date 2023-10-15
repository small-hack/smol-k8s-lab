---
layout: default
parent: Intro
title: Using the CLI (command line interface)
description: "smol-k8s-lab cli (command line interface)"
permalink: /cli
---

## Help

```bash
# this will show the help text
smol-k8s-lab --help
```

<details>
  <summary>Help text example</summary>

  <a href="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/screenshots/help_text.svg">
    <img src="https://raw.githubusercontent.com/jessebot/smol-k8s-lab/main/docs/screenshots/help_text.svg" alt="Output of smol-k8s-lab --help after cloning the directory and installing the prerequisites.">
  </a>

</details>

If the help text shows up, you most likely are good to go :) Check out the respectively [CLI] and [TUI] sections to learn more!

### Install a k8s distro

This command will launch the TUI by default, [unless you have it disabled]. If you have the TUI disabled, running this command will run everything via the CLI, unless something in the configuration file is missing or we run into conflicts:

```bash
smol-k8s-lab
```

### Uninstall a distro of k8s

```bash
# --delete can be replaced with -D
smol-k8s-lab --delete $NAME_OF_YOUR_CLUSTER
```
