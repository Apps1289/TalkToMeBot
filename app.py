from functools import partial
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from src.helper import chatbot


# FastAPI application instance
app = FastAPI(
    title="TalkToMeBot API",
    description="FastAPI backend for the LangGraph chatbot.",
    version="1.0.0",
)

# Pydantic models for request validation
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10_000)
    thread_id: str = Field(..., min_length=1, max_length=200)

# Pydantic model for response validation
class ChatResponse(BaseModel):
    thread_id: str
    response: str


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "TalkToMeBot API is running"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    config = {"configurable": {"thread_id": request.thread_id}}

    result = await run_in_threadpool(
        partial(
            chatbot.invoke,
            {"messages": [HumanMessage(content=request.message)]},
            config=config,
        )
    )
    response_message = result["messages"][-1]
    response_text = response_message.content

    if not isinstance(response_text, str):
        raise HTTPException(
            status_code=502,
            detail="The chatbot returned an invalid response.",
        )

    return ChatResponse(thread_id=request.thread_id, response=response_text)