import streamlit as st
import requests
import webbrowser

st.title("🗓️ Calendar Booking Assistant")
BACKEND_URL = "https://ai-calendar-backend-r97f.onrender.com"

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
            response = requests.post(f"{BACKEND_URL}/chat", json={"message": user_input})
            reply = response.json().get("reply", "⚠️ Sorry, I couldn't process your request.")
            
            if "User not authenticated" in reply:
                st.warning("🔐 Please log in to Google to proceed.")
                auth_url = f"{BACKEND_URL}/authorize"
                st.markdown(f"[Click here to log in]({auth_url})", unsafe_allow_html=True)
        except requests.exceptions.ConnectionError:
            reply = "❌ Backend not reachable. Please check if it's deployed."
        except ValueError:
            reply = "⚠️ Received an invalid response from the backend."

    st.chat_message("bot").markdown(reply)
    st.session_state.chat.append(("bot", reply))
