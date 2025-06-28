import requests

try:
	res = requests.post("http://localhost:8000/chat", json={"message": "Book a meeting on 2023-10-12 at 15:00"})
	res.raise_for_status()  # Raise an error for HTTP codes 4xx/5xx
	print(res.json())
except requests.exceptions.RequestException as e:
	print(f"An error occurred: {e}")
