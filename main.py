from fastapi import FastAPI
from calendar_utils import get_calendar_service
from pydantic import BaseModel
# from agent_flow import ConversationState
from agent_flow import run_langgraph


# state = ConversationState()
app = FastAPI()
service = get_calendar_service()

class ChatInput(BaseModel):
    message: str

@app.get("/")
def home():
    return {"message": "Calendar AI is running!"}

@app.post("/chat")
def chat(data: ChatInput):
    user_input = data.message
    print(f"User input: {user_input}")
    reply = run_langgraph(user_input)
    return {"reply": reply}

@app.post("/chat/langgraph")
def chat_langgraph(data: ChatInput):
    user_input = data.message
    print(f"LangGraph input: {user_input}")
    reply = run_langgraph(user_input)
    return {"reply": reply}