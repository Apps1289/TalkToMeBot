import sqlite3
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Literal, Annotated
from pydantic import BaseModel, Field
from .model import model
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
import requests


# tool
search_tool = DuckDuckGoSearchRun(region='us-en')

@tool
def calc(first_num: float, second_num:float, operation:str) -> dict:
    """
    A simple calculator tool that performs basic arithmetic operations.
    
    """
    if operation == "add":
        result = first_num + second_num
    elif operation == "subtract":
        result = first_num - second_num
    elif operation == "multiply":
        result = first_num * second_num
    elif operation == "divide":
        if second_num == 0:
            return {"error": "Division by zero is not allowed."}
        result = first_num / second_num
    else:
        return {"error": f"Unsupported operation: {operation}"}

    return {"first": first_num, "second": second_num, "operation": operation, "result": result}

@tool
def get_stock_price(symbol: str) -> dict:
    
    """  
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA') 
    using Alpha Vantage with API key in the URL.
    
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=4DLY5OKRPHY7BBO8"
    

    response = requests.get(url)
    data = response.json()

    return data

tools = [search_tool,get_stock_price,calc]
llm_with_tools = model.bind_tools(tools)


# defining state of the chatbot
class ChatbotState(TypedDict):
    
    messages: Annotated[list[BaseMessage], add_messages] # list of messages in the conversation]


# defining node
def chat_bot(state: ChatbotState) -> ChatbotState:
    """LLM node that may answer or request a tool call."""
    sys_msg = SystemMessage(
        content= """   
    You are TalkToMeBot, a friendly general-purpose conversational assistant.
    Follow these rules strictly:

    1. Respond naturally to greetings, introductions, small talk,
       and general conversational messages.
    2. Never call a tool just because a tool is available.
    3. Use the calculator only when the user explicitly asks for a
       calculation or a mathematical problem requires calculation.
    4. Use the stock price tool only when the user asks about a stock
       price or related stock quote.
    5. Use web search only when the user asks for information that
       requires searching the web or up-to-date information.
    6. If the user says "I am Abhi", acknowledge the introduction
       naturally. Do not perform calculations or searches.
    7. Never invent a tool request or introduce an unrelated topic.
    8. If no tool is needed, answer the user directly.
    """
    )
    messages = [sys_msg] + state["messages"]
    response = llm_with_tools.invoke(messages)
    
    return {
        "messages": [response]  # return the response as a list of messages
    }

tool_node = ToolNode(tools=tools)


conn = sqlite3.connect(database='chatbot_state.db', check_same_thread=False)  # Create a connection to the SQLite database
# checkpointer -> to save the state of the chatbot
checkpointer = SqliteSaver(conn=conn)

# define the state graph
graph = StateGraph(ChatbotState)

# adding nodes to the graph
graph.add_node('chat_bot', chat_bot)
graph.add_node("tools", tool_node)

# adding edges to the graph
graph.add_edge(START, 'chat_bot')
graph.add_conditional_edges('chat_bot', tools_condition)
graph.add_edge('tools', 'chat_bot')



chatbot = graph.compile(checkpointer=checkpointer)





    
    