from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os
from dotenv import load_dotenv
from agent_flow import run_langgraph

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
SCOPES = ["https://www.googleapis.com/auth/calendar"]

user_tokens = {}

app = FastAPI()

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

@app.get("/authorize")
def authorize():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uris": [REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline', include_granted_scopes='true')
    return RedirectResponse(auth_url)

@app.get("/callback")
async def oauth_callback(request: Request):
    code = request.query_params.get("code")

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uris": [REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

    flow.fetch_token(code=code)
    credentials = flow.credentials

    # ✅ Print all credential fields to logs
    print("==== OAUTH CREDENTIALS ====")
    print("Token:", credentials.token)
    print("Refresh Token:", credentials.refresh_token)
    print("Token URI:", credentials.token_uri)
    print("Client ID:", credentials.client_id)
    print("Client Secret:", credentials.client_secret)
    print("============================")

    user_tokens["demo_user"] = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes
    }

    return JSONResponse(content={"message": "✅ Authorization complete! You can now use the calendar."})



@app.post("/chat")
def chat(data: dict):
    try:
        user_input = data.get("message", "")
        creds_info = user_tokens.get("demo_user")

        if not creds_info:
            return {"reply": "❌ User not authenticated. Please visit /authorize."}

        creds = Credentials.from_authorized_user_info(info=creds_info, scopes=SCOPES)

        # Validate refresh_token and other required fields
        required_keys = ["refresh_token", "token_uri", "client_id", "client_secret"]
        for key in required_keys:
            if not creds_info.get(key):
                return {"reply": f"❌ Missing required field: {key}. Please re-authorize."}

        service = build('calendar', 'v3', credentials=creds)

        return {"reply": run_langgraph(user_input)}

    except Exception as e:
        print("❌ ERROR in /chat route:", str(e))
        return {"reply": f"❌ Backend error: {str(e)}"}
