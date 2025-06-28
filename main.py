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
import json

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

import json

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

    # ✅ Log for debugging
    print("==== OAUTH CREDENTIALS ====")
    print(credentials.to_json())
    print("============================")

    # ✅ Save the full credential object in proper JSON format
    # Ensure refresh_token is included in the saved credentials
    credentials_dict = json.loads(credentials.to_json())
    if not credentials_dict.get("refresh_token") and credentials.refresh_token:
        credentials_dict["refresh_token"] = credentials.refresh_token
    elif not credentials_dict.get("refresh_token"):
        return JSONResponse(content={"message": "❌ Missing refresh_token. Please reauthorize."}, status_code=400)
    user_tokens["demo_user"] = credentials_dict

    return JSONResponse(content={"message": "✅ Authorization complete! You can now use the calendar."})



@app.post("/chat")
def chat(data: dict):
    try:
        user_input = data.get("message", "")
        creds_info = user_tokens.get("demo_user")

        if not creds_info:
            return {"reply": "❌ User not authenticated. Please visit /authorize."}

        # Ensure all necessary fields are present in creds_info
        if not all(key in creds_info for key in ["refresh_token", "token_uri", "client_id", "client_secret"]):
            return {"reply": "❌ Missing necessary fields in credentials. Please reauthorize."}
        
        creds = Credentials.from_authorized_user_info(info=creds_info, scopes=SCOPES)

        # Manually refresh if expired
        if creds.expired and creds.refresh_token:
            creds.refresh(GoogleRequest())

        service = build('calendar', 'v3', credentials=creds)
        return {"reply": run_langgraph(user_input)}

    except Exception as e:
        print("❌ ERROR in /chat route:", str(e))
        return {"reply": f"❌ Backend error: {str(e)}"}
