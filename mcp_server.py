
from playwright.async_api import async_playwright
import google.generativeai as genai

class PlaywrightController:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()

    async def stop(self):
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def navigate(self, url):
        await self.page.goto(url)

    async def click(self, element_id):
        element = self.page.locator(f"[data-playwright-id='{element_id}']")
        await element.click()

    async def type_text(self, element_id, text):
        element = self.page.locator(f"[data-playwright-id='{element_id}']")
        await element.fill(text)

    async def get_page_snapshot(self):
        await self.page.wait_for_load_state("networkidle")

        interactive_elements = await self.page.query_selector_all(
            "a, button, input, textarea, select"
        )

        snapshot = []
        for i, element in enumerate(interactive_elements):
            element_id = f"element-{i}"
            await element.evaluate(f"(element) => element.setAttribute('data-playwright-id', '{element_id}')")

            if not await element.is_visible():
                continue

            tag_name = await element.get_attribute("tagName")
            text = await element.text_content()
            attrs = await element.evaluate("(element) => Array.from(element.attributes).reduce((obj, attr) => { obj[attr.name] = attr.value; return obj; }, {})")

            snapshot.append({
                "id": element_id,
                "tag": tag_name.lower(),
                "text": text.strip(),
                "attributes": attrs,
            })

        return snapshot

class AIAgent:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def get_next_action(self, conversation, snapshot):
        system_prompt = """
You are a web agent. Your goal is to complete the user's request by interacting with the web page.
You will be given a snapshot of the current page, which includes a list of interactive elements.
Based on the user's request and the page snapshot, you must choose the next action to take.
The available actions are:
- navigate(url): Go to a specific URL.
- click(element_id): Click on an element with the given ID.
- type(element_id, text): Type text into an element with the given ID.
- done(): Indicate that the task is complete.

You must respond with a JSON object representing the action to take. For example:
{"action": "navigate", "url": "https://www.google.com"}
{"action": "click", "element_id": "element-123"}
{"action": "type", "element_id": "element-456", "text": "hello world"}
{"action": "done"}
"""

        # Build the conversation history
        messages = [system_prompt]
        for role, content in conversation:
            messages.append(f"{role}: {content}")

        # Add the current page snapshot
        messages.append(f"Page snapshot:\n{snapshot}")

        response = self.model.generate_content(
            messages,
            generation_config=genai.types.GenerationConfig(
                candidate_count=1,
                temperature=0.7,
            )
        )

        return response.text
