#!/usr/bin/env python
# shamelessly stolen from:
# https://blog.davep.org/2023/07/03/making-my-github-banner.html

from smol_k8s_lab.tui.base import BaseApp
import asyncio


async def make_screenshots() -> None:
    """
    make all the screenshots
    """
    async with BaseApp().run_test(size=(86, 47)) as pilot:
        pilot.app.save_screenshot("./docs/images/screenshots/start_screen.svg")

        # Test pressing the "tab" key followed by the "c" key
        await pilot.press("tab", "c")  
        pilot.app.save_screenshot("./docs/images/screenshots/tui_config_screen.svg")

        # Test pressing the "q" key
        await pilot.press("q", "h")  
        pilot.app.save_screenshot("./docs/images/screenshots/tui_help_screen.svg")

if __name__ == "__main__":
    asyncio.run(make_screenshots())
