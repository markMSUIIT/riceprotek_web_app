import streamlit as st
import pandas as pd
import numpy as np
import io
from utils.database import (
    init_database, create_record, read_records, 
    update_record, delete_record, get_record_by_id, 
    get_table_columns, load_csv_to_db
)
from utils.firebase_auth import initialize_auth_session, is_authenticated, display_auth_ui, display_user_profile, get_current_user
from utils.rbac import can_manage_users, can_encode_data, can_view_analytics, log_action, init_roles_and_users
from utils.data_processing import (
    process_pest_data, get_summary_statistics, 
    get_temporal_aggregation, detect_outliers,
    filter_by_area, get_available_areas, get_area_summary, compare_areas
)
from utils.visualizations import (
    create_pest_trend_chart, create_comparison_chart,
    create_scatter_plot, create_distribution_chart,
    create_heatmap, create_environmental_comparison,
    create_area_comparison_chart, create_area_trend_chart, create_area_heatmap
)
from pathlib import Path
from datetime import datetime


# Initialize Firebase authentication session
initialize_auth_session()

# Check if user is authenticated
if not is_authenticated():
    display_auth_ui()
    st.stop()

# Page configuration (only after authentication)
st.set_page_config(
    page_title="RiceProTek Insect Pest Management",
    page_icon="🐛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar - Logo and Navigation
st.sidebar.image("riceprotek_icon.png", use_container_width=True)
st.sidebar.markdown('<div class="sidebar-header">🐛 Navigation</div>', unsafe_allow_html=True)

# Initialize database
init_database()

# Initialize roles and users
init_roles_and_users()

# Modern custom styling
st.markdown("""
    <style>
    * {
        margin: 0;
        padding: 0;
    }
    
    /* Main container */
    .main {
        padding: 2rem;
    }
    
    /* Headers */
    .main-header {
        font-size: 2.8em;
        font-weight: 700;
        background: linear-gradient(135deg, #2E7D32 0%, #1B5E20 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 2rem;
        letter-spacing: -0.5px;
    }
    
    h1, h2, h3 {
        color: #1B5E20;
        font-weight: 700;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f5f7fa 100%);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        border-left: 4px solid #2E7D32;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
        transform: translateY(-2px);
    }
    
    /* Sidebar styling */
    .sidebar-header {
        font-size: 1.4em;
        font-weight: 700;
        color: #1B5E20;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #2E7D32;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 0.75rem 1.5rem;
        background-color: #f0f2f6;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #2E7D32 0%, #1B5E20 100%);
        color: white;
    }
    
    /* Buttons */
    .stButton > button {
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        border-radius: 8px;
        border: none;
        transition: all 0.3s ease;
        background: linear-gradient(135deg, #2E7D32 0%, #1B5E20 100%);
        color: white;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(46, 125, 50, 0.3);
    }
    
    /* Info boxes */
    .stAlert {
        border-radius: 10px;
        padding: 1.25rem;
        border-left: 4px solid #2E7D32;
    }
    
    /* Dividers */
    hr {
        border-color: #e0e0e0;
        margin: 1.5rem 0;
    }
    
    /* Data frames */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select,
    .stMultiSelect > div > div > div {
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        padding: 0.75rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #2E7D32;
        box-shadow: 0 0 0 3px rgba(46, 125, 50, 0.1);
    }
    
    /* Cards with shadows */
    .card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        margin-bottom: 1.5rem;
    }
    </style>
""", unsafe_allow_html=True)


user = get_current_user()

# Build navigation menu based on role
nav_options = ["Dashboard", "Area Analysis", "Pest Records", "Monitoring Points", "NASA POWER Data", "Analytics", "Settings"]

# Add User Management for super_admin and admin only
if user and can_manage_users(user):
    nav_options.insert(3, "User Management")
    nav_options.insert(4, "Insects Management")

page = st.sidebar.radio(
    "Select a section:",
    nav_options,
    label_visibility="collapsed"
)

# Display user profile
display_user_profile()

# Modern Main header with logo
# st.markdown("""
#     <div style="text-align: center; margin-bottom: 2rem;">
#         <div style="background: linear-gradient(135deg, #2E7D32 0%, #1B5E20 100%); padding: 2rem; border-radius: 15px; box-shadow: 0 8px 30px rgba(0,0,0,0.15);">
#             <h1 style="color: white; font-size: 2.5em; margin: 0; font-weight: 700;">🐛 RiceProTek</h1>
#             <p style="color: rgba(255,255,255,0.9); font-size: 1.1em; margin-top: 0.5rem; margin-bottom: 0;">Insect Pest Management System</p>
#         </div>
#     </div>
# """, unsafe_allow_html=True)

# ============================================================================
# DASHBOARD PAGE - Accessible to all roles
# ============================================================================
if page == "Dashboard":
    # Modern header
    st.markdown("""
    <div style='padding: 30px; border-radius: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; margin-bottom: 30px;'>
        <h1 style='margin: 0; font-size: 2.8em; font-weight: 800;'>🐛 RiceProTek Dashboard</h1>
        <p style='margin: 10px 0 0 0; font-size: 1.1em; opacity: 0.95;'>Real-time pest management monitoring system</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get current user info
    current_user = get_current_user()
    user_name = current_user.get('name', 'Administrator') if current_user else 'User'
    
    # Load data
    pest_df = read_records("pest_records")
    monitoring_points_df = read_records("monitoring_points")
    
    # Key Statistics Cards - Enhanced
    st.markdown("""
    <div style='padding: 20px; border-radius: 15px; background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);'>
        <h3 style='margin-top: 0; color: #111827;'>📊 Key Metrics</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
            <div style='padding: 20px; border-radius: 12px; background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%); border-top: 4px solid #1e3a8a;'>
                <p style='margin: 0; color: #e0e7ff; font-size: 0.85em;'>Total Pest Records</p>
                <h2 style='margin: 10px 0 0 0; color: white; font-size: 2.5em; font-weight: 800;'>{len(pest_df)}</h2>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div style='padding: 20px; border-radius: 12px; background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); border-top: 4px solid #92400e;'>
                <p style='margin: 0; color: #fef3c7; font-size: 0.85em;'>Monitoring Points</p>
                <h2 style='margin: 10px 0 0 0; color: white; font-size: 2.5em; font-weight: 800;'>{len(monitoring_points_df)}</h2>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div style='padding: 20px; border-radius: 12px; background: linear-gradient(135deg, #ec4899 0%, #db2777 100%); border-top: 4px solid #831843;'>
                <p style='margin: 0; color: #fbcfe8; font-size: 0.85em;'>System Status</p>
                <h2 style='margin: 10px 0 0 0; color: white; font-size: 2.5em; font-weight: 800;'>🟢 Active</h2>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    # System Overview Section
    st.markdown("""
    <div style='padding: 20px; border-radius: 15px; background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);'>
        <h3 style='margin-top: 0; color: #111827;'>📈 System Overview</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        if len(pest_df) > 0:
            pest_df_processed = process_pest_data(pest_df)
            summary_stats = get_summary_statistics(pest_df_processed, 'rbb_count')
            
            total_rbb = pest_df['rbb_count'].sum() if 'rbb_count' in pest_df.columns else 0
            total_wsb = pest_df['wsb_count'].sum() if 'wsb_count' in pest_df.columns else 0
            
            st.markdown(f"""
                <div style='padding: 20px; border-radius: 12px; background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); border-left: 4px solid #0284c7;'>
                    <h4 style='color: #0c4a6e; margin: 0 0 15px 0;'>🐛 Pest Summary</h4>
                    <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 10px;'>
                        <div><p style='margin: 0; color: #0c4a6e; font-size: 0.9em;'><strong>RBB Count:</strong></p><p style='margin: 5px 0 0 0; color: #0284c7; font-size: 1.3em; font-weight: 700;'>{int(total_rbb)}</p></div>
                        <div><p style='margin: 0; color: #0c4a6e; font-size: 0.9em;'><strong>WSB Count:</strong></p><p style='margin: 5px 0 0 0; color: #0284c7; font-size: 1.3em; font-weight: 700;'>{int(total_wsb)}</p></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info("📌 No pest records available yet. Start by adding data in the Pest Records section.")
    
    with info_col2:
        if len(monitoring_points_df) > 0:
            st.markdown(f"""
                <div style='padding: 20px; border-radius: 12px; background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); border-left: 4px solid #059669;'>
                    <h4 style='color: #064e3b; margin: 0 0 15px 0;'>📍 Monitoring Coverage</h4>
                    <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 10px;'>
                        <div><p style='margin: 0; color: #064e3b; font-size: 0.9em;'><strong>Active Points:</strong></p><p style='margin: 5px 0 0 0; color: #059669; font-size: 1.3em; font-weight: 700;'>{len(monitoring_points_df)}</p></div>
                        <div><p style='margin: 0; color: #064e3b; font-size: 0.9em;'><strong>Status:</strong></p><p style='margin: 5px 0 0 0; color: #059669; font-size: 1em; font-weight: 600;'>✓ Ready</p></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info("📌 No monitoring points configured. Add monitoring points to begin environmental tracking.")
    
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    # Quick Actions
    st.markdown("""
    <div style='padding: 20px; border-radius: 15px; background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);'>
        <h3 style='margin-top: 0; color: #111827;'>⚡ Quick Actions</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    
    quick_col1, quick_col2, quick_col3 = st.columns(3)
    
    with quick_col1:
        if st.button("📋 Add Pest Record", use_container_width=True, key="quick_pest"):
            st.session_state.quick_action = "pest_record"
    
    with quick_col2:
        if st.button("📍 Add Monitoring Point", use_container_width=True, key="quick_monitor"):
            st.session_state.quick_action = "monitoring_point"
    
    with quick_col3:
        if st.button("🌡️ View Environmental Data", use_container_width=True, key="quick_env"):
            st.session_state.quick_action = "environment"
    
    st.divider()

# ============================================================================
# MONITORING POINTS PAGE - Admin and Encoder only
# ============================================================================
elif page == "Monitoring Points":
    # Role-based access control
    if user['role'] not in ['super_admin', 'admin', 'encoder']:
        st.error("❌ Access Denied! Only Super Admin, Admin, and Encoder can manage monitoring points.")
        st.stop()
    
    st.header("📍 Monitoring Points Management")
    
    st.markdown("""
    Manage monitoring locations (barangays and points) for pest surveillance and data collection.
    Each point has specific coordinates for weather data correlation and pest monitoring.
    """)
    
    st.divider()
    
    from utils.database import (
        get_monitoring_points, create_monitoring_point, 
        update_monitoring_point, delete_monitoring_point,
        get_monitoring_point_by_id
    )
    import sqlite3
    
    # Create tabs for different operations
    tab1, tab2, tab3, tab4 = st.tabs(["📋 View Points", "➕ Add Point", "✏️ Edit Point", "🗑️ Delete Point"])
    
    # TAB 1: VIEW ALL MONITORING POINTS
    with tab1:
        st.subheader("All Monitoring Points")
        
        points_df = get_monitoring_points()
        
        if len(points_df) > 0:
            # Add display columns
            display_df = points_df[["id", "point_number", "municipality", "cluster", "barangay", "latitude", "longitude", "area_name"]].copy()
            display_df.columns = ["ID", "Point #", "Municipality", "Cluster", "Barangay", "Latitude", "Longitude", "Area Name"]
            
            st.dataframe(display_df, use_container_width=True, height=400)
            
            st.write("")
            
            # Summary statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Points", len(points_df))
            with col2:
                st.metric("Active Points", len(points_df[points_df["is_active"] == 1]))
            with col3:
                st.metric("Clusters", points_df["cluster"].nunique())
            with col4:
                st.metric("Barangays", points_df["barangay"].nunique())
            
            st.divider()
            
            # Cluster summary
            st.subheader("Points by Cluster")
            cluster_summary = points_df.groupby("cluster").size()
            st.bar_chart(cluster_summary)
            
            st.divider()
            
            # Download option
            csv = points_df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name="monitoring_points.csv",
                mime="text/csv"
            )
        
        else:
            st.info("ℹ️ No monitoring points found. Add one using the 'Add Point' tab.")
    
    # TAB 2: ADD NEW MONITORING POINT
    with tab2:
        st.subheader("Add New Monitoring Point")
        
        col1, col2 = st.columns(2)
        
        with col1:
            point_number = st.number_input("Point Number", min_value=1, value=1, help="Unique point identifier")
            municipality = st.text_input("Municipality", value="Midsayap")
            cluster = st.number_input("Cluster", min_value=1, value=1)
        
        with col2:
            barangay = st.text_input("Barangay", value="Central Bulanan")
            area_name = st.text_input("Area Name (Optional)", help="e.g., PhilRice (Lot 64)")
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            latitude = st.number_input("Latitude", value=7.178, format="%.6f", min_value=-90.0, max_value=90.0)
        
        with col2:
            longitude = st.number_input("Longitude", value=124.500, format="%.6f", min_value=-180.0, max_value=180.0)
        
        st.divider()
        
        notes = st.text_area("Notes (Optional)", help="Additional information about this monitoring point")
        
        st.write("")
        
        if st.button("✅ Add Monitoring Point", use_container_width=True, type="primary"):
            try:
                data = {
                    "point_number": int(point_number),
                    "municipality": municipality,
                    "cluster": int(cluster),
                    "barangay": barangay,
                    "latitude": latitude,
                    "longitude": longitude,
                    "area_name": area_name if area_name else None,
                    "notes": notes if notes else None,
                    "is_active": 1
                }
                
                point_id = create_monitoring_point(data)
                st.success(f"✅ Monitoring point added successfully! (ID: {point_id})")
                st.balloons()
                
            except Exception as e:
                st.error(f"❌ Error adding monitoring point: {str(e)}")
    
    # TAB 3: EDIT MONITORING POINT
    with tab3:
        st.subheader("Edit Monitoring Point")
        
        points_df = get_monitoring_points()
        
        if len(points_df) > 0:
            point_id = st.selectbox(
                "Select Point to Edit",
                points_df["id"].values,
                format_func=lambda x: f"Point {points_df[points_df['id']==x]['point_number'].values[0]} - {points_df[points_df['id']==x]['barangay'].values[0]}"
            )
            
            point = get_monitoring_point_by_id(point_id)
            
            if point:
                st.info(f"📍 Editing Point #{point['point_number']} - {point['barangay']}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    point_number = st.number_input("Point Number", value=point["point_number"], min_value=1, key="edit_point_num")
                    municipality = st.text_input("Municipality", value=point["municipality"], key="edit_mun")
                    cluster = st.number_input("Cluster", value=point["cluster"], min_value=1, key="edit_cluster")
                
                with col2:
                    barangay = st.text_input("Barangay", value=point["barangay"], key="edit_barangay")
                    area_name = st.text_input("Area Name", value=point.get("area_name") or "", key="edit_area_name")
                
                st.divider()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    latitude = st.number_input("Latitude", value=point["latitude"], format="%.6f", key="edit_lat")
                
                with col2:
                    longitude = st.number_input("Longitude", value=point["longitude"], format="%.6f", key="edit_lon")
                
                st.divider()
                
                notes = st.text_area("Notes", value=point.get("notes") or "", key="edit_notes")
                is_active = st.checkbox("Active", value=point.get("is_active", 1), key="edit_active")
                
                st.write("")
                
                if st.button("💾 Update Point", use_container_width=True, type="primary"):
                    try:
                        update_data = {
                            "point_number": int(point_number),
                            "municipality": municipality,
                            "cluster": int(cluster),
                            "barangay": barangay,
                            "latitude": latitude,
                            "longitude": longitude,
                            "area_name": area_name if area_name else None,
                            "notes": notes if notes else None,
                            "is_active": 1 if is_active else 0
                        }
                        
                        update_monitoring_point(point_id, update_data)
                        st.success("✅ Monitoring point updated successfully!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error updating monitoring point: {str(e)}")
        
        else:
            st.info("ℹ️ No monitoring points found to edit.")
    
    # TAB 4: DELETE MONITORING POINT
    with tab4:
        st.subheader("Delete Monitoring Point")
        
        st.warning("⚠️ Deleting a monitoring point will remove it from the system. This action cannot be undone.")
        
        points_df = get_monitoring_points()
        
        if len(points_df) > 0:
            point_id = st.selectbox(
                "Select Point to Delete",
                points_df["id"].values,
                format_func=lambda x: f"Point {points_df[points_df['id']==x]['point_number'].values[0]} - {points_df[points_df['id']==x]['barangay'].values[0]}",
                key="delete_point"
            )
            
            point = get_monitoring_point_by_id(point_id)
            
            if point:
                st.info(f"📍 Selected: Point #{point['point_number']} - {point['barangay']} ({point['municipality']})")
                st.info(f"Coordinates: {point['latitude']}, {point['longitude']}")
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    if st.button("🗑️ Confirm Delete", use_container_width=True, type="secondary"):
                        try:
                            delete_monitoring_point(point_id)
                            st.success("✅ Monitoring point deleted successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error deleting monitoring point: {str(e)}")
                
                with col2:
                    st.button("❌ Cancel", use_container_width=True)
        
        else:
            st.info("ℹ️ No monitoring points found to delete.")
    
    st.divider()
    
    # BULK IMPORT SECTION
    st.subheader("📥 Bulk Import from CSV")
    
    uploaded_file = st.file_uploader("Upload monitoring points CSV file", type="csv")
    
    if uploaded_file is not None:
        try:
            import_df = pd.read_csv(uploaded_file)
            
            st.success(f"✅ File loaded! Found {len(import_df)} rows")
            
            # Display preview
            st.subheader("Preview")
            st.dataframe(import_df.head())
            
            # Mapping configuration
            st.subheader("Column Mapping")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                pt_col = st.selectbox("Point Number Column", import_df.columns, key="pt_col")
            with col2:
                mun_col = st.selectbox("Municipality Column", import_df.columns, key="mun_col")
            with col3:
                cluster_col = st.selectbox("Cluster Column", import_df.columns, key="cluster_col")
            with col4:
                barangay_col = st.selectbox("Barangay Column", import_df.columns, key="barangay_col")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                lat_col = st.selectbox("Latitude Column", import_df.columns, key="lat_col")
            with col2:
                lon_col = st.selectbox("Longitude Column", import_df.columns, key="lon_col")
            with col3:
                area_col = st.selectbox("Area Name Column (Optional)", [None] + list(import_df.columns), key="area_col")
            
            st.write("")
            
            if st.button("📤 Import Monitoring Points", use_container_width=True, type="primary"):
                try:
                    imported_count = 0
                    skipped_count = 0
                    errors = []
                    
                    for idx, row in import_df.iterrows():
                        try:
                            data = {
                                "point_number": int(row[pt_col]),
                                "municipality": str(row[mun_col]).strip(),
                                "cluster": int(row[cluster_col]) if pd.notna(row[cluster_col]) else None,
                                "barangay": str(row[barangay_col]).strip(),
                                "latitude": float(row[lat_col]),
                                "longitude": float(row[lon_col]),
                                "area_name": str(row[area_col]).strip() if area_col and pd.notna(row[area_col]) else None,
                                "is_active": 1
                            }
                            
                            create_monitoring_point(data)
                            imported_count += 1
                        
                        except sqlite3.IntegrityError:
                            skipped_count += 1
                        except Exception as e:
                            errors.append(f"Row {idx + 1}: {str(e)}")
                    
                    st.success(f"✅ Import complete! Imported {imported_count} points, Skipped {skipped_count} duplicates")
                    
                    if errors:
                        st.warning(f"⚠️ {len(errors)} errors occurred:")
                        for error in errors[:5]:
                            st.caption(error)
                    
                    st.rerun()
                
                except Exception as e:
                    st.error(f"❌ Error during import: {str(e)}")
        
        except Exception as e:
            st.error(f"❌ Error reading CSV file: {str(e)}")
    
    st.divider()
    
    # PRE-POPULATED DATA
    st.subheader("📌 Pre-populate Sample Data")
    
    if st.button("Load sample monitoring points from Midsayap", use_container_width=True):
        sample_data = [
            {
                "point_number": 1,
                "municipality": "Midsayap",
                "cluster": 1,
                "barangay": "Central Bulanan",
                "latitude": 7.139222,
                "longitude": 124.532531,
                "area_name": None,
                "is_active": 1
            },
            {
                "point_number": 2,
                "municipality": "Midsayap",
                "cluster": 1,
                "barangay": "Salunayan",
                "latitude": 7.156674,
                "longitude": 124.494224,
                "area_name": None,
                "is_active": 1
            },
            {
                "point_number": 3,
                "municipality": "Midsayap",
                "cluster": 1,
                "barangay": "Nes",
                "latitude": 7.144393,
                "longitude": 124.511458,
                "area_name": None,
                "is_active": 1
            },
            {
                "point_number": 4,
                "municipality": "Midsayap",
                "cluster": 2,
                "barangay": "Patindiguen",
                "latitude": 7.21772,
                "longitude": 124.48773,
                "area_name": None,
                "is_active": 1
            },
            {
                "point_number": 5,
                "municipality": "Midsayap",
                "cluster": 2,
                "barangay": "PhilRice (Lot A)",
                "latitude": 7.180493,
                "longitude": 124.486464,
                "area_name": "PhilRice (Lot A)",
                "is_active": 1
            },
            {
                "point_number": 6,
                "municipality": "Midsayap",
                "cluster": 3,
                "barangay": "PhilRice (Lot 64)",
                "latitude": 7.177998,
                "longitude": 124.500615,
                "area_name": "PhilRice (Lot 64)",
                "is_active": 1
            },
            {
                "point_number": 7,
                "municipality": "Midsayap",
                "cluster": 3,
                "barangay": "Lower Katingawan",
                "latitude": 7.18942,
                "longitude": 124.524209,
                "area_name": None,
                "is_active": 1
            },
            {
                "point_number": 8,
                "municipality": "Midsayap",
                "cluster": 3,
                "barangay": "Palonguguen",
                "latitude": 7.179431,
                "longitude": 124.486422,
                "area_name": None,
                "is_active": 1
            }
        ]
        
        imported = 0
        skipped = 0
        
        for data in sample_data:
            try:
                create_monitoring_point(data)
                imported += 1
            except:
                skipped += 1
        
        st.success(f"✅ Loaded {imported} sample points! (Skipped {skipped} duplicates)")
        st.rerun()

# ============================================================================
# AREA ANALYSIS PAGE - Analysts, Super Admin, Admin only
# ============================================================================
elif page == "Area Analysis":
    # Role-based access control
    if user['role'] not in ['super_admin', 'admin', 'analyst']:
        st.error("❌ Access Denied! Only Analysts, Admins, and Super Admins can view this page.")
        st.stop()
    
    st.subheader("📍 Area-Based Pest Analysis")
    
    pest_df = read_records("pest_records")
    
    if len(pest_df) > 0:
        pest_df = process_pest_data(pest_df)
        
        available_areas = get_available_areas(pest_df)
        
        if not available_areas:
            st.warning("⚠️ No area data available in the database.")
        else:
            # Tab-based interface
            tab1, tab2, tab3, tab4 = st.tabs(["Area Summary", "Area Comparison", "Area Trends", "Area Heatmap"])
            
            # TAB 1: AREA SUMMARY
            with tab1:
                st.write("**Summary statistics for each area**")
                
                area_summary_data = compare_areas(pest_df, available_areas)
                
                if len(area_summary_data) > 0:
                    st.dataframe(area_summary_data, use_container_width=True, hide_index=True)
                    
                    # Download button
                    csv = area_summary_data.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Area Summary as CSV",
                        data=csv,
                        file_name="area_summary.csv",
                        mime="text/csv",
                        key="area_summary_download"
                    )
                else:
                    st.info("No area data available.")
            
            # TAB 2: AREA COMPARISON
            with tab2:
                st.write("**Compare pest populations across areas**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    chart = create_area_comparison_chart(pest_df, 'rbb_count')
                    if chart:
                        st.plotly_chart(chart, use_container_width=True)
                
                with col2:
                    chart = create_area_comparison_chart(pest_df, 'wsb_count')
                    if chart:
                        st.plotly_chart(chart, use_container_width=True)
            
            # TAB 3: AREA TRENDS
            with tab3:
                st.write("**Pest trends for specific area**")
                
                selected_area = st.selectbox(
                    "Select an area to view trends",
                    available_areas,
                    key="area_trend_select"
                )
                
                # Get area summary
                area_info = get_area_summary(pest_df, selected_area)
                if area_info:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Total Records", area_info['Total Records'])
                    
                    with col2:
                        st.metric("RBB Total", int(area_info['RBB Total']))
                    
                    with col3:
                        st.metric("WSB Total", int(area_info['WSB Total']))
                
                st.divider()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    chart = create_area_trend_chart(pest_df, selected_area, 'rbb_count')
                    if chart:
                        st.plotly_chart(chart, use_container_width=True)
                
                with col2:
                    chart = create_area_trend_chart(pest_df, selected_area, 'wsb_count')
                    if chart:
                        st.plotly_chart(chart, use_container_width=True)
            
            # TAB 4: AREA HEATMAP
            with tab4:
                st.write("**Pest intensity heatmap by area and month**")
                
                chart = create_area_heatmap(pest_df)
                if chart:
                    st.plotly_chart(chart, use_container_width=True)
    
    else:
        st.info("📁 No data available. Please load data from the Settings page.")

# ============================================================================
# PEST RECORDS PAGE - Encoders, Super Admin, Admin only
# ============================================================================
elif page == "Pest Records":
    # Role-based access control
    if user['role'] not in ['super_admin', 'admin', 'encoder']:
        st.error("❌ Access Denied! Only Encoders, Admins, and Super Admins can access Pest Records.")
        st.stop()
    if user['role'] not in ['super_admin', 'encoder', 'analyst']:
        st.error("❌ You don't have permission to access pest records.")
        st.stop()
    
    st.subheader("📋 Pest Records Management")
    
    # Super Admin and Admin - All tabs
    tab1, tab2, tab3, tab4 = st.tabs(["View", "Add New", "Edit", "Delete"])
    
    # TAB 1: VIEW RECORDS
    with tab1:
        st.write("**View all pest records**")
        
        pest_df = read_records("pest_records")
        
        if len(pest_df) > 0:
            # Filters
            col1, col2, col3 = st.columns(3)
            
            with col1:
                filter_year = st.multiselect(
                    "Filter by Year",
                    sorted(pest_df['year'].unique()),
                    default=sorted(pest_df['year'].unique())
                )
            
            with col2:
                filter_month = st.multiselect(
                    "Filter by Month",
                    sorted(pest_df['month'].unique()),
                    default=sorted(pest_df['month'].unique())
                )
            
            with col3:
                filter_area = st.multiselect(
                    "Filter by Area Code",
                    sorted(pest_df['area_code'].dropna().unique()),
                    default=sorted(pest_df['area_code'].dropna().unique()) if 'area_code' in pest_df.columns else []
                )
            
            # Apply filters
            filtered_df = pest_df[
                (pest_df['year'].isin(filter_year)) &
                (pest_df['month'].isin(filter_month)) &
                (pest_df['area_code'].isin(filter_area))
            ]
            
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)
            
            # Download button
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name="pest_records.csv",
                mime="text/csv"
            )
        else:
            st.info("No pest records found.")
    
    # TAB 2: ADD NEW RECORD
    with tab2:
        st.markdown("""
        <div style='padding: 15px; border-radius: 10px; background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%); border-left: 4px solid #22c55e;'>
            <p style='margin: 0; color: #15803d; font-size: 0.95em;'><strong>➕ Add New Pest Record</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<p style='font-weight: 600; color: #374151;'>📅 Date Information</p>", unsafe_allow_html=True)
            year = st.number_input("Year", min_value=2018, max_value=2030, value=2024, key="add_year")
            month = st.number_input("Month", min_value=1, max_value=12, value=1, key="add_month")
            day = st.number_input("Day", min_value=1, max_value=31, value=1, key="add_day")
        
        with col2:
            st.markdown("<p style='font-weight: 600; color: #374151;'>📍 Location Information</p>", unsafe_allow_html=True)
            cluster = st.number_input("Cluster", min_value=1, value=1, key="add_cluster")
            area_code = st.text_input("Area Code", value="1", key="add_area")
        
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style='padding: 15px; border-radius: 10px; background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); border-left: 4px solid #0284c7;'>
            <p style='margin: 0; color: #0c4a6e; font-size: 0.95em;'><strong>🐛 Insect Recording</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        # Get available insects
        insects_df = read_records("insects")
        if len(insects_df) > 0:
            insect_options = {row['name']: row['id'] for _, row in insects_df.iterrows()}
            selected_insect_name = st.selectbox("Select Insect Type", list(insect_options.keys()), key="add_insect")
            selected_insect_id = insect_options[selected_insect_name]
        else:
            st.warning("⚠️ No insect types available. Please create insect types in the Admin panel first.")
            selected_insect_id = None
        
        count = st.number_input("Count", min_value=0, value=0, key="add_count")
        time_observed = st.time_input("Time Observed", key="add_time")
        
        if st.button("✅ Add Record", use_container_width=True, key="add_record_btn"):
            if selected_insect_id is None:
                st.error("❌ Please create insect types first or select a valid insect type.")
            else:
                data = {
                    'year': int(year),
                    'month': int(month),
                    'day': int(day),
                    'cluster': int(cluster),
                    'area_code': area_code,
                    'insect_id': selected_insect_id,
                    'count': int(count),
                    'time_observed': str(time_observed)
                }
                
                try:
                    record_id = create_record('pest_records', data)
                    st.success(f"✅ Record saved successfully! (ID: {record_id})")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Error saving record: {str(e)}")
    
    # TAB 3: EDIT RECORD
    with tab3:
        st.write("**Edit an existing record**")
        
        pest_df = read_records("pest_records")
        
        if len(pest_df) > 0:
            record_id = st.selectbox(
                "Select Record ID to Edit",
                pest_df['id'].values,
                format_func=lambda x: f"ID: {x} - {pest_df[pest_df['id']==x][['year', 'month', 'day']].values[0]}"
            )
            
            record = get_record_by_id('pest_records', record_id)
            
            if record:
                col1, col2 = st.columns(2)
                
                with col1:
                    rbb_count = st.number_input("RBB Count", value=record['rbb_count'], key="pest_edit_rbb")
                    wsb_count = st.number_input("WSB Count", value=record['wsb_count'], key="pest_edit_wsb")
                    temperature = st.number_input("Temperature (°C)", value=record['temperature'], key="pest_edit_temp")
                
                with col2:
                    humidity = st.number_input("Humidity (%)", value=record['humidity'], key="pest_edit_hum")
                    precipitation = st.number_input("Precipitation (mm)", value=record['precipitation'], key="pest_edit_precip")
                
                if st.button("💾 Update Record", use_container_width=True):
                    update_data = {
                        'rbb_count': rbb_count,
                        'wsb_count': wsb_count,
                        'temperature': temperature,
                        'humidity': humidity,
                        'precipitation': precipitation
                    }
                    
                    update_record('pest_records', record_id, update_data)
                    st.success("✅ Record updated successfully!")
        else:
            st.info("No records available to edit.")
    
    # TAB 4: DELETE RECORD
    with tab4:
        st.write("**Delete a record**")
        st.warning("⚠️ This action cannot be undone!")
        
        pest_df = read_records("pest_records")
        
        if len(pest_df) > 0:
            record_id = st.selectbox(
                "Select Record ID to Delete",
                pest_df['id'].values,
                format_func=lambda x: f"ID: {x} - {pest_df[pest_df['id']==x][['year', 'month', 'day']].values[0]}"
            )
            
            if st.button("🗑️ Delete Record", use_container_width=True, type="secondary"):
                delete_record('pest_records', record_id)
                st.success("✅ Record deleted successfully!")
                st.rerun()
        else:
            st.info("No records available to delete.")

# ============================================================================

# NASA POWER DATA PAGE - All authenticated users can access
# ============================================================================
elif page == "NASA POWER Data":
    st.header("NASA POWER Weather Data")
    st.markdown("""
    NASA POWER (Prediction of Worldwide Energy Resources) provides daily global weather data 
    including temperature, precipitation, wind speed, humidity, and radiation data.
    """)
    
    st.divider()
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Fetch Data", "View Data", "Parameters"])
    
    # TAB 1: Fetch Data
    with tab1:
        st.subheader("Fetch NASA POWER Data")
        
        from datetime import datetime, timedelta
        from utils.nasa_power_api import fetch_nasa_power_data, LOCATION
        from utils.database import get_monitoring_points
        
        # Get available monitoring points for selection
        try:
            monitoring_points_df = get_monitoring_points()
            if len(monitoring_points_df) > 0:
                st.subheader("Select Monitoring Point")
                
                point_options = {
                    f"Point {row['point_number']} - {row['barangay']}": {
                        "latitude": row["latitude"],
                        "longitude": row["longitude"],
                        "name": row["area_name"] or row["barangay"]
                    }
                    for idx, row in monitoring_points_df.iterrows()
                }
                
                selected_point = st.selectbox(
                    "Select a monitoring point to fetch weather data:",
                    list(point_options.keys()),
                    help="Choose from your registered monitoring points"
                )
                
                selected_coords = point_options[selected_point]
                
                # Display selected location
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Latitude", f"{selected_coords['latitude']:.6f}°")
                with col2:
                    st.metric("Longitude", f"{selected_coords['longitude']:.6f}°")
                with col3:
                    st.metric("Location", selected_coords['name'])
            else:
                st.warning("No monitoring points found. Please add monitoring points first.")
                selected_coords = LOCATION
        except Exception as e:
            st.warning(f"Could not load monitoring points: {str(e)}. Using default location.")
            selected_coords = LOCATION
        
        st.divider()
        
        st.subheader("Select Date Range")
        
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=datetime.now() - timedelta(days=365),
                help="Earliest available data: January 1, 2022"
            )
        
        with col2:
            end_date = st.date_input(
                "End Date",
                value=datetime.now(),
                help="Latest available data: Current date"
            )
        
        st.divider()
        
        st.subheader("Select Parameters")
        st.info("Select one or more weather parameters to fetch. If none are selected, all parameters will be fetched.")
        
        from utils.nasa_power_api import PARAMETERS
        
        # Create parameter selection with columns for better layout
        param_options = list(PARAMETERS.keys())
        param_descriptions = [PARAMETERS[p] for p in param_options]
        
        # Use multiselect with descriptions
        selected_parameters = st.multiselect(
            "Weather Parameters to Fetch:",
            options=param_options,
            default=None,
            format_func=lambda x: f"{x} - {PARAMETERS[x]}",
            help="Select multiple parameters by clicking and using Ctrl/Cmd+Click"
        )
        
        st.write("")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fetch_button = st.button("Fetch Data from NASA POWER", type="primary", use_container_width=True)
        
        with col2:
            mock_button = st.button("Use Mock Data (For Testing)", use_container_width=True)
        
        if fetch_button:
            with st.spinner("Fetching data from NASA POWER API..."):
                st.info(f"Requesting data for coordinates: {selected_coords['latitude']:.4f}, {selected_coords['longitude']:.4f}")
                
                # Use selected parameters if any, otherwise fetch all
                params_to_fetch = selected_parameters if selected_parameters else None
                
                df = fetch_nasa_power_data(
                    start_date, 
                    end_date, 
                    selected_coords['latitude'],
                    selected_coords['longitude'],
                    parameters=params_to_fetch
                )
                
                if df is not None:
                    st.session_state.nasa_data = df
                    st.success(f"Successfully fetched {len(df)} days of data from NASA POWER!")
                    
                    # Display summary statistics
                    st.subheader("Data Summary")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Records", len(df))
                    with col2:
                        st.metric("Date Range", f"{df['Date'].min().strftime('%Y-%m-%d')}")
                    with col3:
                        # Use safe column access - try multiple possible column names
                        temp_col = None
                        for col_name in ["Temperature at 2 Meters (°C)", "T2M"]:
                            if col_name in df.columns:
                                temp_col = col_name
                                break
                        if temp_col:
                            avg_temp = df[temp_col].mean()
                            st.metric("Avg Temperature", f"{avg_temp:.1f}°C")
                        else:
                            st.metric("Avg Temperature", "N/A")
                    with col4:
                        # Use safe column access - try multiple possible column names
                        precip_col = None
                        for col_name in ["Precipitation Corrected (mm/day)", "PRECTOTCORR"]:
                            if col_name in df.columns:
                                precip_col = col_name
                                break
                        if precip_col:
                            total_precip = df[precip_col].sum()
                            st.metric("Total Precipitation", f"{total_precip:.1f} mm")
                        else:
                            st.metric("Total Precipitation", "N/A")
        
        elif mock_button:
            with st.spinner("Generating mock data for testing..."):
                from utils.nasa_power_api import generate_mock_nasa_data
                
                # Use selected parameters if any, otherwise fetch all
                params_to_fetch = selected_parameters if selected_parameters else None
                
                df = generate_mock_nasa_data(
                    start_date,
                    end_date,
                    selected_coords['latitude'],
                    selected_coords['longitude'],
                    parameters=params_to_fetch
                )
                
                if df is not None:
                    st.session_state.nasa_data = df
                    st.success(f"Generated {len(df)} days of mock data for testing!")
                    
                    # Display summary statistics
                    st.subheader("Data Summary (Mock Data)")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Records", len(df))
                    with col2:
                        st.metric("Date Range", f"{df['Date'].min().strftime('%Y-%m-%d')}")
                    with col3:
                        # Use safe column access - try multiple possible column names
                        temp_col = None
                        for col_name in ["Temperature at 2 Meters (°C)", "T2M"]:
                            if col_name in df.columns:
                                temp_col = col_name
                                break
                        if temp_col:
                            avg_temp = df[temp_col].mean()
                            st.metric("Avg Temperature", f"{avg_temp:.1f}°C")
                        else:
                            st.metric("Avg Temperature", "N/A")
                    with col4:
                        # Use safe column access - try multiple possible column names
                        precip_col = None
                        for col_name in ["Precipitation Corrected (mm/day)", "PRECTOTCORR"]:
                            if col_name in df.columns:
                                precip_col = col_name
                                break
                        if precip_col:
                            total_precip = df[precip_col].sum()
                            st.metric("Total Precipitation", f"{total_precip:.1f} mm")
                        else:
                            st.metric("Total Precipitation", "N/A")
    
    # TAB 2: View Data
    with tab2:
        st.subheader("Downloaded Weather Data")
        
        if "nasa_data" in st.session_state and st.session_state.nasa_data is not None:
            df = st.session_state.nasa_data
            
            # Data statistics
            st.info(f"Total records: **{len(df)}** | Date range: **{df['Date'].min().strftime('%Y-%m-%d')}** to **{df['Date'].max().strftime('%Y-%m-%d')}** | Columns: **{len(df.columns)}'**")
            
            # Display table with expander
            with st.expander("View Full Data Table", expanded=True):
                st.dataframe(df, use_container_width=True, height=500)
            
            st.write("")
            
            # Download and save options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download as CSV",
                    data=csv,
                    file_name=f"nasa_power_data_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                # Excel download
                try:
                    excel_buffer = io.BytesIO()
                    df.to_excel(excel_buffer, index=False, sheet_name='NASA POWER Data')
                    excel_buffer.seek(0)
                    st.download_button(
                        label="Download as Excel",
                        data=excel_buffer,
                        file_name=f"nasa_power_data_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                except:
                    pass
            
            with col3:
                # Ask for area code before saving
                st.subheader("Save Options")
                area_code_input = st.text_input("Enter Area Code for this data:", value="", placeholder="e.g., Zone A, North Farm")
                
                if st.button("Save to Database", use_container_width=True):
                    if not area_code_input.strip():
                        st.error("Please enter an area code before saving!")
                    else:
                        from utils.nasa_power_api import format_nasa_data_for_db
                        from datetime import datetime
                        import pandas as pd
                        
                        records = format_nasa_data_for_db(df, "PhilRice (NASA POWER)")
                        
                        saved_count = 0
                        for record in records:
                            try:
                                # Parse date from datetime object
                                date_obj = record["date"]
                                if isinstance(date_obj, str):
                                    date_obj = datetime.strptime(str(date_obj), "%Y-%m-%d %H:%M:%S").date()
                                
                                # Helper function to safely convert to float, handling NaN
                                def safe_float(val, default=0):
                                    if val is None or pd.isna(val):
                                        return default
                                    try:
                                        return float(val)
                                    except:
                                        return default
                                
                                # Map NASA data to environmental_factors table schema
                                db_record = {
                                    "year": int(date_obj.year),
                                    "month": int(date_obj.month),
                                    "day": int(date_obj.day),
                                    "week_number": int(date_obj.isocalendar()[1]),
                                    "area_code": area_code_input.strip(),
                                    "cluster": 0,
                                    "temp_2m": safe_float(record["temperature"]),
                                    "temp_2m_min": safe_float(record["temperature_min"]),
                                    "temp_2m_max": safe_float(record["temperature_max"]),
                                    "humidity_2m": safe_float(record["humidity"]),
                                    "precipitation": safe_float(record["rainfall"]),
                                    "wind_speed_2m": safe_float(record["wind_speed"]),
                                    "wind_speed_2m_min": safe_float(record["wind_speed_min"]),
                                    "wind_speed_2m_max": safe_float(record["wind_speed_max"]),
                                    "wind_direction": safe_float(record["wind_direction"]),
                                    "allsky_uva": safe_float(record.get("uva_irradiance")),
                                    "allsky_uvb": safe_float(record.get("uvb_irradiance")),
                                    "clear_sky_par": safe_float(record.get("par_irradiance")),
                                    "moon_category": 1,
                                    "rbb_weekly": 0,
                                    "wsb_weekly": 0,
                                    "gwe_top": 0
                                }
                                
                                create_record("environmental_factors", db_record)
                                saved_count += 1
                            except Exception as e:
                                st.warning(f"Could not save record for {record['date']}: {str(e)}")
                        
                        st.success(f"Saved {saved_count} records to database from area: {area_code_input}!")
            
            st.write("")
            
            # Data exploration section
            st.subheader("Data Exploration")
            
            explore_col1, explore_col2 = st.columns(2)
            
            with explore_col1:
                st.write("**Available Parameters:**")
                param_list = ", ".join([col for col in df.columns if col != 'Date'])
                st.caption(param_list)
            
            with explore_col2:
                st.write("**Data Statistics:**")
                st.dataframe(df.describe().T, use_container_width=True)
            
            st.write("")
            
            # Chart section
            st.subheader("Visualizations")
            
            chart_tab1, chart_tab2, chart_tab3 = st.tabs(["Temperature", "Precipitation", "Wind Speed"])
            
            with chart_tab1:
                # Find temperature columns
                temp_cols = [col for col in df.columns if 'T2M' in col or 'Temperature' in col]
                if temp_cols:
                    chart_df = df.set_index("Date")[temp_cols]
                    st.line_chart(chart_df, use_container_width=True)
                else:
                    st.info("No temperature data available")
            
            with chart_tab2:
                # Find precipitation columns
                precip_cols = [col for col in df.columns if 'PRECTOTCORR' in col or 'Precipitation' in col]
                if precip_cols:
                    chart_df = df.set_index("Date")[precip_cols]
                    st.bar_chart(chart_df, use_container_width=True)
                else:
                    st.info("No precipitation data available")
            
            with chart_tab3:
                # Find wind speed columns
                wind_cols = [col for col in df.columns if 'WS2M' in col or 'Wind Speed' in col]
                if wind_cols:
                    chart_df = df.set_index("Date")[wind_cols]
                    st.line_chart(chart_df, use_container_width=True)
                else:
                    st.info("No wind speed data available")
        
        else:
            st.info("No data fetched yet. Go to the Fetch Data tab to download NASA POWER data.")
    
    # TAB 3: Available Parameters
    with tab3:
        st.subheader("Available Parameters from NASA POWER")
        
        from utils.nasa_power_api import get_available_parameters
        
        params = get_available_parameters()
        
        param_df = pd.DataFrame([
            {"Parameter Code": code, "Description": desc}
            for code, desc in params.items()
        ])
        
        st.dataframe(param_df, use_container_width=True)
        
        st.markdown("""
        ### Data Sources:
        - **CERES SYN1deg**: Clear Sky Surface PAR, All Sky Surface UVA, All Sky Surface UVB
        - **MERRA-2**: All other parameters (Temperature, Humidity, Precipitation, Wind, Soil Wetness)
        
        ### Missing Data:
        Missing values are represented as -999 in the raw data and are converted to None in our system.
        
        ### Location:
        - **Name**: PhilRice (Lot 64)
        - **Latitude**: 7.178°
        - **Longitude**: 124.5006°
        - **Elevation**: 213.14 m (from MERRA-2)
        - **Region**: 0.5 x 0.625 degree lat/lon region average
        """)

# ============================================================================
# ANALYTICS PAGE - Analysts, Super Admin, Admin only
# ============================================================================
elif page == "Analytics":
    # Role-based access control
    if user['role'] not in ['super_admin', 'admin', 'analyst']:
        st.error("❌ Access Denied! Only Analysts, Admins, and Super Admins can view Analytics.")
        st.stop()
    
    st.subheader("📈 Analytics & Insights")
    
    pest_df = read_records("pest_records")
    
    if len(pest_df) > 0:
        pest_df = process_pest_data(pest_df)
        
        tab1, tab2, tab3, tab4 = st.tabs(["Summary Stats", "Trends", "Correlations", "Outliers"])
        
        # TAB 1: SUMMARY STATISTICS
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**RBB Statistics**")
                rbb_stats = get_summary_statistics(pest_df, 'rbb_count')
                for key, value in rbb_stats.items():
                    st.metric(key, f"{value:.2f}")
            
            with col2:
                st.write("**WSB Statistics**")
                wsb_stats = get_summary_statistics(pest_df, 'wsb_count')
                for key, value in wsb_stats.items():
                    st.metric(key, f"{value:.2f}")
        
        # TAB 2: TRENDS
        with tab2:
            trend_type = st.radio("Select aggregation period:", ["Daily", "Monthly", "Yearly"], horizontal=True)
            
            if trend_type == "Daily":
                st.plotly_chart(create_pest_trend_chart(pest_df, 'rbb_count'), use_container_width=True)
                st.plotly_chart(create_pest_trend_chart(pest_df, 'wsb_count'), use_container_width=True)
            elif trend_type == "Monthly":
                agg_data = get_temporal_aggregation(pest_df, 'month')
                st.plotly_chart(create_pest_trend_chart(agg_data, 'rbb_count'), use_container_width=True)
                st.plotly_chart(create_pest_trend_chart(agg_data, 'wsb_count'), use_container_width=True)
            else:  # Yearly
                agg_data = get_temporal_aggregation(pest_df, 'year')
                st.plotly_chart(create_pest_trend_chart(agg_data, 'rbb_count'), use_container_width=True)
                st.plotly_chart(create_pest_trend_chart(agg_data, 'wsb_count'), use_container_width=True)
        
        # TAB 3: CORRELATIONS
        with tab3:
            if len(env_df) > 0:
                # Merge pest and environmental data
                merged_df = pest_df.copy()
                
                # Create correlation analysis
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**RBB vs Environmental Factors**")
                    fig = create_scatter_plot(merged_df, 'temperature', 'rbb_count', 'humidity')
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.write("**WSB vs Environmental Factors**")
                    fig = create_scatter_plot(merged_df, 'temperature', 'wsb_count', 'humidity')
                    st.plotly_chart(fig, use_container_width=True)
                
                # Distribution analysis
                col1, col2 = st.columns(2)
                
                with col1:
                    st.plotly_chart(create_distribution_chart(merged_df, 'rbb_count'), use_container_width=True)
                
                with col2:
                    st.plotly_chart(create_distribution_chart(merged_df, 'wsb_count'), use_container_width=True)
            else:
                st.info("Environmental data not available.")
        
        # TAB 4: OUTLIERS
        with tab4:
            pest_type = st.selectbox("Analyze outliers for:", ["RBB Count", "WSB Count", "Temperature", "Humidity"])
            
            col_map = {
                "RBB Count": "rbb_count",
                "WSB Count": "wsb_count",
                "Temperature": "temperature",
                "Humidity": "humidity"
            }
            
            outliers = detect_outliers(pest_df, col_map[pest_type], threshold=2)
            
            if len(outliers) > 0:
                st.write(f"**Found {len(outliers)} outliers for {pest_type}**")
                st.dataframe(outliers, use_container_width=True, hide_index=True)
            else:
                st.info(f"No outliers detected for {pest_type}.")
    
    else:
        st.info("📁 No data available. Please load data from the Settings page.")

# ============================================================================
# USER MANAGEMENT PAGE (Super Admin & Admin Only)
# ============================================================================
elif page == "User Management":
    if not can_manage_users(user):
        st.error("❌ You don't have permission to access this page. Only Super Admin and Admin can manage users.")
        st.stop()
    
    st.subheader("👥 User Management")
    
    tab1, tab2, tab3 = st.tabs(["Create User", "Manage Users", "Activity Log"])
    
    # TAB 1: CREATE NEW USER
    with tab1:
        st.write("**Create a new user account**")
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_username = st.text_input("Username", placeholder="Enter username", key="new_user_username")
            new_email = st.text_input("Email", placeholder="user@example.com", key="new_user_email")
        
        with col2:
            new_password = st.text_input("Password", type="password", placeholder="Min 6 characters", key="new_user_password")
            new_role = st.selectbox("Role", ["encoder", "analyst", "admin"], key="new_user_role")
        
        if st.button("✅ Create User", use_container_width=True, type="primary"):
            if new_username and new_email and new_password:
                if len(new_password) < 6:
                    st.error("❌ Password must be at least 6 characters")
                else:
                    from utils.rbac import create_user
                    success, message = create_user(new_username, new_email, new_password, new_role, user['username'])
                    
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.error(message)
            else:
                st.error("❌ Please fill in all fields")
    
    # TAB 2: MANAGE USERS
    with tab2:
        st.write("**View and manage existing users**")
        st.divider()
        
        from utils.rbac import get_all_users, delete_user, update_user_role
        
        users = get_all_users()
        
        if users:
            # Display users in a table
            users_df = pd.DataFrame(users, columns=['ID', 'Username', 'Email', 'Role', 'Active', 'Created', 'Last Login'])
            st.dataframe(users_df, use_container_width=True, hide_index=True)
            
            st.divider()
            st.write("**Modify User Role or Status**")
            
            # Select user to modify
            user_options = {f"{u[1]} ({u[3]})": u[0] for u in users}
            selected_user_display = st.selectbox("Select User", list(user_options.keys()), key="modify_user_select")
            selected_user_id = user_options[selected_user_display]
            
            col1, col2 = st.columns(2)
            
            with col1:
                new_role = st.selectbox("Assign New Role", ["encoder", "analyst", "admin"], key="assign_role")
                
                if st.button("🔄 Update Role", use_container_width=True):
                    success, message = update_user_role(selected_user_id, new_role, user['username'])
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
            
            with col2:
                if st.button("🗑️ Deactivate User", use_container_width=True, type="secondary"):
                    success, message = delete_user(selected_user_id, user['username'])
                    if success:
                        st.warning(message)
                        st.rerun()
                    else:
                        st.error(message)
        else:
            st.info("📭 No users found")
    
    # TAB 3: ACTIVITY LOG
    with tab3:
        st.write("**User activity log**")
        st.divider()
        
        from utils.rbac import get_activity_log
        
        activities = get_activity_log(100)
        
        if activities:
            activity_df = pd.DataFrame(activities, columns=['Username', 'Action', 'Details', 'Timestamp'])
            st.dataframe(activity_df, use_container_width=True, hide_index=True)
        else:
            st.info("📭 No activity log")

# ============================================================================
# INSECTS MANAGEMENT PAGE - Super Admin & Admin only
# ============================================================================
elif page == "Insects Management":
    # Role-based access control
    if user['role'] not in ['super_admin', 'admin']:
        st.error("❌ Access Denied! Only Admins can manage insects.")
        st.stop()
    
    # Modern header
    st.markdown("""
    <div style='padding: 30px; border-radius: 15px; background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); color: white; margin-bottom: 30px;'>
        <h1 style='margin: 0; font-size: 2.8em; font-weight: 800;'>🐛 Insects Management</h1>
        <p style='margin: 10px 0 0 0; font-size: 1.1em; opacity: 0.95;'>Create, read, update, and delete insect types</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 View Insects", "➕ Add Insect", "✏️ Edit Insect", "🗑️ Delete Insect"])
    
    # TAB 1: VIEW INSECTS
    with tab1:
        st.markdown("""
        <div style='padding: 15px; border-radius: 10px; background: linear-gradient(135deg, #ddd6fe 0%, #c7d2fe 100%); border-left: 4px solid #7c3aed;'>
            <p style='margin: 0; color: #4c1d95; font-size: 0.95em;'><strong>📋 All Insect Types</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        insects_df = read_records("insects")
        
        if len(insects_df) > 0:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div style='padding: 20px; border-radius: 12px; background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); border-top: 4px solid #6d28d9;'>
                    <p style='margin: 0; color: #ede9fe; font-size: 0.85em;'>Total Insects</p>
                    <h2 style='margin: 10px 0 0 0; color: white; font-size: 2.2em;'>{len(insects_df)}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                active_count = len(insects_df[insects_df['is_active'] == 1]) if 'is_active' in insects_df.columns else len(insects_df)
                st.markdown(f"""
                <div style='padding: 20px; border-radius: 12px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); border-top: 4px solid #064e3b;'>
                    <p style='margin: 0; color: #d1fae5; font-size: 0.85em;'>Active</p>
                    <h2 style='margin: 10px 0 0 0; color: white; font-size: 2.2em;'>{active_count}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div style='padding: 20px; border-radius: 12px; background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%); border-top: 4px solid #1e3a8a;'>
                    <p style='margin: 0; color: #e0e7ff; font-size: 0.85em;'>System Ready</p>
                    <h2 style='margin: 10px 0 0 0; color: white; font-size: 2.2em;'>✓</h2>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
            st.dataframe(insects_df[['id', 'name', 'scientific_name', 'is_active']], use_container_width=True, hide_index=True)
            
            csv = insects_df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name="insects.csv",
                mime="text/csv"
            )
        else:
            st.info("📌 No insect types found. Create one using the 'Add Insect' tab.")
    
    # TAB 2: ADD INSECT
    with tab2:
        st.markdown("""
        <div style='padding: 15px; border-radius: 10px; background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%); border-left: 4px solid #22c55e;'>
            <p style='margin: 0; color: #15803d; font-size: 0.95em;'><strong>➕ Add New Insect Type</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Insect Name (Common)", placeholder="e.g., Rice Brown Planthopper", key="add_insect_name")
        
        with col2:
            scientific_name = st.text_input("Scientific Name", placeholder="e.g., Nilaparvata lugens", key="add_sci_name")
        
        description = st.text_area("Description (Optional)", placeholder="Describe the insect characteristics...", key="add_description")
        
        if st.button("✅ Add Insect", use_container_width=True, key="add_insect_btn"):
            if not name:
                st.error("❌ Insect name is required!")
            else:
                data = {
                    'name': name,
                    'scientific_name': scientific_name if scientific_name else None,
                    'description': description if description else None,
                    'is_active': 1
                }
                
                try:
                    insect_id = create_record('insects', data)
                    st.success(f"✅ Insect added successfully! (ID: {insect_id})")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # TAB 3: EDIT INSECT
    with tab3:
        st.markdown("""
        <div style='padding: 15px; border-radius: 10px; background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-left: 4px solid #d97706;'>
            <p style='margin: 0; color: #78350f; font-size: 0.95em;'><strong>✏️ Edit Insect Type</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        insects_df = read_records("insects")
        
        if len(insects_df) > 0:
            selected_insect_id = st.selectbox(
                "Select Insect to Edit",
                insects_df["id"].values,
                format_func=lambda x: f"{insects_df[insects_df['id']==x]['name'].values[0]}"
            )
            
            insect = get_record_by_id('insects', selected_insect_id)
            
            if insect:
                col1, col2 = st.columns(2)
                
                with col1:
                    name = st.text_input("Insect Name", value=insect['name'], key=f"edit_name_{selected_insect_id}")
                
                with col2:
                    scientific_name = st.text_input("Scientific Name", value=insect.get('scientific_name') or '', key=f"edit_sci_{selected_insect_id}")
                
                description = st.text_area("Description", value=insect.get('description') or '', key=f"edit_desc_{selected_insect_id}")
                
                is_active = st.checkbox("Active", value=bool(insect.get('is_active', 1)), key=f"edit_active_{selected_insect_id}")
                
                if st.button("💾 Update Insect", use_container_width=True, key=f"update_insect_{selected_insect_id}"):
                    update_data = {
                        'name': name,
                        'scientific_name': scientific_name if scientific_name else None,
                        'description': description if description else None,
                        'is_active': 1 if is_active else 0
                    }
                    
                    try:
                        update_record('insects', selected_insect_id, update_data)
                        st.success("✅ Insect updated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        else:
            st.info("📌 No insects to edit.")
    
    # TAB 4: DELETE INSECT
    with tab4:
        st.markdown("""
        <div style='padding: 15px; border-radius: 10px; background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); border-left: 4px solid #dc2626;'>
            <p style='margin: 0; color: #7f1d1d; font-size: 0.95em;'><strong>🗑️ Delete Insect Type</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        st.warning("⚠️ Deleting an insect type will remove it from the system. This action cannot be undone!")
        
        insects_df = read_records("insects")
        
        if len(insects_df) > 0:
            selected_insect_id = st.selectbox(
                "Select Insect to Delete",
                insects_df["id"].values,
                format_func=lambda x: f"{insects_df[insects_df['id']==x]['name'].values[0]}",
                key="delete_insect_select"
            )
            
            if st.button("🗑️ Delete Insect", use_container_width=True, key="delete_insect_btn", type="secondary"):
                try:
                    delete_record('insects', selected_insect_id)
                    st.success("✅ Insect deleted successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        else:
            st.info("📌 No insects to delete.")

# ============================================================================
# SETTINGS PAGE - Super Admin & Admin only
# ============================================================================
elif page == "Settings":
    # Role-based access control
    if user['role'] not in ['super_admin', 'admin']:
        st.error("❌ Access Denied! Only Admins and Super Admins can access Settings.")
        st.stop()
    
    st.subheader("⚙️ Settings & Data Management")
    
    tab1, tab2 = st.tabs(["Load Data", "Database Info"])
    
    # TAB 1: LOAD DATA
    with tab1:
        st.write("**Import data from CSV files**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Load RBB Pest Records", use_container_width=True):
                csv_path = r"c:\Users\USER\Downloads\DS October 2024-March 2025_RBB Daily Light Trap Data.xlsx - Aggregated.csv"
                if Path(csv_path).exists():
                    try:
                        load_csv_to_db(csv_path, "pest_records")
                        st.success(f"✅ Successfully loaded RBB data!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error loading file: {str(e)}")
                else:
                    st.error(f"❌ File not found: {csv_path}")
        
        with col2:
            if st.button("📥 Load Environmental Factors", use_container_width=True):
                csv_path = r"c:\Users\USER\Downloads\cumulative_weekly_avg_per_week_across_years_12.11.2025 (1).csv"
                if Path(csv_path).exists():
                    try:
                        load_csv_to_db(csv_path, "environmental_factors")
                        st.success(f"✅ Successfully loaded environmental data!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error loading file: {str(e)}")
                else:
                    st.error(f"❌ File not found: {csv_path}")
        
        st.divider()
        st.info("💡 Click the buttons above to import data from the CSV files provided.")
    
    # TAB 2: DATABASE INFO
    with tab2:
        st.write("**Database Information**")
        
        pest_df = read_records("pest_records")
        
        st.metric("Pest Records (Local)", len(pest_df))
        if len(pest_df) > 0:
            st.write(f"**Date Range:** {pest_df['year'].min()}-{pest_df['month'].min():02d} to {pest_df['year'].max()}-{pest_df['month'].max():02d}")
            st.write(f"**RBB Total:** {pest_df['rbb_count'].sum()}")
        
        st.divider()
        
        if st.button("Clear All Data", type="secondary"):
            if st.session_state.get("confirm_clear"):
                # In production, you'd implement actual deletion
                st.warning("Data clearing not implemented in this demo.")
            else:
                st.session_state.confirm_clear = True
                st.warning("Click again to confirm clearing all data")

st.sidebar.divider()
st.sidebar.info(
    "🐛 **RiceProTek** - Insect Pest Management System\n\n"
    "Monitor and manage insect pest populations and environmental factors."
)
