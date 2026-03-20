"""
ADA v3 — Web Automation Skill.
Operates external websites using Playwright.
"""
import asyncio
from typing import Optional
from ada_core.skills.base_skill import BaseSkill

# This skill requires the 'playwright' package
try:
    from playwright.async_api import async_playwright
except ImportError:
    async_playwright = None

class WebAutomationSkill(BaseSkill):
    def __init__(self):
        super().__init__()
        self.role = "You are ADA's Web Operator. Your objective is to interact with external websites to extract data or perform tasks."
        self.browser = None
        self.context = None
        self.page = None

    async def open_page(self, url: str):
        if not async_playwright:
            return "Error: Playwright not installed."
        
        if not self.browser:
            self.pw = await async_playwright().start()
            self.browser = await self.pw.chromium.launch(headless=True)
            self.context = await self.browser.new_context()
            
        self.page = await self.context.new_page()
        await self.page.goto(url)
        return f"Page {url} opened."

    async def click(self, selector: str):
        if self.page:
            await self.page.click(selector)
            return f"Clicked {selector}."
        return "No page open."

    async def type_text(self, selector: str, text: str):
        if self.page:
            await self.page.fill(selector, text)
            return f"Typed in {selector}."
        return "No page open."

    async def read_text(self, selector: str) -> str:
        if self.page:
            return await self.page.inner_text(selector)
        return "No page open."

    async def close(self):
        if self.browser:
            await self.browser.close()
            await self.pw.stop()
            self.browser = None
        return "Browser closed."
