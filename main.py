from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from agent_flow import run_langgraph
import os, json
from calendar_utils import get_calendar_service

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
    token_data = json.loads(os.environ["GOOGLE_CALENDAR_TOKEN"])
    creds = Credentials.from_authorized_user_info(token_data, scopes=["https://www.googleapis.com/auth/calendar"])
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds

# def get_calendar_service():
#     from googleapiclient.discovery import build
#     creds = get_calendar_creds()
#     service = build("calendar", "v3", credentials=creds)
#     return service


@app.post("/chat")
def chat(data: ChatInput):
    try:
        user_input = data.message
        print(f"📨 Incoming message: {user_input}")

        service = get_calendar_service()
        reply = run_langgraph(user_input, service)  # pass service to your logic
        print("✅ Agent reply:", reply)
        return {"reply": reply}

    except Exception as e:
        print("❌ ERROR in /chat route:", str(e))
        return {"reply": f"❌ Backend error: {str(e)}"}
