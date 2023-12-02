#!/usr/bin/env python
# shamelessly stolen from:
# https://blog.davep.org/2023/07/03/making-my-github-banner.html

from smol_k8s_lab.tui.base import BaseApp
import asyncio


async def make_screenshots() -> None:
    """
    make all the screenshots
    """
    async with BaseApp().run_test(size=(87, 48)) as pilot:
        pilot.app.save_screenshot("./docs/images/screenshots/start_screen.svg")

if __name__ == "__main__":
    asyncio.run(make_screenshots())
