## Confirming your configuration

After you've taken a look through all the configuration screens, you'll be blessed by this final overview screen that lets you check out each section of the config file without the TUI:

![<img src="../../assets/images/screenshots/confirm_screen.svg" alt="terminal screenshot of the smol-k8s-lab confirmation screen. At the top it says smol k8s lab - Review your configuration (last step!) and then there is one main large box titled Review All Values that contains 4 tabs: Core config, K8s Distro Config, Apps Config, and Global Parameters Config. Under each tab is that section of the smol-k8s-lab config file with syntax highlighting. Below the main box on the screen are two buttons: 🚆 Let's roll!, ✋Go Back.">](../../assets/images/screenshots/confirm_screen.svg)

## Bitwarden screen

If you haven't exported your Bitwarden credentials as env vars (`BW_PASSWORD`, `BW_CLIENTID`, and `BW_CLIENTSECRET`), then after you hit the "Let's Go" button, you'll see this screen:

![<img src="../../assets/images/screenshots/bitwarden_prompt.svg" alt="terminal screenshot of the smol-k8s-lab confirmation screen. At the top it says smol k8s lab - Review your configuration (last step!). Below that is a large modal for filling out your bitwarden credentials. Behind that modal is the confirmation screen which is detailed above in the alt text for the first image on this page">](../../assets/images/screenshots/bitwarden_credentials_screen.svg)
