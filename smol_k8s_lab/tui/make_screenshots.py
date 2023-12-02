#!/usr/bin/env python
# shamelessly stolen from:
# https://blog.davep.org/2023/07/03/making-my-github-banner.html

from smol_k8s_lab.tui.base import BaseApp
import asyncio


async def make_base_screenshots() -> None:
    """
    make all the screenshots
    """
    async with BaseApp().run_test(size=(87, 47)) as pilot:
        pilot.app.save_screenshot("./docs/images/screenshots/start_screen.svg")

        # Test pressing the "tab" key followed by the "c" key
        await pilot.press("tab", "c")
        pilot.app.save_screenshot("./docs/images/screenshots/tui_config_screen.svg")

        # Test pressing the "q" key
        await pilot.press("q", "h")
        pilot.app.save_screenshot("./docs/images/screenshots/tui_help_screen.svg")

        await pilot.press("q")

async def make_distro_screen_screenshots() -> None:
    """
    make all the screenshots
    """
    async with BaseApp().run_test(size=(87, 47)) as pilot:
        # Test pressing the "enter" key
        await pilot.press("enter", "enter", "enter")
        pilot.app.save_screenshot("./docs/images/screenshots/distro_config_screen.svg")

        # Test selecting another distro from the drop down
        await pilot.press("enter", "down", "enter")
        pilot.app.save_screenshot("./docs/images/screenshots/kind_config_screen.svg")

        # Test selecting another distro from the drop down
        await pilot.press("tab", "tab", "tab", "right")
        pilot.app.save_screenshot("./docs/images/screenshots/kind_config_screen2.svg")


async def make_apps_screen_screenshots() -> None:
    """
    make all the screenshots
    """
    async with BaseApp().run_test(size=(87, 47)) as pilot:
        # Test pressing the "enter" key and then the "n" key
        await pilot.press("enter", "n")
        pilot.app.save_screenshot("./docs/images/screenshots/apps_screen.svg")


if __name__ == "__main__":
    asyncio.run(make_base_screenshots())
    asyncio.run(make_distro_screen_screenshots())
    asyncio.run(make_apps_screen_screenshots())
