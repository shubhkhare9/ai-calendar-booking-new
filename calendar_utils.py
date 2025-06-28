#calendar_utils.py
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import datetime
from dateutil import parser as dateutil_parser
from google.auth.transport.requests import Request
import os
import pickle

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    creds = None
    # 🔐 Save the token for future runs
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # 🔄 If not valid or missing, re-authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # 💾 Save token to reuse next time
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # ✅ Build the service using saved creds
    from googleapiclient.discovery import build
    service = build('calendar', 'v3', credentials=creds)
    return service



def check_availability(service, start_iso, end_iso):

    print("🔍 Checking availability:")
    print("→ timeMin:", start_iso)
    print("→ timeMax:", end_iso)

    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_iso,
        timeMax=end_iso,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    return len(events) == 0





def book_event(service, summary, start_time, end_time):
    event = {
        'summary': summary,
        'start': {
            'dateTime': start_time,
            'timeZone': 'Asia/Kolkata',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'Asia/Kolkata',
        }
    }

    return service.events().insert(calendarId='primary', body=event).execute()

def format_datetime(dt):
      if isinstance(dt, datetime.datetime):
            return dt.isoformat()
      elif isinstance(dt, datetime.date):
            return dt.isoformat() + 'T00:00:00'
      else:
            raise ValueError("Unsupported datetime type. Must be datetime.datetime or datetime.date.")
