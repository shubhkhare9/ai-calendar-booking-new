import dateparser

text = "Book a meeting tomorrow at 3 PM"
dt = dateparser.parse(text, settings={"PREFER_DATES_FROM": "future"})

print("Parsed datetime:", dt)

