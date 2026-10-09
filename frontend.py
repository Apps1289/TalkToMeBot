import time
import uuid

import requests
import streamlit as st


API_URL = "http://127.0.0.1:8000/chat"
NEW_CHAT_TITLE = "New chat"


def type_response(text: str):
    """Yield one character at a time for a typewriter effect."""
    for character in text:
        yield character
        time.sleep(0.02)


def make_chat_title(message: str, limit: int = 32) -> str:
    """Use the first user message as a short sidebar title."""
    title = " ".join(message.split())
    if len(title) > limit:
        return title[: limit - 1].rstrip() + "…"
    return title


# Keep each chat's ID and visible transcript together in this browser session.
# Migrate state from the earlier single-chat version if Streamlit still has it.
if "chats" not in st.session_state:
    old_thread_id = st.session_state.get("thread_id", str(uuid.uuid4()))
    old_messages = st.session_state.get("message_history", [])
    first_user_message = next(
        (message["content"] for message in old_messages if message["role"] == "user"),
        None,
    )
    st.session_state["chats"] = {
        old_thread_id: {
            "title": make_chat_title(first_user_message) if first_user_message else NEW_CHAT_TITLE,
            "messages": old_messages,
        }
    }
    st.session_state["active_thread_id"] = old_thread_id

if not st.session_state["chats"]:
    new_thread_id = str(uuid.uuid4())
    st.session_state["chats"][new_thread_id] = {
        "title": NEW_CHAT_TITLE,
        "messages": [],
    }
    st.session_state["active_thread_id"] = new_thread_id
elif st.session_state.get("active_thread_id") not in st.session_state["chats"]:
    st.session_state["active_thread_id"] = next(iter(st.session_state["chats"]))


with st.sidebar:
    st.title("Chats")
    if st.button("＋ New chat", use_container_width=True):
        new_thread_id = str(uuid.uuid4())
        st.session_state["chats"][new_thread_id] = {
            "title": NEW_CHAT_TITLE,
            "messages": [],
        }
        st.session_state["active_thread_id"] = new_thread_id
        st.rerun()

    st.divider()
    chat_ids = list(st.session_state["chats"])
    for chat_id in reversed(chat_ids):
        chat = st.session_state["chats"][chat_id]
        is_active = chat_id == st.session_state["active_thread_id"]
        if st.button(
            chat["title"],
            key=f"chat_{chat_id}",
            type="primary" if is_active else "secondary",
            use_container_width=True,
        ):
            st.session_state["active_thread_id"] = chat_id
            st.rerun()


active_thread_id = st.session_state["active_thread_id"]
active_chat = st.session_state["chats"][active_thread_id]

for msg in active_chat["messages"]:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.text(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.text(msg["content"])

if active_chat.get("error"):
    st.error(active_chat["error"])


# The browser submits a message to Streamlit; Streamlit sends it to FastAPI.
user_input = st.chat_input("Type your message here...")
if user_input:
    active_chat["error"] = None
    active_chat["messages"].append({"role": "user", "content": user_input})
    if active_chat["title"] == NEW_CHAT_TITLE:
        active_chat["title"] = make_chat_title(user_input)

    with st.chat_message("user"):
        st.text(user_input)

    with st.chat_message("assistant"):
        try:
            api_response = requests.post(
                API_URL,
                json={
                    "thread_id": active_thread_id,
                    "message": user_input,
                },
                timeout=120,
            )
        except requests.exceptions.RequestException:
            active_chat["error"] = (
                "Could not reach FastAPI. Start the backend with `uvicorn app:app --reload`."
            )
        else:
            if not api_response.ok:
                active_chat["error"] = f"FastAPI returned HTTP {api_response.status_code}."
            else:
                try:
                    payload = api_response.json()
                    response_text = payload.get("response") if isinstance(payload, dict) else None
                    if not isinstance(response_text, str):
                        raise ValueError("FastAPI response did not include a text response.")
                except ValueError:
                    active_chat["error"] = "FastAPI returned an invalid response."
                else:
                    active_chat["error"] = None
                    displayed_response = st.write_stream(type_response(response_text))
                    active_chat["messages"].append(
                        {"role": "assistant", "content": displayed_response}
                    )
    st.rerun()
