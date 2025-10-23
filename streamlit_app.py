
import streamlit as st
from mcp_server import PlaywrightController, AIAgent
import json
import os

st.title("AI-Powered Web Agent")

# --- Initialization ---
@st.cache_resource
def install_playwright():
    """Installs the Playwright browser."""
    import subprocess
    subprocess.run(["playwright", "install", "chromium"], check=True)

install_playwright()

# API key input
api_key = st.sidebar.text_input("Enter your Google AI API Key", type="password")

# Initialize session state
if "playwright_controller" not in st.session_state:
    st.session_state.playwright_controller = PlaywrightController()

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Helper Functions ---
def perform_action(action):
    """Executes a single Playwright action."""
    controller = st.session_state.playwright_controller
    action_type = action.get("action")

    if action_type == "navigate":
        controller.navigate(action["url"])
        return f"Navigated to {action['url']}"
    elif action_type == "click":
        controller.click(action["element_id"])
        return f"Clicked element {action['element_id']}"
    elif action_type == "type":
        controller.type_text(action["element_id"], action["text"])
        return f"Typed '{action['text']}' into element {action['element_id']}"
    elif action_type == "done":
        return "Task marked as done."
    else:
        return f"Unknown action: {action_type}"

# --- UI Display ---
# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "screenshot_path" in message:
            st.image(message["screenshot_path"])

# --- Main Logic ---
if prompt := st.chat_input("What should I do?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if not api_key:
        st.warning("Please enter your Google AI API Key to continue.")
        st.stop()

    # Initialize AI Agent if not already done
    if "ai_agent" not in st.session_state:
        st.session_state.ai_agent = AIAgent(api_key)

    # --- Agent Execution Loop ---
    with st.chat_message("assistant"):
        with st.spinner("Agent is thinking and acting..."):
            # 1. Get Page Snapshot
            snapshot = st.session_state.playwright_controller.get_page_snapshot()

            # 2. Get AI Action
            conversation = [(msg["role"], msg["content"]) for msg in st.session_state.messages]
            action_json_string = st.session_state.ai_agent.get_next_action(conversation, snapshot)

            try:
                action = json.loads(action_json_string)
            except json.JSONDecodeError:
                st.error(f"Error: The AI returned invalid JSON. Please try again. \n```json\n{action_json_string}\n```")
                st.stop()

            # 3. Perform Action
            result = perform_action(action)
            st.markdown(result)

            # 4. Take Screenshot and Save
            screenshot_path = "screenshot.png"
            st.session_state.playwright_controller.page.screenshot(path=screenshot_path)

            # 5. Display Screenshot and Update History
            if os.path.exists(screenshot_path):
                st.image(screenshot_path)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result,
                    "screenshot_path": screenshot_path
                })
            else:
                 st.session_state.messages.append({
                    "role": "assistant",
                    "content": result
                })

    # Rerun to update the chat display smoothly
    st.rerun()
