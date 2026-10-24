from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Literal, Annotated
from pydantic import BaseModel, Field
from .model import model
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver

# defining state of the chatbot
class ChatbotState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages] # list of messages in the conversation]


# defining node
def chat_bot(state: ChatbotState) -> ChatbotState:
    messages = state["messages"]
    response = model.invoke(messages)
    
    return {
        "messages": [response]  # return the response as a list of messages
    }
    
# checkpointer -> to save the state of the chatbot
checkpointer = InMemorySaver()

# define the state graph
graph = StateGraph(ChatbotState)

# adding nodes to the graph
graph.add_node('chat_bot', chat_bot)

# adding edges to the graph
graph.add_edge(START, 'chat_bot')
graph.add_edge('chat_bot', END)

chatbot = graph.compile(checkpointer=checkpointer)
    
    