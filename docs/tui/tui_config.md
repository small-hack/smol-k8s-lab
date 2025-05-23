## TUI and Accessibility configuration

You can configure the TUI (Terminal User Interface), including accessibility features, either via the config file, or via the TUI itself.

From any screen in the TUI, you can press ++c++ and it will bring up the Accessibility and TUI config screen.

![terminal screenshot showing the smol-k8s-lab configure accessibility options and tui config screen. There are two boxes. Box one: Configure accessibility features. The first header in the box says Terminal Bell config and features a section with two switches: bell on focus, and bell on error. The second header in the first box says Text to speech Config. Below are three rows. The first row has a input field for speech program with placeholder text that says name of program for speech. The 2nd row has two switches. Switch one is on key press, and the switch two is on focus. The final row in the 1st box has two switches. Switch one is screen titles, and switch two is screen descriptions. The second box on this screen is titled configure terminal UI and it features two switches. Box two's first switch is TUI enabled, and the second switch is footer enabaled.](../../assets/images/screenshots/tui_config_screen.svg)

Some options may not take effect until you return to the start screen or restart the program.

To exit the TUI config screen, just press ++q++ or ++esc++.

To checkout more information on configuring accessibility options via the config file, check out our examples [here](/config_file/#tui-and-accessibility-configuration).

### Disabling the TUI

There are two ways to disable the TUI, but both accomplish the same thing: modifying the `$XDG_CONFIG_HOME/smol-k8s-lab/config.yaml`.

Here's a short video showing how to do this. I don't know how to add subtitles, but the voice says "Welcome to smol-k8s-lab. Press ++tab++, then ++c++, to configure accessibility options." If you have an existing cluster, you can just just press ++c++ without needing to press tab first.

![type:video](../../assets/videos/how_to_disable_text_to_speech.mov)

#### Disable TUI via TUI

Launch the TUI with `smol-k8s-lab` and then press ++c++. Click the switch next to the word "enabled", and this will disable the TUI from launching automatically. You can still launch the tui with `smol-k8s-lab -i` or `smol-k8s-lab --interactive`. Once disabled by default, you can only re-enable it by default from the config file.

#### Disable TUI via the config file

In `$XDG_CONFIG_HOME/smol-k8s-lab/config.yaml`, set `smol_k8s_lab.tui.enabled` to `false` like this:

```yaml
smol_k8s_lab:
  tui:
    enabled: false
```

To re-enable the tui, set `smol_k8s_lab.tui.enabled` to `true`


## Logging, Password Management, and Run Command

There's a special screen that pops up just before the [confirmation screen](/tui/confirmation_screen/#confirming-your-configuration) where we ask for a few last minute run-specific options.

![terminal screenshot showing the smol-k8s-lab configure logging, password management, and run command config screen. The screen features three main boxes. Box one title is configure logging. It says configure logging for all of smol-k8s-lab. Below the text it has a level dropdown set to debug and a file input with no value. The seond box title is configure password manager. The text reads Save app credentials to a local password manager vault. Only Bitwarden is supported at this time, but if enabled, Bitwarden can be used as your k8s external secret provider. To avoid a password prompt, export the following env vars: BW_PASSWORD, BW_CLIENTID, BW_CLIENTSECRET. Below that is a row with an enabled switch and a duplicate strategy drop down menu set to edit. The final box on the screen is titled configure command to run after config. The text reads If window behavior is set to same window, command runs after smol-k8s-lab has completed. The first row in the box features a teminal dropdown set wezterm, and a window behavior drop down menu set to split right. The final row in the box is a command input field and it is set to k9s --command applications.argoproj.io](../../assets/images/screenshots/logging_password_config.svg)

## FAQ

### I'm getting Alsa errors whenever I launch the TUI over SSH or on a machine without audio drivers.

This is because we use your terminal bell or we're trying to use text to speech. You can disable text to speech and bell by hitting ++C++ anywhere in the TUI and then switching all the switches under Accessibility to the off position. Alternatively, you can disable all of this in the `$XDG_CONFIG_HOME/smol-k8s-lab/config.yaml` (If you don't have the `$XDG_CONFIG_HOME` env var configured, we will default to `~/.config/smol-k8s-lab/config.yaml`). See the [TUI and Accessibility config file docs](/config_file/#tui-and-accessibility-configuration) for more info on how to do this via the config file.

### Why does the `smol-k8s-lab` look weird in the default macOS terminal?

Please see the official [textual docs](https://textual.textualize.io/FAQ/#why-doesnt-textual-look-good-on-macos) for this, but the gist of it is:

> You can (mostly) fix this by opening settings -> profiles > Text tab, and changing the font settings. We have found that Menlo Regular font, with a character spacing of 1 and line spacing of 0.805 produces reasonable results. If you want to use another font, you may have to tweak the line spacing until you get good results.


### What terminal do you recommend for using the `smol-k8s-lab` TUI?

We use [wezterm](https://wezfurlong.org/wezterm/index.html), because it works on both Linux and macOS. Before we used wezterm, on macOS, we used [iTerm2](https://iterm2.com/). Both are great terminals with a lot of love put into them.
