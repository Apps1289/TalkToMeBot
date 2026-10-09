# TalkToMeBot
Ai based chatbot for normal conversation like any other chatting models

## Run the FastAPI backend

Install the dependencies:

```bash
pip install -r requirements.txt
```

Start the API from the project root:

```bash
uvicorn app:app --reload
```

The API will be available at `http://127.0.0.1:8000`. Interactive API
documentation is available at `http://127.0.0.1:8000/docs`.

Send a message with a conversation-specific `thread_id` to preserve the
conversation state managed by LangGraph:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"thread_id\":\"conversation-1\",\"message\":\"Hello\"}"
```

The Ollama service must be running locally with the `llama3.2` model available.

## Run the Streamlit frontend

Keep the FastAPI backend running in one terminal, then start the frontend from
the project root in a second terminal:

```bash
streamlit run frontend.py
```

The frontend sends each message to FastAPI's `/chat` endpoint. Each chat appears
in the sidebar; selecting one restores its displayed messages and reuses its
`thread_id` for the next request. **New chat** creates a separate conversation.
The chat list is held in Streamlit session state, so it lasts for the current
browser session. The backend's in-memory LangGraph checkpointer also loses its
conversation state when FastAPI restarts.
