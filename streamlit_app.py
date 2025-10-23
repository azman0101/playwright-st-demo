
import streamlit as st
import subprocess
from playwright.sync_api import sync_playwright
import os

st.title("Playwright on Streamlit Cloud")

@st.cache_resource
def install_browsers():
    subprocess.run(["playwright", "install", "chromium"], check=True)

# Install browsers
with st.spinner("Installing browsers..."):
    install_browsers()

st.success("Browsers installed!")

url = st.text_input("Enter a URL to visit")

if url:
    try:
        with st.spinner("Visiting URL and taking a screenshot..."):
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.goto(url)
                screenshot_path = "screenshot.png"
                page.screenshot(path=screenshot_path)
                browser.close()

        if os.path.exists(screenshot_path):
            st.image(screenshot_path)
            st.success("Screenshot taken successfully!")
        else:
            st.error("Failed to take screenshot.")
    except Exception as e:
        st.error(f"An error occurred: {e}")
