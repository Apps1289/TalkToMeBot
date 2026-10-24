import os
from dotenv import load_dotenv


load_dotenv()
os.environ["LANGSMITH_PROJECT"] = "CHATBOT"

import time
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk, ToolMessage
from src.tool_backend import chatbot
from src.utility import (
    generate_thread_id,
    reset_chat,
    add_thread,
    load_conversation,
    get_thread_label,
    get_saved_threads,
)

# Initialize session state before rendering or handling the sidebar.
if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "thread_chat" not in st.session_state:
    st.session_state["thread_chat"] = get_saved_threads()

if "thread_id" not in st.session_state or isinstance(
    st.session_state["thread_id"], list
):
    st.session_state["thread_id"] = generate_thread_id()
    

# Sidebar for my chat
st.sidebar.title("TalkToMeBot")
if st.sidebar.button("New Chat"):
    reset_chat()
    st.rerun()
    
st.sidebar.header("Conversation History")
for thread_id in st.session_state["thread_chat"][::-1]:  # Display the most recent threads first
    thread_label = get_thread_label(thread_id)
    
    if thread_label is None:
        continue
    if st.sidebar.button(thread_label, key=f"thread_{thread_id}"):
        st.session_state["thread_id"] = thread_id
        messages = load_conversation(thread_id)
        
        temp_msg = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = "user"
            else:
                role = "assistant"
            temp_msg.append({"role": role, "content": msg.content})
        st.session_state["message_history"] = temp_msg
        st.rerun()
        
for message in st.session_state.message_history:
    with st.chat_message(message["role"]):
        st.text(message["content"])
        
# The browser submits a message to Streamlit; Streamlit sends it to FastAPI.
user_input = st.chat_input("Type your message here...")

if user_input:
    # Add the thread only after it contains the first user message.
    add_thread(st.session_state["thread_id"])
    st.session_state.message_history.append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.text(user_input)
    
    CONFIG = {
        "configurable": {"thread_id": st.session_state["thread_id"]},
        "metadata": {"thread_id": st.session_state["thread_id"]},
        "run_name": "chat_turn",
    }

    # Assistant streaming block
    with st.chat_message("assistant"):
        # Use a mutable holder so the generator can set/modify it
        status_holder = {"box": None}

        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages",
            ):
                # Lazily create & update the SAME status container when any tool runs
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", "tool")
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"🔧 Using `{tool_name}` …", expanded=True
                        )
                    else:
                        status_holder["box"].update(
                            label=f"🔧 Using `{tool_name}` …",
                            state="running",
                            expanded=True,
                        )

                # Stream ONLY assistant tokens
                if isinstance(message_chunk, AIMessage):
                    yield message_chunk.content

        ai_message = st.write_stream(ai_only_stream())

        # Finalize only if a tool was actually used
        if status_holder["box"] is not None:
            status_holder["box"].update(
                label="✅ Tool finished", state="complete", expanded=False
            )

    # Save assistant message
    st.session_state["message_history"].append(
        {"role": "assistant", "content": ai_message}
    )