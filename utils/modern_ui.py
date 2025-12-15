"""Modern UI styling utilities for Streamlit app"""
import streamlit as st

def apply_modern_theme():
    """Apply modern theme styling to Streamlit app"""
    st.markdown("""
    <style>
    /* Global Styles */
    * {
        box-sizing: border-box;
    }
    
    /* Main container */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Headers */
    h1 { font-weight: 800 !important; }
    h2 { font-weight: 700 !important; margin-top: 30px !important; }
    h3 { font-weight: 600 !important; }
    
    /* Buttons */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15) !important;
    }
    
    /* Input fields */
    .stTextInput, .stNumberInput, .stSelectbox, .stMultiSelect {
        border-radius: 10px !important;
    }
    
    /* Dataframe */
    .streamlit-dataframe {
        border-radius: 12px !important;
        overflow: hidden !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] button {
        border-radius: 10px 10px 0 0 !important;
        font-weight: 600 !important;
    }
    
    /* Divider */
    .stDivider {
        margin: 30px 0 !important;
    }
    
    /* Info/Warning/Error boxes */
    .stInfo, .stWarning, .stError, .stSuccess {
        border-radius: 12px !important;
    }
    </style>
    """, unsafe_allow_html=True)

def metric_card(title, value, icon, color, description=""):
    """Create a modern metric card"""
    return f"""
    <div style='background: linear-gradient(135deg, {color}15 0%, white 100%); 
                border-radius: 15px; padding: 25px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
                border-top: 3px solid {color}; transition: transform 0.3s;'>
        <div style='font-size: 2.8em; margin-bottom: 10px;'>{icon}</div>
        <h3 style='font-size: 2.2em; font-weight: 700; margin: 0; color: {color};'>{value}</h3>
        <p style='font-size: 0.95em; color: #64748b; font-weight: 500; margin-top: 10px; margin-bottom: 0;'>{title}</p>
        {f"<p style='font-size: 0.85em; color: #94a3b8; margin-top: 8px;'>{description}</p>" if description else ""}
    </div>
    """

def info_box(title, content_dict, icon, color):
    """Create a modern info box with multiple stats"""
    content_html = ""
    for key, value in content_dict.items():
        content_html += f"<div><p style='color: #64748b; margin: 0 0 5px 0; font-size: 0.9em;'>{key}</p><p style='color: {color}; margin: 0; font-size: 1.8em; font-weight: 700;'>{value}</p></div>"
    
    return f"""
    <div style='background: linear-gradient(135deg, {color}10 0%, white 100%); 
                border-radius: 15px; padding: 25px; border-left: 5px solid {color};'>
        <h4 style='color: {color}; margin-bottom: 20px; font-weight: 700; font-size: 1.1em;'>{icon} {title}</h4>
        <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 15px;'>
            {content_html}
        </div>
    </div>
    """

def gradient_header(title, subtitle, color1="#667eea", color2="#764ba2"):
    """Create a modern gradient header"""
    return f"""
    <div style='padding: 30px; border-radius: 15px; background: linear-gradient(135deg, {color1} 0%, {color2} 100%); color: white; margin-bottom: 30px;'>
        <h1 style='margin: 0; font-size: 2.8em; font-weight: 800;'>{title}</h1>
        <p style='margin: 10px 0 0 0; font-size: 1.1em; opacity: 0.95;'>{subtitle}</p>
    </div>
    """
