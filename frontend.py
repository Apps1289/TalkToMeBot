import time
import streamlit as st
from src.helper import chatbot
from langchain_core.messages import HumanMessage
from src.utility import (
    generate_thread_id,
    reset_chat,
    add_thread,
    load_conversation,
    get_thread_label,
)

# Initialize session state before rendering or handling the sidebar.
if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "thread_chat" not in st.session_state:
    st.session_state["thread_chat"] = []

if "thread_id" not in st.session_state:
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
    
    # Streaming -> Display the response as it is generated
    with st.chat_message("assistant"):
        # stream returns message chunks and metadata, we only want the content of the message chunks
        # it is a generator, so we can use a generator expression to 
        # extract the content of the message chunks
        response_text = st.write_stream(
            message_chunks.content for message_chunks, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config= {"configurable": {"thread_id": st.session_state["thread_id"]}},
                stream_mode="messages"
            )
        )
        st.session_state.message_history.append({"role": "assistant", "content": response_text})