import streamlit as st
import os
import json
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.id_token import verify_oauth2_token
import base64

# Load credentials from client_secret.json
def load_client_secret():
    """Load Google OAuth credentials from client_secret.json"""
    secret_path = Path(__file__).parent.parent / "client_secret.json"
    if secret_path.exists():
        with open(secret_path, 'r') as f:
            return json.load(f).get('web', {})
    return {}

CLIENT_CONFIG = load_client_secret()
GOOGLE_CLIENT_ID = CLIENT_CONFIG.get('client_id', '')
GOOGLE_CLIENT_SECRET = CLIENT_CONFIG.get('client_secret', '')

def initialize_session():
    """Initialize session state for authentication"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_info" not in st.session_state:
        st.session_state.user_info = None

def check_authentication():
    """Check if user is authenticated"""
    return st.session_state.get("authenticated", False)

def login_with_google():
    """Display Google Login UI and handle authentication"""
    st.set_page_config(
        page_title="RiceProTek - Login",
        page_icon="🐛",
        layout="centered"
    )
    
    st.markdown("""
        <style>
        body {
            background-color: #f5f5f5;
        }
        .login-container {
            display:none;
            max-width: 450px;
            margin: 0 auto;
            padding: 50px 40px;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .login-header {
            text-align: center;
            font-size: 2em;
            font-weight: bold;
            color: #2E7D32;
            margin-bottom: 20px;
        }
        .login-subtitle {
            text-align: center;
            font-size: 1.1em;
            color: #666;
            margin-bottom: 40px;
        }
        .google-button {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            padding: 12px;
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 1em;
            cursor: pointer;
            transition: box-shadow 0.2s;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .google-button:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        .divider {
            text-align: center;
            margin: 30px 0 20px;
            font-size: 0.9em;
            color: #999;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Show logo if available
    logo_path = Path(__file__).parent.parent / "riceprotek_icon.png"
    if logo_path.exists():
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.image(str(logo_path), width=120)
    
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-header">RiceProTek</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-subtitle">Insect Pest Management System</div>', unsafe_allow_html=True)
    
    st.divider()
    
    st.markdown("### Welcome!")
    st.write("Sign in to access the pest management dashboard")
    
    st.markdown('<div class="divider">Sign in with your Google Account</div>', unsafe_allow_html=True)
    
    # Demo Login Option for Testing
    st.info("**Demo Mode:** Click the button below to proceed with demo access (for testing)")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔓 Demo Login", use_container_width=True, type="primary"):
            st.session_state.authenticated = True
            st.session_state.user_info = {
                "email": "demo@riceprotek.com",
                "name": "Demo User",
                "picture": None
            }
            st.success("✅ Logged in as Demo User!")
            st.rerun()
    
    st.divider()
    
    # Google OAuth Info
    if GOOGLE_CLIENT_ID:
        st.markdown(f"""
        **Google Sign-In Available**
        
        Client ID: `{GOOGLE_CLIENT_ID[:20]}...`
        
        To enable full Google authentication:
        1. Open [Google OAuth Console](https://myaccount.google.com/security)
        2. Authorize this application
        3. You'll be redirected back to RiceProTek
        """)
    else:
        st.error("❌ Google credentials not found in client_secret.json")
    
    st.markdown('</div>', unsafe_allow_html=True)

def handle_google_login(token):
    """Handle Google login token verification"""
    try:
        # Verify the token
        idinfo = verify_oauth2_token(token, Request(), GOOGLE_CLIENT_ID)
        
        # Token is valid, store user info
        st.session_state.authenticated = True
        st.session_state.user_info = {
            "email": idinfo.get("email"),
            "name": idinfo.get("name"),
            "picture": idinfo.get("picture")
        }
        
        return True
    except Exception as e:
        st.error(f"Authentication failed: {str(e)}")
        return False

def logout():
    """Handle user logout"""
    st.session_state.authenticated = False
    st.session_state.user_info = None

def display_user_info():
    """Display authenticated user information in sidebar"""
    if st.session_state.user_info:
        with st.sidebar:
            st.divider()
            st.markdown("### 👤 User")
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if st.session_state.user_info.get("picture"):
                    st.image(st.session_state.user_info["picture"], width=40)
                else:
                    st.markdown("👤")
            
            with col2:
                st.write(f"**{st.session_state.user_info.get('name', 'User')}**")
                st.caption(st.session_state.user_info.get('email', 'No email'))
            
            if st.button("🚪 Logout", use_container_width=True):
                logout()
                st.rerun()


