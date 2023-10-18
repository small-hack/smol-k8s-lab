## Using the TUI

`smol-k8s-lab` uses the [textual](https://www.textualize.io/) framework to create an interactive graphical interface in the terminal. To get tips on how to navigate the TUI you can press `?` from within the TUI to get a help screen that looks like this:

![terminal screenshot of the tui help screen](./images/screenshots)

Some helpful tips:

| key binding   | description |
|:-------------:|:------------|
| ++'?'++       | display the help screen | 
| ++c++         | display the TUI config screen | 
| ++f++         | show or hide the footer with key hints |
| ++n++         | on the start screen, n will create a "new" cluster. All other screens this is "next" screen |
| ++b++ / ++escape++ / ++q++ | Back a screen. If on the start screen, these quit the application |
| ++tab++ / ++shift+tab++ | change focus to different elements on the page |


## TUI configuration

You can configure the TUI (Terminal User Interface) either via the config file, or via the TUI itself.

From any screen in the TUI, you can press `c` and it will bring up the TUI.

![terminal screenshot showing the smol-k8s-lab configure tui screen. There is one box with a blue border. The border title is "Configure Terminal UI" and the text at the top of the box says "These parameters are all related to the TUI itself." Below that there's a row of three switches labeled: enabled, footer, and k9s. Below that is an input row with for k9s command with pre-populated text that says applications.argoproj.io](./images/screenshots/tui_config_screen.svg)

Some options may not take effect till you return to the start screen or restart the program.

To exit the TUI config, just press `q` or `escape`.

### Disabling the TUI

There are two ways to disable the TUI, but both accomplish the same thing: modifying the `$XDG_CONFIG_HOME/smol-k8s-lab/config.yaml`.

#### Disable TUI via TUI

Launch the TUI with `smol-k8s-lab` and then press `c`. Click the switch next to the word "enabled", and this will disable the TUI from launching automatically. You can still launch the tui with `smol-k8s-lab -i` or `smol-k8s-lab --interactive`. Once disabled by default, you can only re-enable it by default from the config file.

#### Disable TUI via the config file

In `$XDG_CONFIG_HOME/smol-k8s-lab/config.yaml`, set `smol_k8s_lab.tui.enabled` to `false` like this:

```yaml
smol_k8s_lab:
  tui:
    enabled: false
```

To re-enable the tui, set `smol_k8s_lab.tui.enabled` to `true`
