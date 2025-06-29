from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from agent_flow import run_langgraph
import os, json

app = FastAPI()

class ChatInput(BaseModel):
    message: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "🚀 AI Calendar Backend is running!"}

def get_calendar_creds():
    try:
        token_data = json.loads(os.environ["GOOGLE_CALENDAR_TOKEN"])
    except KeyError:
        raise ValueError("❌ GOOGLE_CALENDAR_TOKEN environment variable is missing or invalid.")
    creds = Credentials.from_authorized_user_info(token_data, scopes=["https://www.googleapis.com/auth/calendar"])
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds

@app.post("/chat")
def chat(data: ChatInput):
    try:
        creds = get_calendar_creds()
        reply = run_langgraph(data.message, creds)
        return {"reply": reply}
    except Exception as e:
        return {"reply": f"❌ Backend error: {str(e)}"}
