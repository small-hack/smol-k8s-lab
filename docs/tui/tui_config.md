## TUI configuration

You can configure the TUI (Terminal User Interface) either via the config file, or via the TUI itself.

From any screen in the TUI, you can press `c` and it will bring up the TUI.

![terminal screenshot showing the smol-k8s-lab configure tui screen. There is one box with a blue border. The border title is "Configure Terminal UI" and the text at the top of the box says "These parameters are all related to the TUI itself." Below that there's a row of three switches labeled: enabled, footer, and k9s. Below that is an input row with for k9s command with pre-populated text that says applications.argoproj.io](/images/screenshots/tui_config_screen.svg)

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

## FAQ

### Why does the `smol-k8s-lab` look weird in the default macOS terminal?

Please see the official [textual docs](https://textual.textualize.io/FAQ/#why-doesnt-textual-look-good-on-macos) for this, but the gist of it is:

> You can (mostly) fix this by opening settings -> profiles > Text tab, and changing the font settings. We have found that Menlo Regular font, with a character spacing of 1 and line spacing of 0.805 produces reasonable results. If you want to use another font, you may have to tweak the line spacing until you get good results.


### What terminal do you recommend for using the `smol-k8s-lab` TUI?

We use [wezterm](https://wezfurlong.org/wezterm/index.html), because it works on both Linux and macOS. Before we used wezterm, on macOS, we used [iTerm2](https://iterm2.com/). Both are great terminals with a lot of love put into them.
