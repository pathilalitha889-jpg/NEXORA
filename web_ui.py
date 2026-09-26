
import os
import json
import streamlit as st

os.environ["NEXORA_UI"] = "1"

try:
    if "OPENAI_API_KEY" in st.secrets:
       os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

    if "EMAIL_ADDRESS" in st.secrets:
        os.environ["EMAIL_ADDRESS"] = st.secrets["EMAIL_ADDRESS"]

    if "EMAIL_APP_PASSWORD" in st.secrets:
        os.environ["EMAIL_APP_PASSWORD"] = st.secrets["EMAIL_APP_PASSWORD"]

    if "GOOGLE_TOKEN_JSON" in st.secrets:
        with open("token.json", "w", encoding="utf-8") as f:
            f.write(st.secrets["GOOGLE_TOKEN_JSON"])
    if "GOOGLE_CREDENTIALS_JSON" in st.secrets:
        with open("credentials.json", "w", encoding="utf-8") as f:
           f.write(st.secrets["GOOGLE_CREDENTIALS_JSON"])

except Exception:
    pass

import agent
# -------------------------------------------------
# GOOGLE LOGIN
# -------------------------------------------------

LOCAL_MODE = os.getenv("NEXORA_LOCAL", "0") == "1"

if not LOCAL_MODE:

    try:
        logged_in = st.user.is_logged_in
    except (AttributeError, KeyError):
        logged_in = False

    if not logged_in:

        st.markdown("## 🔐 Welcome to NEXORA")
        st.write("Please sign in with your Google account to continue.")

        if st.button(
            "🔵 Continue with Google",
            type="primary",
            use_container_width=True
        ):
            st.login()

        st.stop()

# Logged-in user
with st.sidebar:

    if not LOCAL_MODE:

        st.success(
            f"Signed in as {st.user.email}"
        )

        if st.button(
            "Logout",
            use_container_width=True
        ):
            st.logout()
st.set_page_config(
    page_title="NEXORA",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------

if "rag_file_path" not in st.session_state:
    st.session_state["rag_file_path"] = None

if "pending_action" not in st.session_state:
    st.session_state["pending_action"] = None

if "pending_command" not in st.session_state:
    st.session_state["pending_command"] = ""

if "last_response" not in st.session_state:
    st.session_state["last_response"] = ""

# -------------------------------------------------
# STYLES
# -------------------------------------------------

st.markdown("""
<style>

.stApp {
    background: #050505;
    color: #ffffff;
}

.main {
    background: #050505;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

/* Header */

.nexora-title {
    font-size: 44px;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 4px;
}

.nexora-subtitle {
    font-size: 18px;
    color: #9ca3af;
    margin-bottom: 28px;
}

/* Feature cards */

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #111111;
    border: 1px solid #262626;
    border-radius: 16px;
}

/* Text */

h1, h2, h3, h4, h5, h6 {
    color: #ffffff !important;
}

p, label {
    color: #d1d5db !important;
}

/* Text area */

textarea {
    background-color: #111111 !important;
    color: #ffffff !important;
    border: 1px solid #333333 !important;
}

/* File uploader */

section[data-testid="stFileUploaderDropzone"] {
    background: #111111;
    border: 1px dashed #444444;
}

/* Sidebar */

section[data-testid="stSidebar"] {
    background: #080808;
}

section[data-testid="stSidebar"] * {
    color: #eeeeee;
}

/* Buttons */

.stButton > button {
    border-radius: 10px;
    font-weight: 600;
}

/* Divider */

hr {
    border-color: #262626;
}

/* Success / warning / error */

div[data-testid="stAlert"] {
    border-radius: 12px;
}

/* Footer */

.nexora-footer {
    text-align: center;
    color: #666666;
    padding: 20px;
    font-size: 13px;
}

</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------

with st.sidebar:
    st.markdown("## 🤖 NEXORA")
    st.caption("Intelligent Multi-Tool AI Agent")

    st.divider()

    st.markdown("### 🛠️ Tools")
    st.write("📅 Calendar")
    st.write("📧 Gmail")
    st.write("📝 Tasks")
    st.write("🧠 Memory")
    st.write("📚 RAG")

    st.divider()

    st.caption(
        "NEXORA understands natural language "
        "and selects the required tool automatically."
    )

# -------------------------------------------------
# HEADER
# -------------------------------------------------

st.markdown(
    '<div class="nexora-title">🤖 NEXORA</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="nexora-subtitle">'
    'Your intelligent multi-tool AI agent'
    '</div>',
    unsafe_allow_html=True
)

# -------------------------------------------------
# FEATURES
# -------------------------------------------------

st.markdown("## What can NEXORA do?")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    with st.container(border=True):
        st.markdown("### 📅")
        st.markdown("**Calendar**")
        st.caption("Create meetings")

with col2:
    with st.container(border=True):
        st.markdown("### 📧")
        st.markdown("**Email**")
        st.caption("Send Gmail")

with col3:
    with st.container(border=True):
        st.markdown("### 📝")
        st.markdown("**Tasks**")
        st.caption("Manage tasks")

with col4:
    with st.container(border=True):
        st.markdown("### 🧠")
        st.markdown("**Memory**")
        st.caption("Remember things")

with col5:
    with st.container(border=True):
        st.markdown("### 📚")
        st.markdown("**PDF**")
        st.caption("Read documents")

st.divider()

# -------------------------------------------------
# COMMAND INPUT
# -------------------------------------------------

st.markdown("## 💬 Talk to NEXORA")

command = st.text_area(
    "What would you like me to do?",
    placeholder=(
        "Example: Schedule a meeting with Ravi tomorrow at 10 AM\n"
        "Example: Send an email to someone@example.com\n"
        "Example: Remember that my interview is next Monday\n"
        "Example: What does the uploaded document say?"
    ),
    height=120,
    key="command_input"
)

# -------------------------------------------------
# DOCUMENT UPLOAD
# -------------------------------------------------

with st.expander("📎 Upload a PDF "):

    uploaded_file = st.file_uploader(
        "Choose PDF, DOCX or TXT",
        type=["pdf", "docx", "txt"]
    )

    if uploaded_file:

        os.makedirs("uploads", exist_ok=True)

        file_path = os.path.join(
            "uploads",
            uploaded_file.name
        )

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.session_state["rag_file_path"] = file_path

        st.success(
            f"Uploaded: {uploaded_file.name}"
        )

# -------------------------------------------------
# AGENT FUNCTION
# -------------------------------------------------
def run_agent(command):

    google_access_token = None

    try:
        if st.user.is_logged_in and "access" in st.user.tokens:
            google_access_token = st.user.tokens["access"]
    except Exception:
        google_access_token = None

    result = agent.app.invoke(
        {
            "command": command,
            "action": "",
            "result": "",
            "file_path": st.session_state.get(
                "rag_file_path"
            ),
            "permission_granted": False,
            "google_access_token": google_access_token
        }
    )

    return result
# -------------------------------------------------
# RUN NEXORA
# -------------------------------------------------

if st.button(
    "🚀 Run NEXORA",
    type="primary",
    use_container_width=True
):

    if not command.strip():

        st.warning(
            "Please enter a command."
        )

    else:

        with st.spinner(
            "NEXORA is thinking..."
        ):

            try:

                result = run_agent(command)

                action = result.get(
                    "action",
                    ""
                )

                response = result.get(
                    "result",
                    "No response."
                )

                # -----------------------------------------
                # EMAIL PERMISSION REQUIRED
                # -----------------------------------------

                if action == "SEND_EMAIL":

                    st.session_state["pending_action"] = "SEND_EMAIL"
                    st.session_state["pending_command"] = command
                    st.session_state["last_response"] = ""

                # -----------------------------------------
                # CALENDAR PERMISSION REQUIRED
                # -----------------------------------------

                elif action == "MEETING":

                    st.session_state["pending_action"] = "MEETING"
                    st.session_state["pending_command"] = command
                    st.session_state["last_response"] = ""

                # -----------------------------------------
                # NORMAL RESPONSE
                # -----------------------------------------

                else:

                    st.session_state["last_response"] = response

            except Exception as e:

                st.error(
                    f"NEXORA error: {e}"
                )

# -------------------------------------------------
# PENDING PERMISSION UI
# -------------------------------------------------

pending_action = st.session_state.get(
    "pending_action"
)

pending_command = st.session_state.get(
    "pending_command",
    ""
)

# -------------------------------------------------
# EMAIL PERMISSION
# -------------------------------------------------

if pending_action == "SEND_EMAIL":

    st.divider()

    st.warning(
        "🔐 Permission required before sending email."
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "✅ Allow",
            use_container_width=True,
            key="permission_allow_email"
        ):

            try:


                result = agent.app.invoke(
    {
        "command": command,
        "action": "SEND_EMAIL",
        "result": "",
        "file_path": st.session_state.get(
            "rag_file_path"
        ),
        "permission_granted": True,
        "google_access_token": st.user.tokens["access"]
    }
)


                email_response = result.get(
                    "result",
                    "Email sent successfully!"
                )

                if email_response == "PERMISSION_REQUIRED":

                    st.error(
                        "Permission was not granted."
                    )

                else:

                    st.success(
                        email_response
                    )

                    st.session_state["pending_action"] = None
                    st.session_state["pending_command"] = ""

            except Exception as e:

                st.error(
                    f"Email error: {e}"
                )

    with col2:

        if st.button(
            "❌ Deny",
            use_container_width=True,
            key="permission_deny_email"
        ):

            st.error(
                "Action cancelled by user."
            )

            st.session_state["pending_action"] = None
            st.session_state["pending_command"] = ""

# -------------------------------------------------
# CALENDAR PERMISSION
# -------------------------------------------------

if pending_action == "MEETING":

    st.divider()

    st.warning(
        "🔐 Permission required before creating calendar event."
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "✅ Allow",
            use_container_width=True,
            key="permission_allow_meeting"
        ):

            try:


                result = agent.app.invoke(
    {
        "command": command,
        "action": "MEETING",
        "result": "",
        "file_path": st.session_state.get(
            "rag_file_path"
        ),
        "permission_granted": True,
        "google_access_token": st.user.tokens["access"]
    }
)

                meeting_response = result.get(
                    "result",
                    "Meeting created successfully!"
                )

                if meeting_response == "PERMISSION_REQUIRED":

                    st.error(
                        "Permission was not granted."
                    )

                else:

                    st.success(
                        meeting_response
                    )

                    st.session_state["pending_action"] = None
                    st.session_state["pending_command"] = ""

            except Exception as e:

                st.error(
                    f"Calendar error: {e}"
                )

    with col2:

        if st.button(
            "❌ Deny",
            use_container_width=True,
            key="permission_deny_meeting"
        ):

            st.error(
                "Action cancelled by user."
            )

            st.session_state["pending_action"] = None
            st.session_state["pending_command"] = ""

# -------------------------------------------------
# LAST RESPONSE
# -------------------------------------------------

last_response = st.session_state.get(
    "last_response",
    ""
)

if last_response:

    st.divider()

    st.markdown(
        "## 🤖 NEXORA Response"
    )

    with st.container(border=True):

        st.write(
            last_response
        )

# -------------------------------------------------
# FOOTER
# -------------------------------------------------

st.divider()

st.markdown(
    '<div class="nexora-footer">'
    'NEXORA • Intelligent Multi-Tool AI Agent'
    '</div>',
    unsafe_allow_html=True
)