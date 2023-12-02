#!/usr/bin/env python
# shamelessly stolen from:
# https://blog.davep.org/2023/07/03/making-my-github-banner.html

from smol_k8s_lab.tui.base import BaseApp
import asyncio


async def make_base_screenshots() -> None:
    """
    make all the screenshots for the start screen, help screen, and config screen
    """
    async with BaseApp().run_test(size=(87, 47)) as pilot:
        pilot.app.save_screenshot("./docs/images/screenshots/start_screen.svg")

        # press the "tab" key followed by the "c" key
        await pilot.press("tab", "c")
        pilot.app.save_screenshot("./docs/images/screenshots/tui_config_screen.svg")

        # press the "q" key and "h" key for the help screen
        await pilot.press("q", "h")
        pilot.app.save_screenshot("./docs/images/screenshots/tui_help_screen.svg")


async def make_distro_screen_screenshots() -> None:
    """
    make all the screenshots
    """
    async with BaseApp().run_test(size=(90, 55)) as pilot:
        # press the "enter" key and then f key to go to the distro screen and then hide the footer
        await pilot.press("enter", "f")
        pilot.app.save_screenshot("./docs/images/screenshots/distro_config_screen.svg")

        # Test selecting another distro from the drop down
        await pilot.press("enter", "down", "enter")
        pilot.app.save_screenshot("./docs/images/screenshots/kind_config_screen.svg")

        # press the "a" key to add a new app
        await pilot.press("a")
        pilot.app.save_screenshot("./docs/images/screenshots/add_k3s_option_screen.svg")
        await pilot.press("escape")

        # Test selecting another distro from the drop down
        await pilot.press("tab", "tab", "tab", "right")
        pilot.app.save_screenshot("./docs/images/screenshots/kind_config_screen2.svg")


async def make_apps_screen_screenshots() -> None:
    """
    make all the screenshots
    """
    async with BaseApp().run_test(size=(87, 47)) as pilot:
        # press the "enter" key and then the "n" key
        await pilot.press("enter", "n")
        pilot.app.save_screenshot("./docs/images/screenshots/apps_screen.svg")

        # press the "a" key to add a new app
        await pilot.press("a")
        pilot.app.save_screenshot("./docs/images/screenshots/new_app_modal_screen.svg")

        # press tab, tab, enter to get to the modify_global_parameters button
        await pilot.press("escape","tab","tab","enter")
        pilot.app.save_screenshot("./docs/images/screenshots/modify_global_parameters_modal_screen.svg")

async def make_confirmation_screen_screenshots() -> None:
    """
    make all the screenshots
    """
    async with BaseApp().run_test(size=(87, 47)) as pilot:
        # logging and password config
        await pilot.press("enter", "n", "n")
        pilot.app.save_screenshot("./docs/images/screenshots/logging_password_config.svg")

        # confirmation screen finally
        await pilot.press("n")
        pilot.app.save_screenshot("./docs/images/screenshots/confirm_screen.svg")

if __name__ == "__main__":
    asyncio.run(make_base_screenshots())
    asyncio.run(make_distro_screen_screenshots())
    asyncio.run(make_apps_screen_screenshots())
