#!/usr/bin/env python
# thank you to davep for helping me learn this:
# https://blog.davep.org/2023/07/03/making-my-github-banner.html

from smol_k8s_lab.tui.base import BaseApp
import asyncio


screenshot_path = "./docs/assets/images/screenshots"


async def make_base_screenshots() -> None:
    """
    make all the screenshots for the start screen, help screen, and config screen
    """
    async with BaseApp().run_test(size=(87, 47)) as pilot:
        pilot.app.save_screenshot(f"{screenshot_path}/start_screen.svg")

        # press the "tab" key followed by the "c" key
        await pilot.press("tab", "c")
        pilot.app.save_screenshot(f"{screenshot_path}/tui_config_screen.svg")

        # press the "q" key and "h" key for the help screen
        await pilot.press("q", "h")
        pilot.app.save_screenshot(f"{screenshot_path}/tui_help_screen.svg")


async def make_distro_screen_screenshots() -> None:
    """
    make all the screenshots
    """
    async with BaseApp().run_test(size=(90, 55)) as pilot:
        # press the "enter" key and then f key to go to the distro screen and then hide the footer
        await pilot.press("enter", "f")
        pilot.app.save_screenshot(f"{screenshot_path}/distro_config_screen.svg")

        # Test selecting another distro from the drop down
        await pilot.press("enter", "down", "enter")
        pilot.app.save_screenshot(f"{screenshot_path}/kind_config_screen.svg")

        # press the "a" key to add a new app
        await pilot.press("a")
        pilot.app.save_screenshot(f"{screenshot_path}/add_k3s_option_screen.svg")
        await pilot.press("escape")

        # Test selecting another distro from the drop down
        await pilot.press("tab", "tab", "tab", "right")
        pilot.app.save_screenshot(f"{screenshot_path}/kind_config_screen2.svg")


async def make_apps_screen_screenshots() -> None:
    """
    make all the screenshots
    """
    async with BaseApp().run_test(size=(90, 55)) as pilot:
        # press the "enter" key and then the "n" key
        await pilot.press("enter", "n")
        pilot.app.save_screenshot(f"{screenshot_path}/apps_screen.svg")

        # press the "a" key to add a new app
        await pilot.press("a")
        pilot.app.save_screenshot(f"{screenshot_path}/new_app_modal_screen.svg")

        # press tab, tab, enter to get to the modify_global_parameters button
        await pilot.press("escape","tab","tab","enter")
        pilot.app.save_screenshot(f"{screenshot_path}/modify_global_parameters_modal_screen.svg")

async def make_confirmation_screen_screenshots() -> None:
    """
    make all the screenshots
    """
    async with BaseApp().run_test(size=(87, 47)) as pilot:
        # logging and password config
        await pilot.press("enter", "n", "n")
        pilot.app.save_screenshot(f"{screenshot_path}/logging_password_config.svg")

        # confirmation screen finally
        await pilot.press("n")
        pilot.app.save_screenshot(f"{screenshot_path}/confirm_screen.svg")

if __name__ == "__main__":
    asyncio.run(make_base_screenshots())
    asyncio.run(make_distro_screen_screenshots())
    asyncio.run(make_apps_screen_screenshots())
