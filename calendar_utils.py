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

# def get_calendar_service():
#     creds = Credentials(
#         token=None,
#         refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
#         token_uri="https://oauth2.googleapis.com/token",
#         client_id=os.getenv("GOOGLE_CLIENT_ID"),
#         client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
#         scopes=["https://www.googleapis.com/auth/calendar"]
#     )

#     service = build('calendar', 'v3', credentials=creds)
#     return service

def get_calendar_service():
    # Replace with the path to your credentials JSON file
    credentials_path = "C:\Users\Admin\OneDrive\Desktop\AI-calendar-booking-CLEAN\credentials.json"

    # Load credentials from file
    creds = Credentials.from_authorized_user_file(credentials_path, scopes=["https://www.googleapis.com/auth/calendar"])

    # Ensure the credentials contain the necessary fields
    if not creds.valid and creds.refresh_token:
        creds.refresh(Request())

    # Build the Google Calendar service
    service = build("calendar", "v3", credentials=creds)
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
