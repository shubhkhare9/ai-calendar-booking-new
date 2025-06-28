import streamlit as st
import requests

st.title("🗓️ Calendar Booking Assistant")

if "chat" not in st.session_state:
    st.session_state.chat = []

# Display chat history
for role, msg in st.session_state.chat:
    st.chat_message(role).markdown(msg)

user_input = st.chat_input("Type your message...")
if user_input:
    st.chat_message("user").markdown(user_input)
    st.session_state.chat.append(("user", user_input))
    
    with st.spinner("Thinking..."):
        try:
            response = requests.post("http://localhost:8000/chat", json={"message": user_input})
            reply = response.json().get("reply", "⚠️ Sorry, I couldn't process your request.")
        except requests.exceptions.ConnectionError:
            reply = "❌ Backend is not running. Please start FastAPI with `uvicorn main:app --reload`."
        except ValueError:
            reply = "⚠️ Received an invalid response from the backend."

    st.chat_message("bot").markdown(reply)
    st.session_state.chat.append(("bot", reply))
