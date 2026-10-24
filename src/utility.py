import uuid
import streamlit as st
from src.backend_sql import chatbot, checkpointer
from langchain_core.messages import HumanMessage

# generate a unique id for the session
def generate_thread_id():
    thread_id = uuid.uuid4()
    return thread_id

# creating a config dictionary to store the thread id
def add_thread(thread_id):
    if "thread_chat" not in st.session_state:
        st.session_state["thread_chat"] = []

    if thread_id not in st.session_state["thread_chat"]:
        st.session_state["thread_chat"].append(thread_id)
        
# reset the chat by clearing the session state
def reset_chat():
    thread_id = generate_thread_id()
    st.session_state["thread_id"] = thread_id
    st.session_state["message_history"] = []
    
def load_conversation(thread_id):
    state = chatbot.get_state(config={"configurable": {"thread_id": thread_id}})
    
    return state.values.get("messages", [])


def get_thread_label(thread_id, max_length=40):
    """Return a short, user-friendly label for a conversation thread."""
    messages = load_conversation(thread_id)

    for message in messages:
        if isinstance(message, HumanMessage):
            content = str(message.content).strip()
            if content:
                if len(content) > max_length:
                    return f"{content[:max_length - 3].rstrip()}..."
                return content

    return None

thread_set = set()  # Initialize an empty set to store unique thread IDs
def get_saved_threads():
    for checkpoint in checkpointer.list(None):
        thread_set.add(checkpoint.config['configurable']['thread_id'])  # Add each thread ID to the set
        
    return list(thread_set)  # Return the unique thread IDs as a list

    
        
    
    
