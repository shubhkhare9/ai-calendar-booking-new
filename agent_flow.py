from calendar_utils import check_availability, book_event
from datetime import datetime, timedelta
import pytz
import dateparser
import re
from dateutil import parser as dateutil_parser
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from langgraph.graph import StateGraph
from typing import TypedDict, Optional
from calendar_utils import get_calendar_service, format_datetime
import datetime


WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

def extract_duration(user_input):
    match = re.search(r"for\s+(\d{1,2})\s*(hour|minute|minutes|hours)", user_input.lower())
    if match:
        value, unit = match.groups()
        value = int(value)
        if "hour" in unit:
            return value * 60
        return value
    return None

def extract_datetime(user_input):
    text = user_input.lower()
    now = datetime.now()
    tz = pytz.timezone("Asia/Kolkata")

    range_match = re.search(
        r"""between\s+(\d{1,2}(:\d{2})?\s*[ap]m)\s*(?:to|and|-)\s*(\d{1,2}(:\d{2})?\s*[ap]m).*?(monday|tuesday|wednesday|thursday|friday|saturday|sunday|week|tomorrow|today)""",
        text
    )

    if range_match:
        start_time, _, end_time, _, day_ref = range_match.groups()
        base_date = now
        if day_ref == "tomorrow":
            base_date += timedelta(days=1)
        elif day_ref == "today":
            pass
        elif "week" in day_ref:
            base_date += timedelta(weeks=1)
        elif day_ref in WEEKDAYS:
            target_day = WEEKDAYS[day_ref]
            current_day = now.weekday()
            days_ahead = (target_day - current_day + 7) % 7
            base_date += timedelta(days=days_ahead)
        parsed_day = base_date.date()
        start_dt = tz.localize(datetime.combine(parsed_day, dateutil_parser.parse(start_time).time()))
        end_dt = tz.localize(datetime.combine(parsed_day, dateutil_parser.parse(end_time).time()))
        return (start_dt.isoformat(), end_dt.isoformat())

    if "tomorrow" in text:
        dt = now + timedelta(days=1)

        if "night" in text:
            dt = dt.replace(hour=20, minute=0)
        elif "afternoon" in text:
            dt = dt.replace(hour=15, minute=0)
        elif "morning" in text:
            dt = dt.replace(hour=9, minute=0)
        else:
            dt = dt.replace(hour=10, minute=0)

        dt = tz.localize(dt)
        end = dt + timedelta(minutes=30)
        return dt.isoformat(), end.isoformat()


    if "today" in text:
        if "night" in text:
            dt = now.replace(hour=20, minute=0)
        elif "afternoon" in text:
            dt = now.replace(hour=15, minute=0)
        elif "morning" in text:
            dt = now.replace(hour=9, minute=0)
        else:
            dt = now.replace(hour=10, minute=0)

        dt = tz.localize(dt)
        end = dt + timedelta(minutes=30)
        return dt.isoformat(), end.isoformat()


    try:
        dt = dateutil_parser.parse(user_input, fuzzy=True)
        if dt.tzinfo is None:
            dt = tz.localize(dt)
        if dt.time() == datetime.min.time():
            dt = dt.replace(hour=10, minute=0)
        end = dt + timedelta(minutes=30)
        return dt.isoformat(), end.isoformat()
    except:
        pass

    for day in WEEKDAYS:
        if day in text:
            target_day = WEEKDAYS[day]
            current_day = now.weekday()
            days_ahead = (target_day - current_day + 7) % 7
            if "next" in text and days_ahead == 0:
                days_ahead = 7
            dt = now + timedelta(days=days_ahead)
            dt = dt.replace(hour=10, minute=0)
            dt = tz.localize(dt)
            end = dt + timedelta(minutes=30)
            return dt.isoformat(), end.isoformat()

    return None, None

class BookingState(TypedDict):
    message: str
    start: Optional[str]
    end: Optional[str]
    confirmed: Optional[bool]
    summary: Optional[str]
    duration: Optional[int]
    route: Optional[str]
    intent: Optional[str]

def node_extract(state: BookingState) -> BookingState:
    start, end = extract_datetime(state["message"])
    duration = extract_duration(state["message"])
    state["start"] = start
    state["end"] = end
    state["duration"] = duration
    state["summary"] = "Meeting"
    state["intent"] = "check" if "free" in state["message"].lower() or "available" in state["message"].lower() else "book"
    return state

def node_check(state: BookingState) -> BookingState:
    from calendar_utils import get_calendar_service
    service = get_calendar_service()

    if not state["start"]:
        state["route"] = "fail"
    elif state.get("intent") == "check":
        state["route"] = "suggest"
    elif check_availability(service, state["start"], state["end"]):
        state["route"] = "available"
    else:
        state["route"] = "busy"
    return state

def node_confirm(state: BookingState) -> BookingState:
    state["confirmed"] = True
    return state

def node_book(state: BookingState) -> BookingState:
    from calendar_utils import get_calendar_service
    service = get_calendar_service()
    event = book_event(service, state["summary"], state["start"], state["end"])
    start_fmt = dateutil_parser.parse(state["start"]).strftime('%B %d, %Y at %I:%M %p')
    end_fmt = dateutil_parser.parse(state["end"]).strftime('%I:%M %p')
    state["message"] = f"✅ Your meeting '{event['summary']}' has been booked on {start_fmt} to {end_fmt}."
    return state

def node_fail(state: BookingState) -> BookingState:
    state["message"] = "❌ I couldn't understand the date/time. Please try again."
    return state

def node_suggest(state: BookingState) -> BookingState:
    from calendar_utils import get_calendar_service
    from dateutil import parser as date_parser
    import traceback

    service = get_calendar_service()
    tz = pytz.timezone("Asia/Kolkata")

    suggestions = []
    try:
        raw_start = state.get("start")
        duration = state.get("duration") or 30

        dt = date_parser.parse(raw_start) if raw_start else datetime.now(tz)
        if dt.tzinfo is None:
            dt = tz.localize(dt)
        else:
            dt = dt.astimezone(tz)

        base = dt.replace(hour=9, minute=0, second=0, microsecond=0)

        for i in range(18):
            trial_start = base + timedelta(minutes=30 * i)
            trial_end = trial_start + timedelta(minutes=duration)
            if trial_end.hour >= 18:
                break
            if check_availability(service, trial_start.isoformat(), trial_end.isoformat()):
                suggestions.append(trial_start.strftime("%I:%M %p"))
            if len(suggestions) >= 5:
                break

        state["message"] = f"🗓️ You're free on that day at: {', '.join(suggestions)}." if suggestions else "❌ You're busy all day. No free slots found."

    except Exception as e:
        print("❌ Exception in node_suggest:", e)
        traceback.print_exc()
        state["message"] = "❌ Failed to suggest slots due to internal error."

    return state

def node_busy(state: BookingState) -> BookingState:
    state["message"] = "❌ You're busy at that time. Please suggest another slot."
    return state

workflow = StateGraph(BookingState)
workflow.add_node("extract", node_extract)
workflow.add_node("check", node_check)
workflow.add_node("confirm", node_confirm)
workflow.add_node("book", node_book)
workflow.add_node("fail", node_fail)
workflow.add_node("busy", node_busy)
workflow.add_node("suggest", node_suggest)

workflow.set_entry_point("extract")
workflow.add_edge("extract", "check")
workflow.add_conditional_edges("check", lambda s: s["route"], {
    "available": "confirm",
    "busy": "busy",
    "fail": "fail",
    "suggest": "suggest"
})
workflow.add_edge("confirm", "book")
workflow.set_finish_point("book")

calendar_graph = workflow.compile()

def run_langgraph(message: str, creds) -> str:
    print("🔍 Incoming message:", message)

    # Dummy example, assuming 2PM tomorrow
    tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
    start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
    end_time = start_time + datetime.timedelta(minutes=30)

    service = get_calendar_service(creds)

    if check_availability(service, format_datetime(start_time), format_datetime(end_time)):
        book_event(service, "Meeting", format_datetime(start_time), format_datetime(end_time))
        return f"✅ Meeting scheduled for {start_time.strftime('%Y-%m-%d %I:%M %p')}"
    else:
        return "❌ You're not available at that time."
