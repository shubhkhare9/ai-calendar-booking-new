# calendar_utils.py

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import datetime
from dateutil import parser as dateutil_parser
from google.auth.transport.requests import Request
import logging, os, pickle, json
import streamlit as st
from datetime import datetime, timedelta, timezone




SCOPES = ["https://www.googleapis.com/auth/calendar"]

def get_calendar_service():
    token_json = json.loads(os.environ["GOOGLE_CALENDAR_TOKEN"])
    creds = Credentials.from_authorized_user_info(token_json, scopes=SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build('calendar', 'v3', credentials=creds)

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
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))
        return dt.isoformat()
    elif isinstance(dt, datetime.date):
        dt = datetime.combine(dt, datetime.min.time())
        dt = dt.replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))
        return dt.isoformat()
    else:
        raise ValueError("Unsupported datetime type. Must be datetime or datetime.date.")
    
# @st.cache_resource
# def load_credentials():
#     token_json = json.loads(os.environ["GOOGLE_CALENDAR_TOKEN"])
#     creds = Credentials.from_authorized_user_info(token_json, scopes=SCOPES)
#     return creds