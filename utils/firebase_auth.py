import streamlit as st
import json
from pathlib import Path
import sqlite3
from utils.rbac import (
    init_roles_and_users, authenticate_user, create_user, 
    get_all_users, delete_user, update_user_role, log_action
)

# Initialize roles and users on first run
init_roles_and_users()

def _get_session_db():
    """Get connection to session database"""
    conn = sqlite3.connect("pest_management.db")
    conn.row_factory = sqlite3.Row
    return conn

def _init_session_table():
    """Initialize session storage table"""
    conn = _get_session_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            user_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(username)
        )
    """)
    conn.commit()
    conn.close()

def _save_session(username, user_data):
    """Save user session to database"""
    conn = _get_session_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO user_sessions (username, user_data)
        VALUES (?, ?)
    """, (username, json.dumps(user_data)))
    conn.commit()
    conn.close()

def _get_saved_session(username):
    """Retrieve saved user session from database"""
    conn = _get_session_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_data FROM user_sessions WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None

def _clear_session(username):
    """Clear user session from database"""
    conn = _get_session_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_sessions WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def initialize_auth_session():
    """Initialize session state for authentication"""
    _init_session_table()
    
    if "user" not in st.session_state:
        st.session_state.user = None
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    # Try to restore session from database if no user is loaded
    if not st.session_state.authenticated and st.session_state.user is None:
        # Check if there's a saved session in browser via query param or cookie
        query_params = st.query_params
        if "user" in query_params:
            username = query_params.get("user")
            saved_user = _get_saved_session(username)
            if saved_user:
                st.session_state.user = saved_user
                st.session_state.authenticated = True

def is_authenticated():
    """Check if user is authenticated"""
    return st.session_state.get("authenticated", False)

def get_current_user():
    """Get current authenticated user"""
    return st.session_state.get("user", None)

def display_auth_ui():
    """Display Firebase authentication UI with RBAC"""
    st.set_page_config(
        page_title="RiceProTek - Login",
        page_icon="🐛",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    st.markdown("""
        <style>
        /* Hide sidebar on login page */
        [data-testid="stSidebar"] {
            display: none !important;
        }
        
        body {
            background: linear-gradient(135deg, #2E7D32 0%, #1B5E20 100%);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        .login-container {
            max-width: 480px;
            margin: 5vh auto;
            padding: 3rem 2.5rem;
            background-color: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }
        
        .login-header {
            text-align: center;
            font-size: 2.5em;
            font-weight: 700;
            background: linear-gradient(135deg, #2E7D32 0%, #1B5E20 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
        }
        
        .login-subtitle {
            text-align: center;
            font-size: 1rem;
            color: #666;
            margin-bottom: 2rem;
            font-weight: 500;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            border-bottom: 2px solid #e0e0e0;
            gap: 15px;
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            color: #666;
            border-bottom: 3px solid transparent;
            transition: all 0.3s ease;
        }
        
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: #2E7D32;
            border-bottom-color: #2E7D32;
        }
        
        .stButton > button {
            width: 100%;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            border-radius: 10px;
            border: none;
            background: linear-gradient(135deg, #2E7D32 0%, #1B5E20 100%);
            color: white;
            transition: all 0.3s ease;
            font-size: 1em;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 30px rgba(46, 125, 50, 0.3);
        }
        
        .stTextInput > div > div > input {
            border-radius: 10px;
            border: 1px solid #e0e0e0;
            padding: 0.75rem;
            font-size: 0.95em;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #2E7D32;
            box-shadow: 0 0 0 3px rgba(46, 125, 50, 0.1);
        }
        
        .stAlert {
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
            border-left: 4px solid;
        }
        
        .demo-btn {
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            text-align: center;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            border: none;
            background-color: #f0f2f6;
            color: #2E7D32;
        }
        
        .demo-btn:hover {
            background-color: #2E7D32;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Show logo
    logo_path = Path(__file__).parent.parent / "riceprotek_icon.png"
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if logo_path.exists():
            st.image(str(logo_path), width=140)
        else:
            st.warning(f"⚠️ Logo not found at {logo_path}")
    
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-header">🌾 RiceProTek 🌾</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-subtitle">Insect Pest Management System</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # Auth tabs
    tab1, tab2, tab3 = st.tabs(["🔓 Login", "📝 Sign Up", "🎯 Demo"])
    
    # LOGIN TAB
    with tab1:
        st.write("")
        login_username = st.text_input("Username", key="login_username", placeholder="Enter your username")
        login_password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")
        
        st.write("")
        if st.button("🔓 Login", use_container_width=True, type="primary"):
            if login_username and login_password:
                user_info = authenticate_user(login_username, login_password)
                
                if user_info:
                    st.session_state.user = user_info
                    st.session_state.authenticated = True
                    _save_session(login_username, user_info)
                    st.success(f"✅ Welcome {user_info['username']}!")
                    log_action(login_username, 'LOGIN', f'User logged in as {user_info["role"]}')
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")
            else:
                st.error("❌ Please enter username and password")
    
    # SIGN UP TAB
    with tab2:
        st.write("")
        st.info("ℹ️ Only Super Admin and Admin can create new users from the Settings page.")
        
        st.markdown("### Demo Accounts:")
        st.code("""
👑 Super Admin:
   Username: 18markian
   Password: admin123

📝 Encoder:
   Username: encoder1
   Password: encoder123

📊 Analyst:
   Username: analyst1
   Password: analyst123
        """)
    
    # DEMO TAB
    with tab3:
        st.write("")
        st.info("👇 Quick access with demo credentials")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("👑 Super Admin", use_container_width=True):
                user_info = authenticate_user("18markian", "admin123")
                if user_info:
                    st.session_state.user = user_info
                    st.session_state.authenticated = True
                    _save_session("18markian", user_info)
                    st.success("✅ Logged in as Super Admin!")
                    st.rerun()
        
        with col2:
            if st.button("📝 Encoder", use_container_width=True):
                user_info = authenticate_user("encoder1", "encoder123")
                if user_info:
                    st.session_state.user = user_info
                    st.session_state.authenticated = True
                    _save_session("encoder1", user_info)
                    st.success("✅ Logged in as Encoder!")
                    st.rerun()
        
        with col3:
            if st.button("📊 Analyst", use_container_width=True):
                user_info = authenticate_user("analyst1", "analyst123")
                if user_info:
                    st.session_state.user = user_info
                    st.session_state.authenticated = True
                    _save_session("analyst1", user_info)
                    st.success("✅ Logged in as Analyst!")
                    st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_user_profile():
    """Display user profile in sidebar with role badge"""
    user = get_current_user()
    
    if user:
        with st.sidebar:
            st.divider()
            st.markdown("### 👤 User Profile")
            
            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown("👤")
            
            with col2:
                st.write(f"**{user['username']}**")
                
                # Role badge with color
                role_colors = {
                    'super_admin': '👑 Super Admin',
                    'admin': '⚙️ Admin',
                    'encoder': '📝 Encoder',
                    'analyst': '📊 Analyst'
                }
                
                role_badge = role_colors.get(user['role'], user['role'])
                st.caption(role_badge)
            
            st.divider()
            
            if st.button("🚪 Logout", use_container_width=True, key="logout_btn"):
                log_action(user['username'], 'LOGOUT', 'User logged out')
                _clear_session(user['username'])
                st.session_state.user = None
                st.session_state.authenticated = False
                st.success("✅ Logged out successfully!")
                st.rerun()

