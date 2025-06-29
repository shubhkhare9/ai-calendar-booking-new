# === main.py ===
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from pydantic import BaseModel
# from dotenv import load_dotenv
from agent_flow import run_langgraph
import os, json

# load_dotenv()

# CLIENT_ID = os.getenv("CLIENT_ID")
# CLIENT_SECRET = os.getenv("CLIENT_SECRET")
# REDIRECT_URI = os.getenv("REDIRECT_URI")
# SCOPES = ["https://www.googleapis.com/auth/calendar"]

# user_tokens = {}

app = FastAPI()

class ChatInput(BaseModel):
    message: str

# ✅ Enable CORS
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

# ✅ Load your calendar credentials from environment variable
def get_calendar_creds():
    token_data = json.loads(os.environ["GOOGLE_CALENDAR_TOKEN"])
    creds = Credentials.from_authorized_user_info(token_data, scopes=["https://www.googleapis.com/auth/calendar"])
    return creds

@app.post("/chat")
def chat(data: ChatInput):
    try:
        user_input = data.message
        print(f"📨 Incoming message: {user_input}")

        creds = get_calendar_creds()
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

        reply = run_langgraph(user_input, creds)
        print("✅ Agent reply:", reply)
        return {"reply": reply}

    except Exception as e:
        print("❌ ERROR in /chat route:", str(e))
        return {"reply": f"❌ Backend error: {str(e)}"}