# === calendar_utils.py ===
import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

# def get_calendar_service():
#     token_info = json.loads(os.getenv("GOOGLE_CALENDAR_TOKEN"))
#     creds = Credentials.from_authorized_user_info(token_info)
#     service = build("calendar", "v3", credentials=creds)
#     return service

def check_availability(service, start_iso, end_iso):
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
        'start': {'dateTime': start_time, 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': end_time, 'timeZone': 'Asia/Kolkata'},
    }
    return service.events().insert(calendarId='primary', body=event).execute()

def get_calendar_service():
    token_info = json.loads(os.getenv("GOOGLE_CALENDAR_TOKEN"))
    creds = Credentials.from_authorized_user_info(token_info)
    return build("calendar", "v3", credentials=creds)

def format_datetime(dt):
    import datetime
    if isinstance(dt, datetime.datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
        return dt.isoformat()
    elif isinstance(dt, datetime.date):
        dt = datetime.datetime.combine(dt, datetime.time(0, 0))
        dt = dt.replace(tzinfo=datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
        return dt.isoformat()
    else:
        raise ValueError("Unsupported datetime type. Must be datetime or datetime.date.")
