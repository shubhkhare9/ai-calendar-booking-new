from datetime import datetime, timedelta
import re
from dateutil import parser as dateutil_parser

def extract_datetime(user_input):
    try:
        # Just try to parse the string as a date
        dt = dateutil_parser.parse(user_input, fuzzy=True)
        if dt.hour == 0 and dt.minute == 0:
            dt = dt.replace(hour=10, minute=0)
        end = dt + timedelta(minutes=30)
        return dt, end
    except Exception as e:
        print("⛔ Error:", e)
        return None, None

# Test with a working phrase
inputs = [
    "1 July at 3 PM",
    "next Monday",
    "this Friday",
    "tomorrow",
    "Saturday",
    "2 July"
]

for input_text in inputs:
    print(f"Testing: {input_text}")
    start, end = extract_datetime(input_text)
    if start:
        print("✅ Start:", start)
        print("✅ End:  ", end)
    else:
        print("❌ Failed to parse.\n")
