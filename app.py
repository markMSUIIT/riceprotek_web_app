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
nav_options = [
    "Dashboard",
    "📍 Area Points",
    "📤 Dataset Upload",
    "Area Analysis",
    "Pest Records",
    "🌡️ Environmental Data",
    "Monitoring Points",
    "NASA POWER Data",
    "📊 Visualizations",
    "Analytics",
    "Settings"
]

# Add Admin-only sections
if user and can_manage_users(user):
    nav_options.insert(3, "User Management")
    nav_options.insert(4, "Insects Management")
    nav_options.append("📋 Activity Logs")

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
    <div style='padding: 30px; border-radius: 15px; background: linear-gradient(135deg, #2E7D32 0%, #1B5E20 100%); color: white; margin-bottom: 30px; box-shadow: 0 4px 15px rgba(46, 125, 50, 0.3);'>
        <h1 style='margin: 0; font-size: 2.8em; font-weight: 800;'>🌾 RiceProTek Dashboard</h1>
        <p style='margin: 10px 0 0 0; font-size: 1.1em; opacity: 0.95;'>Intelligent Pest Management & Environmental Monitoring</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get current user info
    current_user = get_current_user()
    user_name = current_user.get('username', 'User') if current_user else 'User'
    
    # Welcome message
    st.markdown(f"### 👋 Welcome back, **{user_name}**!")
    st.markdown("---")
    
    # Load data
    pest_df = read_records("pest_records")
    monitoring_points_df = read_records("monitoring_points")
    
    # Calculate insights
    total_rbb = int(pest_df['rbb_count'].sum()) if len(pest_df) > 0 and 'rbb_count' in pest_df.columns else 0
    total_wsb = int(pest_df['wsb_count'].sum()) if len(pest_df) > 0 and 'wsb_count' in pest_df.columns else 0
    total_pests = total_rbb + total_wsb
    
    # Calculate trend (last 7 days vs previous 7 days if date column exists)
    rbb_trend = 0
    wsb_trend = 0
    if len(pest_df) > 0 and 'date' in pest_df.columns:
        try:
            pest_df['date'] = pd.to_datetime(pest_df['date'])
            recent_data = pest_df[pest_df['date'] >= (pd.Timestamp.now() - pd.Timedelta(days=7))]
            older_data = pest_df[(pest_df['date'] >= (pd.Timestamp.now() - pd.Timedelta(days=14))) & 
                                (pest_df['date'] < (pd.Timestamp.now() - pd.Timedelta(days=7)))]
            
            recent_rbb = recent_data['rbb_count'].sum() if 'rbb_count' in recent_data.columns else 0
            older_rbb = older_data['rbb_count'].sum() if 'rbb_count' in older_data.columns else 0
            rbb_trend = ((recent_rbb - older_rbb) / older_rbb * 100) if older_rbb > 0 else 0
            
            recent_wsb = recent_data['wsb_count'].sum() if 'wsb_count' in recent_data.columns else 0
            older_wsb = older_data['wsb_count'].sum() if 'wsb_count' in older_data.columns else 0
            wsb_trend = ((recent_wsb - older_wsb) / older_wsb * 100) if older_wsb > 0 else 0
        except:
            pass
    
    # Key Performance Indicators
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        trend_icon = "📈" if rbb_trend > 0 else "📉" if rbb_trend < 0 else "➡️"
        trend_color = "#ef4444" if rbb_trend > 0 else "#10b981" if rbb_trend < 0 else "#6b7280"
        st.metric(
            label="🐛 Rice Black Bug",
            value=f"{total_rbb:,}",
            delta=f"{rbb_trend:+.1f}%" if rbb_trend != 0 else "No change",
            delta_color="inverse"
        )
    
    with col2:
        trend_icon = "📈" if wsb_trend > 0 else "📉" if wsb_trend < 0 else "➡️"
        trend_color = "#ef4444" if wsb_trend > 0 else "#10b981" if wsb_trend < 0 else "#6b7280"
        st.metric(
            label="🦗 White Stem Borer",
            value=f"{total_wsb:,}",
            delta=f"{wsb_trend:+.1f}%" if wsb_trend != 0 else "No change",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            label="📊 Total Records",
            value=f"{len(pest_df):,}",
            delta=f"{len(pest_df)} entries"
        )
    
    with col4:
        st.metric(
            label="📍 Monitoring Sites",
            value=f"{len(monitoring_points_df):,}",
            delta="Active" if len(monitoring_points_df) > 0 else "None"
        )
    
    st.markdown("---")
    
    # Data visualizations and insights
    if len(pest_df) > 0:
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.markdown("### 📈 Pest Population Trends")
            
            # Create trend chart if data is available
            if 'date' in pest_df.columns:
                pest_df_processed = process_pest_data(pest_df)
                if len(pest_df_processed) > 0:
                    fig = create_pest_trend_chart(pest_df_processed)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Not enough data to display trends. Add more records with dates.")
            else:
                st.info("Date information not available. Add dates to pest records for trend analysis.")
        
        with col_right:
            st.markdown("### 🎯 Pest Distribution")
            
            # Pie chart for pest distribution
            import plotly.graph_objects as go
            
            fig = go.Figure(data=[go.Pie(
                labels=['Rice Black Bug', 'White Stem Borer'],
                values=[total_rbb, total_wsb],
                hole=0.4,
                marker=dict(colors=['#ef4444', '#f59e0b']),
                textinfo='label+percent',
                textfont=dict(size=14)
            )])
            
            fig.update_layout(
                title=None,
                height=300,
                showlegend=True,
                margin=dict(l=20, r=20, t=20, b=20)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Alert status
            st.markdown("### ⚠️ Alert Status")
            if total_pests > 100:
                st.error("🚨 **High Alert**: Pest population exceeds threshold!")
            elif total_pests > 50:
                st.warning("⚠️ **Medium Alert**: Monitor pest levels closely.")
            else:
                st.success("✅ **Normal**: Pest levels under control.")
        
        # Recent activity and statistics
        st.markdown("---")
        st.markdown("### 📊 Detailed Statistics")
        
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        
        with stat_col1:
            avg_rbb = pest_df['rbb_count'].mean() if 'rbb_count' in pest_df.columns else 0
            st.markdown(f"""
            <div style='padding: 20px; background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); border-radius: 12px; border-left: 4px solid #dc2626;'>
                <h4 style='margin: 0 0 10px 0; color: #7f1d1d;'>🐛 RBB Analysis</h4>
                <p style='margin: 5px 0; color: #991b1b;'><strong>Average:</strong> {avg_rbb:.1f} per record</p>
                <p style='margin: 5px 0; color: #991b1b;'><strong>Total:</strong> {total_rbb:,}</p>
                <p style='margin: 5px 0; color: #991b1b;'><strong>Max:</strong> {int(pest_df['rbb_count'].max()) if 'rbb_count' in pest_df.columns else 0}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with stat_col2:
            avg_wsb = pest_df['wsb_count'].mean() if 'wsb_count' in pest_df.columns else 0
            st.markdown(f"""
            <div style='padding: 20px; background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-radius: 12px; border-left: 4px solid #d97706;'>
                <h4 style='margin: 0 0 10px 0; color: #78350f;'>🦗 WSB Analysis</h4>
                <p style='margin: 5px 0; color: #92400e;'><strong>Average:</strong> {avg_wsb:.1f} per record</p>
                <p style='margin: 5px 0; color: #92400e;'><strong>Total:</strong> {total_wsb:,}</p>
                <p style='margin: 5px 0; color: #92400e;'><strong>Max:</strong> {int(pest_df['wsb_count'].max()) if 'wsb_count' in pest_df.columns else 0}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with stat_col3:
            unique_areas = pest_df['area'].nunique() if 'area' in pest_df.columns else 0
            st.markdown(f"""
            <div style='padding: 20px; background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); border-radius: 12px; border-left: 4px solid #2563eb;'>
                <h4 style='margin: 0 0 10px 0; color: #1e3a8a;'>📍 Coverage</h4>
                <p style='margin: 5px 0; color: #1e40af;'><strong>Areas Monitored:</strong> {unique_areas}</p>
                <p style='margin: 5px 0; color: #1e40af;'><strong>Total Points:</strong> {len(monitoring_points_df)}</p>
                <p style='margin: 5px 0; color: #1e40af;'><strong>Records:</strong> {len(pest_df)}</p>
            </div>
            """, unsafe_allow_html=True)
        
    else:
        st.info("📊 **No data available yet.** Start by adding pest records to see meaningful insights and analytics.")
    
    st.markdown("---")
    
    # Quick Actions
    st.markdown("### ⚡ Quick Actions")
    
    quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)
    
    with quick_col1:
        if st.button("📋 Add Pest Record", use_container_width=True, key="quick_pest", type="primary"):
            st.switch_page  # Will be handled by navigation
            st.info("Navigate to 'Pest Records' to add new data")
    
    with quick_col2:
        if st.button("📊 View Analytics", use_container_width=True, key="quick_analytics"):
            st.info("Navigate to 'Analytics' for detailed insights")
    
    with quick_col3:
        if st.button("🗺️ Area Analysis", use_container_width=True, key="quick_area"):
            st.info("Navigate to 'Area Analysis' to compare locations")
    
    with quick_col4:
        if st.button("🌡️ Environmental Data", use_container_width=True, key="quick_env"):
            st.info("Navigate to 'NASA POWER Data' for climate info")

# ============================================================================
# AREA POINTS PAGE - Admin and Encoder only
# ============================================================================
elif page == "📍 Area Points":
    from utils.database import (
        create_area_point, get_area_points, get_area_point_by_id,
        update_area_point, delete_area_point, log_activity
    )
    
    st.markdown("## 📍 Area Points Management")
    st.markdown("Area Points are **mandatory** locations where pest and environmental data are collected.")
    st.info("⚠️ **Important**: You must create Area Points before adding any pest or environmental data.")
    
    # Role-based access control
    if user['role'] not in ['super_admin', 'admin', 'encoder']:
        st.error("❌ Access Denied! Only Super Admin, Admin, and Encoder can manage area points.")
        st.stop()
    
    # Tabs for different operations
    tab1, tab2, tab3 = st.tabs(["📋 View Area Points", "➕ Add New", "✏️ Edit/Delete"])
    
    # TAB 1: View Area Points
    with tab1:
        st.markdown("### Current Area Points")
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            show_inactive = st.checkbox("Show inactive area points", value=False)
        
        # Get area points
        area_points_df = get_area_points(active_only=not show_inactive)
        
        if len(area_points_df) > 0:
            st.markdown(f"**Total Area Points:** {len(area_points_df)}")
            
            # Display as table
            display_df = area_points_df[[
                'area_point_id', 'name', 'latitude', 'longitude', 
                'cluster', 'municipality', 'is_active', 'created_at'
            ]]
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # Export option
            csv = area_points_df.to_csv(index=False)
            st.download_button(
                "📥 Download as CSV",
                csv,
                "area_points.csv",
                "text/csv",
                key='download-area-points'
            )
        else:
            st.warning("No area points found. Add your first area point in the 'Add New' tab.")
    
    # TAB 2: Add New Area Point
    with tab2:
        st.markdown("### Add New Area Point")
        
        with st.form("add_area_point_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                area_point_id = st.text_input(
                    "Area Point ID*",
                    placeholder="e.g., LOT_A, FIELD_64",
                    help="Unique identifier for this location"
                )
                name = st.text_input(
                    "Name*",
                    placeholder="e.g., Rice Field A",
                    help="Descriptive name"
                )
                latitude = st.number_input(
                    "Latitude*",
                    min_value=-90.0,
                    max_value=90.0,
                    value=7.178,
                    format="%.6f",
                    help="Decimal degrees"
                )
                longitude = st.number_input(
                    "Longitude*",
                    min_value=-180.0,
                    max_value=180.0,
                    value=124.5006,
                    format="%.6f",
                    help="Decimal degrees"
                )
            
            with col2:
                cluster = st.number_input("Cluster", min_value=0, value=0)
                municipality = st.text_input("Municipality", placeholder="Optional")
                barangay = st.text_input("Barangay", placeholder="Optional")
                description = st.text_area("Description", placeholder="Additional details...")
            
            submitted = st.form_submit_button("➕ Add Area Point", type="primary", use_container_width=True)
            
            if submitted:
                # Validation
                if not area_point_id or not name:
                    st.error("❌ Area Point ID and Name are required!")
                elif not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                    st.error("❌ Invalid coordinates!")
                else:
                    try:
                        data = {
                            'area_point_id': area_point_id.strip(),
                            'name': name.strip(),
                            'latitude': latitude,
                            'longitude': longitude,
                            'cluster': cluster,
                            'municipality': municipality.strip() if municipality else None,
                            'barangay': barangay.strip() if barangay else None,
                            'description': description.strip() if description else None,
                            'created_by': user['username']
                        }
                        
                        point_id = create_area_point(data)
                        
                        # Log activity
                        log_activity(
                            user=user['username'],
                            action='create',
                            module='area_point',
                            entity_type='area_points',
                            entity_id=area_point_id,
                            details={'name': name}
                        )
                        
                        st.success(f"✅ Area Point '{area_point_id}' created successfully!")
                        st.rerun()
                    except ValueError as e:
                        st.error(f"❌ Error: {str(e)}")
                    except Exception as e:
                        st.error(f"❌ Failed to create area point: {str(e)}")
    
    # TAB 3: Edit/Delete
    with tab3:
        st.markdown("### Edit or Delete Area Point")
        
        # Get all area points
        all_points = get_area_points(active_only=False)
        
        if len(all_points) > 0:
            # Select area point to edit
            point_ids = all_points['area_point_id'].tolist()
            selected_id = st.selectbox("Select Area Point", point_ids)
            
            if selected_id:
                point = get_area_point_by_id(selected_id)
                
                if point:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### Edit Details")
                        with st.form("edit_area_point_form"):
                            new_name = st.text_input("Name", value=point['name'])
                            new_lat = st.number_input("Latitude", value=float(point['latitude']), format="%.6f")
                            new_lon = st.number_input("Longitude", value=float(point['longitude']), format="%.6f")
                            new_cluster = st.number_input("Cluster", value=int(point.get('cluster', 0)))
                            new_municipality = st.text_input("Municipality", value=point.get('municipality', ''))
                            new_barangay = st.text_input("Barangay", value=point.get('barangay', ''))
                            new_description = st.text_area("Description", value=point.get('description', ''))
                            
                            update_submitted = st.form_submit_button("💾 Update", type="primary", use_container_width=True)
                            
                            if update_submitted:
                                try:
                                    update_data = {
                                        'name': new_name,
                                        'latitude': new_lat,
                                        'longitude': new_lon,
                                        'cluster': new_cluster,
                                        'municipality': new_municipality,
                                        'barangay': new_barangay,
                                        'description': new_description
                                    }
                                    
                                    update_area_point(selected_id, update_data)
                                    
                                    # Log activity
                                    log_activity(
                                        user=user['username'],
                                        action='update',
                                        module='area_point',
                                        entity_type='area_points',
                                        entity_id=selected_id,
                                        details={'fields_updated': list(update_data.keys())}
                                    )
                                    
                                    st.success(f"✅ Area Point '{selected_id}' updated successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Update failed: {str(e)}")
                    
                    with col2:
                        st.markdown("#### Danger Zone")
                        st.warning("⚠️ Deactivating an area point will prevent new data from being added to it.")
                        
                        if point.get('is_active', 1):
                            if st.button("🚫 Deactivate Area Point", type="secondary", use_container_width=True):
                                try:
                                    delete_area_point(selected_id)
                                    
                                    # Log activity
                                    log_activity(
                                        user=user['username'],
                                        action='delete',
                                        module='area_point',
                                        entity_type='area_points',
                                        entity_id=selected_id,
                                        details={'action': 'deactivated'}
                                    )
                                    
                                    st.success(f"✅ Area Point '{selected_id}' deactivated.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Deactivation failed: {str(e)}")
                        else:
                            st.info("This area point is already inactive.")
        else:
            st.info("No area points available. Add your first area point in the 'Add New' tab.")

# ============================================================================
# DATASET UPLOAD PAGE - Admin and Encoder only
# ============================================================================
elif page == "📤 Dataset Upload":
    from utils.database import create_dataset_upload, update_dataset_upload, log_activity, get_area_points
    from utils.data_processing import (
        validate_pest_dataset, chop_dataset_by_domain, normalize_column_names,
        prepare_for_database
    )
    from utils.pest_management import bulk_import_pest_data
    from utils.database import bulk_create_environmental_data
    
    st.markdown("## 📤 Dataset Upload & Processing")
    st.markdown("Upload CSV files containing pest and environmental data for processing.")
    
    # Role-based access control
    if user['role'] not in ['super_admin', 'admin', 'encoder']:
        st.error("❌ Access Denied! Only Super Admin, Admin, and Encoder can upload datasets.")
        st.stop()
    
    st.info("ℹ️ **Required**: Select an Area Point before uploading. All data will be associated with this location.")
    
    # Area Point Selection (MANDATORY)
    area_points_df = get_area_points()
    
    if len(area_points_df) == 0:
        st.error("❌ No area points available! Please create an area point first in the '📍 Area Points' page.")
        st.stop()
    
    area_point_options = {row['area_point_id']: f"{row['name']} ({row['area_point_id']})" 
                         for _, row in area_points_df.iterrows()}
    
    selected_area_point = st.selectbox(
        "Select Area Point* (Where was this data collected?)",
        options=list(area_point_options.keys()),
        format_func=lambda x: area_point_options[x],
        help="Data will be linked to this location"
    )
    
    if not selected_area_point:
        st.warning("⚠️ Please select an area point to continue.")
        st.stop()
    
    st.success(f"✅ Selected: {area_point_options[selected_area_point]}")
    
    st.markdown("---")
    
    # File Upload
    uploaded_file = st.file_uploader(
        "Upload CSV File",
        type=['csv'],
        help="Upload a CSV file with pest and environmental data"
    )
    
    if uploaded_file is not None:
        try:
            # Read CSV
            df = pd.read_csv(uploaded_file)
            
            st.markdown("### 📋 Dataset Preview")
            st.markdown(f"**Rows:** {len(df)} | **Columns:** {len(df.columns)}")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Normalize column names
            df_normalized = normalize_column_names(df)
            
            # Validation
            st.markdown("### ✅ Validation")
            validation_result = validate_pest_dataset(df_normalized)
            
            if validation_result['valid']:
                st.success("✅ Dataset validation passed!")
            else:
                st.error("❌ Validation failed:")
                for error in validation_result['errors']:
                    st.error(f"  • {error}")
            
            if validation_result.get('warnings'):
                st.warning("⚠️ Warnings:")
                for warning in validation_result['warnings']:
                    st.warning(f"  • {warning}")
            
            # Domain Chopping
            if validation_result['valid']:
                st.markdown("### 📦 Domain Splitting")
                
                domains = chop_dataset_by_domain(df_normalized)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Environmental Records", len(domains['environmental']))
                with col2:
                    st.metric("Pest Records", len(domains['pest']))
                with col3:
                    st.metric("Metadata Records", len(domains['metadata']))
                
                # Process and Import
                st.markdown("### 🚀 Import Data")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    import_environmental = st.checkbox("Import Environmental Data", value=True)
                with col2:
                    import_pest = st.checkbox("Import Pest Data", value=True)
                
                if st.button("🚀 Process and Import Dataset", type="primary", use_container_width=True):
                    with st.spinner("Processing dataset..."):
                        # Create upload record
                        upload_data = {
                            'filename': f"{selected_area_point}_{uploaded_file.name}",
                            'original_filename': uploaded_file.name,
                            'uploader': user['username'],
                            'row_count': len(df),
                            'validation_status': 'valid' if validation_result['valid'] else 'invalid',
                            'validation_errors': str(validation_result.get('errors', [])),
                            'file_size': uploaded_file.size,
                            'columns_detected': str(list(df.columns)),
                            'processing_status': 'processing'
                        }
                        
                        upload_id = create_dataset_upload(upload_data)
                        
                        results = {'environmental': None, 'pest': None}
                        
                        # Import Environmental Data
                        if import_environmental and len(domains['environmental']) > 0:
                            env_prepared = prepare_for_database(
                                domains['environmental'],
                                selected_area_point,
                                user['username']
                            )
                            
                            env_records = []
                            for _, row in env_prepared.iterrows():
                                record = {
                                    'area_point_id': selected_area_point,
                                    'date': row.get('date'),
                                    'source': 'manual',
                                    'temperature': row.get('T2M'),
                                    't2m_min': row.get('T2M_MIN'),
                                    't2m_max': row.get('T2M_MAX'),
                                    'humidity': row.get('RH2M'),
                                    'precipitation': row.get('PRECTOTCORR'),
                                    'wind_speed': row.get('WS2M'),
                                    'wind_speed_max': row.get('WS2M_MAX'),
                                    'wind_speed_min': row.get('WS2M_MIN'),
                                    'wind_direction': row.get('WD2M'),
                                    'solar_radiation': row.get('CLRSKY_SFC_PAR_TOT'),
                                    'uva': row.get('ALLSKY_SFC_UVA'),
                                    'uvb': row.get('ALLSKY_SFC_UVB'),
                                    'gwettop': row.get('GWETTOP')
                                }
                                env_records.append(record)
                            
                            results['environmental'] = bulk_create_environmental_data(env_records, user['username'])
                        
                        # Import Pest Data
                        if import_pest and len(domains['pest']) > 0:
                            pest_prepared = prepare_for_database(
                                domains['pest'],
                                selected_area_point,
                                user['username']
                            )
                            results['pest'] = bulk_import_pest_data(pest_prepared, selected_area_point, user['username'])
                        
                        # Update upload status
                        update_dataset_upload(upload_id, {'processing_status': 'completed'})
                        
                        # Log activity
                        log_activity(
                            user=user['username'],
                            action='upload',
                            module='dataset',
                            entity_type='dataset_uploads',
                            entity_id=upload_id,
                            details={
                                'area_point_id': selected_area_point,
                                'filename': uploaded_file.name,
                                'results': results
                            }
                        )
                        
                        st.success("✅ Dataset imported successfully!")
                        
                        # Show results
                        if results['environmental']:
                            st.info(f"📊 Environmental: {results['environmental']['success']} success, {results['environmental']['failed']} failed")
                        if results['pest']:
                            st.info(f"🐛 Pest: {results['pest']['success']} success, {results['pest']['failed']} failed")
        
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

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

# ============================================================================
# ACTIVITY LOGS PAGE - Admin only
# ============================================================================
elif page == "📋 Activity Logs":
    from utils.database import get_activity_logs
    
    st.markdown("## 📋 Activity Logs")
    st.markdown("View all user activities and system events.")
    
    # Admin-only access
    if user['role'] not in ['super_admin', 'admin']:
        st.error("❌ Access Denied! Only Super Admin and Admin can view activity logs.")
        st.stop()
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        filter_user = st.selectbox("User", ["All"] + list(get_activity_logs()['user'].unique()) if len(get_activity_logs()) > 0 else ["All"])
    with col2:
        filter_module = st.selectbox("Module", ["All", "dataset", "environmental", "pest", "area_point", "auth", "settings"])
    with col3:
        filter_action = st.selectbox("Action", ["All", "create", "read", "update", "delete", "upload", "login", "logout"])
    with col4:
        limit = st.number_input("Limit", min_value=10, max_value=1000, value=100)
    
    # Get logs
    logs_df = get_activity_logs(
        user=None if filter_user == "All" else filter_user,
        module=None if filter_module == "All" else filter_module,
        action=None if filter_action == "All" else filter_action,
        limit=limit
    )
    
    if len(logs_df) > 0:
        st.markdown(f"**Total Logs:** {len(logs_df)}")
        st.dataframe(logs_df, use_container_width=True, hide_index=True)
        
        # Export
        csv = logs_df.to_csv(index=False)
        st.download_button("📥 Export Logs", csv, "activity_logs.csv", "text/csv")
    else:
        st.info("No activity logs found.")

# ============================================================================
# VISUALIZATIONS PAGE
# ============================================================================
elif page == "📊 Visualizations":
    from utils.visualizations import (
        create_pest_density_chart, create_pest_shape_plot,
        create_pest_vs_climate_timeseries, create_weekly_pest_pattern
    )
    from utils.database import read_records, get_area_points
    
    st.markdown("## 📊 Advanced Visualizations")
    
    # Get data
    pest_df = read_records("pest_records")
    env_df = read_records("environmental_data")
    area_points = get_area_points()
    
    if len(pest_df) == 0:
        st.warning("No pest data available. Add data to see visualizations.")
        st.stop()
    
    # Filters
    st.markdown("### Filters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'area_point_id' in pest_df.columns:
            area_filter = st.multiselect("Area Points", pest_df['area_point_id'].unique())
            if area_filter:
                pest_df = pest_df[pest_df['area_point_id'].isin(area_filter)]
    
    with col2:
        if 'pest_type' in pest_df.columns:
            pest_type_filter = st.selectbox("Pest Type", ["All", "rbb", "wsb"])
            if pest_type_filter != "All":
                pest_df = pest_df[pest_df['pest_type'] == pest_type_filter]
    
    with col3:
        date_range = st.date_input("Date Range", [])
    
    # Visualizations
    tab1, tab2, tab3, tab4 = st.tabs(["Density", "Distribution Shape", "Pest vs Climate", "Weekly Patterns"])
    
    with tab1:
        st.markdown("### Pest Density Distribution")
        if 'density' in pest_df.columns:
            fig = create_pest_density_chart(pest_df, pest_type_filter if pest_type_filter != "All" else None)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No density data available.")
    
    with tab2:
        st.markdown("### Population Distribution Shape")
        if 'pest_type' in pest_df.columns and 'count' in pest_df.columns:
            fig = create_pest_shape_plot(pest_df)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Missing required columns for shape plot.")
    
    with tab3:
        st.markdown("### Pest Population vs Climate")
        if len(env_df) > 0:
            climate_var = st.selectbox("Climate Variable", ["temperature", "humidity", "precipitation", "wind_speed"])
            pest_type_select = st.selectbox("Pest", ["rbb", "wsb"], key="climate_pest")
            
            fig = create_pest_vs_climate_timeseries(pest_df, env_df, pest_type_select, climate_var)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough data to create time series comparison.")
        else:
            st.info("No environmental data available.")
    
    with tab4:
        st.markdown("### Weekly Pest Patterns")
        if 'week_number' in pest_df.columns:
            fig = create_weekly_pest_pattern(pest_df, pest_type_filter if pest_type_filter != "All" else None)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Week number data not available.")

# ============================================================================
# ENVIRONMENTAL DATA PAGE
# ============================================================================
elif page == "🌡️ Environmental Data":
    from utils.database import get_environmental_data, create_environmental_data, get_area_points, log_activity
    from utils.data_processing import validate_environmental_data
    
    st.markdown("## 🌡️ Environmental Data Management")
    
    # Role check
    if user['role'] not in ['super_admin', 'admin', 'encoder']:
        st.error("❌ Access Denied!")
        st.stop()
    
    tabs = st.tabs(["📋 View Data", "➕ Add Manual Entry"])
    
    with tabs[0]:
        st.markdown("### Environmental Records")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        area_points = get_area_points()
        with col1:
            if len(area_points) > 0:
                area_filter = st.selectbox("Area Point", ["All"] + list(area_points['area_point_id']))
            else:
                st.warning("No area points available.")
                st.stop()
        
        with col2:
            source_filter = st.selectbox("Source", ["All", "nasa_power", "microclimate", "manual"])
        
        # Get data
        env_df = get_environmental_data(
            area_point_id=None if area_filter == "All" else area_filter,
            source=None if source_filter == "All" else source_filter
        )
        
        if len(env_df) > 0:
            st.markdown(f"**Total Records:** {len(env_df)}")
            st.dataframe(env_df, use_container_width=True, hide_index=True)
        else:
            st.info("No environmental data found.")
    
    with tabs[1]:
        st.markdown("### Add Manual Microclimate Entry")
        
        if len(area_points) == 0:
            st.error("Create an area point first!")
            st.stop()
        
        with st.form("manual_env_form"):
            area_point_id = st.selectbox("Area Point*", area_points['area_point_id'])
            date = st.date_input("Date*")
            
            col1, col2 = st.columns(2)
            with col1:
                temp = st.number_input("Temperature (°C)", value=25.0)
                humidity = st.number_input("Humidity (%)", value=80.0)
            with col2:
                rainfall = st.number_input("Rainfall (mm)", value=0.0)
                soil_temp = st.number_input("Soil Temperature (°C)", value=None)
            
            submitted = st.form_submit_button("💾 Save", type="primary")
            
            if submitted:
                data = {
                    'area_point_id': area_point_id,
                    'date': str(date),
                    'source': 'microclimate',
                    'temperature': temp,
                    'humidity': humidity,
                    'precipitation': rainfall,
                    'soil_temp': soil_temp,
                    'created_by': user['username']
                }
                
                validation = validate_environmental_data(data)
                if validation['valid']:
                    try:
                        create_environmental_data(data)
                        log_activity(user['username'], 'create', 'environmental', 'environmental_data', area_point_id)
                        st.success("✅ Data saved!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                else:
                    for error in validation['errors']:
                        st.error(error)

st.sidebar.divider()
st.sidebar.info(
    "🐛 **RiceProTek** - Insect Pest Management System\n\n"
    "Monitor and manage insect pest populations and environmental factors."
)
