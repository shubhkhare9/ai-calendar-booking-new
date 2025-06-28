from calendar_utils import check_availability, book_event, get_calendar_service, format_datetime
from datetime import datetime, timedelta, time
import pytz
import dateparser
import re
from dateutil import parser as dateutil_parser
from typing import TypedDict, Optional
from langgraph.graph import StateGraph

WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

class BookingState(TypedDict):
    message: str
    start: Optional[str]
    end: Optional[str]
    confirmed: Optional[bool]
    summary: Optional[str]
    duration: Optional[int]
    route: Optional[str]
    intent: Optional[str]
    creds: Optional[any]  # store credentials

def extract_duration(user_input):
    match = re.search(r"for\s+(\d{1,2})\s*(hour|minute|minutes|hours)", user_input.lower())
    if match:
        value, unit = match.groups()
        value = int(value)
        return value * 60 if "hour" in unit else value
    return None

def extract_datetime(user_input):
    tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(tz)

    parsed = dateparser.parse(
        user_input,
        settings={"PREFER_DATES_FROM": "future", "TIMEZONE": "Asia/Kolkata", "RETURN_AS_TIMEZONE_AWARE": True}
    )

    if not parsed:
        return None, None

    text = user_input.lower()
    if "afternoon" in text:
        parsed = parsed.replace(hour=14, minute=0)
    elif "evening" in text:
        parsed = parsed.replace(hour=18, minute=0)
    elif "morning" in text:
        parsed = parsed.replace(hour=10, minute=0)
    elif "night" in text:
        parsed = parsed.replace(hour=21, minute=0)

    end = parsed + timedelta(minutes=30)
    return parsed.isoformat(), end.isoformat()

def node_extract(state: BookingState) -> BookingState:
    state["start"], state["end"] = extract_datetime(state["message"])
    state["duration"] = extract_duration(state["message"])
    state["summary"] = "Meeting"
    state["intent"] = "check" if "free" in state["message"].lower() or "available" in state["message"].lower() else "book"
    return state

def node_check(state: BookingState) -> BookingState:
    if not state["start"]:
        state["route"] = "fail"
        return state

    service = get_calendar_service(state["creds"])
    if state["intent"] == "check":
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
    service = get_calendar_service(state["creds"])
    event = book_event(service, state["summary"], state["start"], state["end"])
    start_fmt = dateutil_parser.parse(state["start"]).strftime('%B %d, %Y at %I:%M %p')
    end_fmt = dateutil_parser.parse(state["end"]).strftime('%I:%M %p')
    state["message"] = f"✅ Your meeting '{event['summary']}' has been booked on {start_fmt} to {end_fmt}."
    return state

def node_fail(state: BookingState) -> BookingState:
    state["message"] = "❌ I couldn't understand the date/time. Please try again."
    return state

def node_busy(state: BookingState) -> BookingState:
    state["message"] = "❌ You're busy at that time. Please suggest another slot."
    return state

def node_suggest(state: BookingState) -> BookingState:
    service = get_calendar_service(state["creds"])
    tz = pytz.timezone("Asia/Kolkata")
    suggestions = []

    base = dateutil_parser.parse(state["start"]).astimezone(tz)
    base = base.replace(hour=9, minute=0, second=0, microsecond=0)
    duration = state.get("duration") or 30

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
    state = {
        "message": message,
        "start": None,
        "end": None,
        "confirmed": False,
        "summary": None,
        "duration": None,
        "route": None,
        "intent": None,
        "creds": creds
    }
    print("🔍 Incoming message:", message)
    final = calendar_graph.invoke(state)
    print("📤 Final state:", final)
    return final.get("message", "🤖 Something went wrong.")


def interpret_fuzzy_time(message: str) -> Optional[datetime.datetime]:
    try:
        # Try parsing directly with strict settings
        parsed = dateparser.parse(
            message,
            settings={
                "PREFER_DATES_FROM": "future",
                "TIMEZONE": "Asia/Kolkata",
                "RETURN_AS_TIMEZONE_AWARE": True,
                "DATE_ORDER": "DMY",  # Very important for formats like 2/7/2025
                "RELATIVE_BASE": datetime.datetime.now(pytz.timezone("Asia/Kolkata")),
            }
        )

        if not parsed:
            print("❌ Could not parse datetime using dateparser.")
            return None

        message_lower = message.lower()

        # Set hour defaults for fuzzy phrases
        if "afternoon" in message_lower:
            parsed = parsed.replace(hour=14, minute=0)
        elif "evening" in message_lower:
            parsed = parsed.replace(hour=18, minute=0)
        elif "morning" in message_lower:
            parsed = parsed.replace(hour=10, minute=0)
        elif "night" in message_lower:
            parsed = parsed.replace(hour=21, minute=0)

        # Localize if not already
        if parsed.tzinfo is None:
            IST = pytz.timezone("Asia/Kolkata")
            parsed = IST.localize(parsed)

        return parsed

    except Exception as e:
        print(f"❌ Error parsing fuzzy time: {e}")
        return None
