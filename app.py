import streamlit as st
import requests
import webbrowser

st.set_page_config(page_title="AI Calendar Booking")
st.title("🗓️ AI Calendar Booking Assistant")

# 👇 Your backend URL
BACKEND_URL = "https://ai-calendar-backend-r97f.onrender.com"

# 🔐 Track login/auth status
if "authorized" not in st.session_state:
    st.session_state.authorized = False

# 🔓 Login step
if not st.session_state.authorized:
    st.warning("Please login with your Google account to continue.")
    if st.button("🔐 Login with Google"):
        auth_url = f"{BACKEND_URL}/authorize"
        webbrowser.open_new_tab(auth_url)
        st.info("After login, come back and click refresh.")
    st.stop()  # 👈 Stop the app here until authorized

# 🧠 Chat history
if "chat" not in st.session_state:
    st.session_state.chat = []

# 💬 Show past chat
for role, msg in st.session_state.chat:
    st.chat_message(role).markdown(msg)

# 🗨️ User input
user_input = st.chat_input("Type your message...")
if user_input:
    st.chat_message("user").markdown(user_input)
    st.session_state.chat.append(("user", user_input))

    with st.spinner("Thinking..."):
        try:
            # 📡 Send message to backend
            response = requests.post(f"{BACKEND_URL}/chat", json={"message": user_input})
            reply = response.json().get("reply", "⚠️ Sorry, I couldn't process your request.")
        except requests.exceptions.ConnectionError:
            reply = "❌ Backend is not running or unreachable."
        except ValueError:
            reply = "⚠️ Received an invalid response from the backend."

    st.chat_message("bot").markdown(reply)
    st.session_state.chat.append(("bot", reply))
