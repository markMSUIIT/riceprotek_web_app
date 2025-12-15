import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import json
from pathlib import Path

# Google Sheets Configuration
SPREADSHEET_ID = "1Vp_EI-o9Cn8cpoUhwCR-_C3o_oIkMA0J"
PEST_RECORDS_SHEET = "Pest Records"
ENVIRONMENTAL_SHEET = "Environmental Factors"

# Scopes for Google Sheets API
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_google_sheets_service():
    """
    Get authenticated Google Sheets service.
    Uses Streamlit secrets for credentials.
    """
    try:
        # Try to get credentials from Streamlit secrets
        if "google_service_account" in st.secrets:
            creds_dict = st.secrets["google_service_account"]
            credentials = Credentials.from_service_account_info(
                creds_dict,
                scopes=SCOPES
            )
            service = build("sheets", "v4", credentials=credentials)
            return service
        else:
            st.error("❌ Google Service Account credentials not found in secrets.")
            st.info("📋 To set up Google Sheets integration:\n"
                   "1. Go to Google Cloud Console\n"
                   "2. Create a service account\n"
                   "3. Download the JSON key file\n"
                   "4. Add it to .streamlit/secrets.toml")
            return None
    except Exception as e:
        st.error(f"❌ Error authenticating with Google: {str(e)}")
        return None

def ensure_sheets_exist():
    """Ensure required sheets exist in the spreadsheet"""
    try:
        service = get_google_sheets_service()
        if not service:
            return False
        
        spreadsheet = service.spreadsheets().get(
            spreadsheetId=SPREADSHEET_ID
        ).execute()
        
        sheet_titles = [sheet["properties"]["title"] for sheet in spreadsheet["sheets"]]
        
        # Create sheets if they don't exist
        if PEST_RECORDS_SHEET not in sheet_titles:
            create_sheet(PEST_RECORDS_SHEET)
            initialize_pest_records_sheet()
        
        if ENVIRONMENTAL_SHEET not in sheet_titles:
            create_sheet(ENVIRONMENTAL_SHEET)
            initialize_environmental_sheet()
        
        return True
    except Exception as e:
        st.error(f"Error ensuring sheets exist: {str(e)}")
        return False

def create_sheet(sheet_name):
    """Create a new sheet in the spreadsheet"""
    try:
        service = get_google_sheets_service()
        if not service:
            return False
        
        request = {
            "addSheet": {
                "properties": {
                    "title": sheet_name
                }
            }
        }
        
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"requests": [request]}
        ).execute()
        
        return True
    except Exception as e:
        st.error(f"Error creating sheet: {str(e)}")
        return False

def initialize_pest_records_sheet():
    """Initialize pest records sheet with headers"""
    headers = [
        ["Year", "Month", "Day", "Latitude", "Longitude", "Cluster", 
         "Area Code", "RBB Count", "WSB Count", "Temperature", 
         "Max Temp", "Min Temp", "Humidity", "Precipitation", "Timestamp"]
    ]
    
    try:
        service = get_google_sheets_service()
        if not service:
            return False
        
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{PEST_RECORDS_SHEET}!A1",
            valueInputOption="RAW",
            body={"values": headers}
        ).execute()
        
        return True
    except Exception as e:
        st.error(f"Error initializing pest records sheet: {str(e)}")
        return False

def initialize_environmental_sheet():
    """Initialize environmental factors sheet with headers"""
    headers = [
        ["Year", "Week Number", "Month", "Day", "Moon Category", 
         "RBB Weekly", "WSB Weekly", "Clear Sky PAR", "AllSky UVA", 
         "AllSky UVB", "Temp 2m", "Temp 2m Min", "Temp 2m Max", 
         "Humidity 2m", "Precipitation", "Wind Speed 2m", 
         "Wind Speed 2m Max", "Wind Speed 2m Min", "Wind Direction", 
         "GWE Top", "Timestamp"]
    ]
    
    try:
        service = get_google_sheets_service()
        if not service:
            return False
        
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{ENVIRONMENTAL_SHEET}!A1",
            valueInputOption="RAW",
            body={"values": headers}
        ).execute()
        
        return True
    except Exception as e:
        st.error(f"Error initializing environmental sheet: {str(e)}")
        return False

def append_pest_record(record_data):
    """Append a new pest record to Google Sheets"""
    try:
        service = get_google_sheets_service()
        if not service:
            return False
        
        from datetime import datetime
        
        row_data = [[
            record_data.get('year'),
            record_data.get('month'),
            record_data.get('day'),
            record_data.get('latitude'),
            record_data.get('longitude'),
            record_data.get('cluster'),
            record_data.get('area_code'),
            record_data.get('rbb_count'),
            record_data.get('wsb_count'),
            record_data.get('temperature'),
            record_data.get('max_temp'),
            record_data.get('min_temp'),
            record_data.get('humidity'),
            record_data.get('precipitation'),
            datetime.now().isoformat()
        ]]
        
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{PEST_RECORDS_SHEET}!A:O",
            valueInputOption="USER_ENTERED",
            body={"values": row_data}
        ).execute()
        
        return True
    except Exception as e:
        st.error(f"Error appending pest record: {str(e)}")
        return False

def append_environmental_record(record_data):
    """Append a new environmental record to Google Sheets"""
    try:
        service = get_google_sheets_service()
        if not service:
            return False
        
        from datetime import datetime
        
        row_data = [[
            record_data.get('year'),
            record_data.get('week_number'),
            record_data.get('month'),
            record_data.get('day'),
            record_data.get('moon_category'),
            record_data.get('rbb_weekly'),
            record_data.get('wsb_weekly'),
            record_data.get('clear_sky_par'),
            record_data.get('allsky_uva'),
            record_data.get('allsky_uvb'),
            record_data.get('temp_2m'),
            record_data.get('temp_2m_min'),
            record_data.get('temp_2m_max'),
            record_data.get('humidity_2m'),
            record_data.get('precipitation'),
            record_data.get('wind_speed_2m'),
            record_data.get('wind_speed_2m_max'),
            record_data.get('wind_speed_2m_min'),
            record_data.get('wind_direction'),
            record_data.get('gwe_top'),
            datetime.now().isoformat()
        ]]
        
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{ENVIRONMENTAL_SHEET}!A:U",
            valueInputOption="USER_ENTERED",
            body={"values": row_data}
        ).execute()
        
        return True
    except Exception as e:
        st.error(f"Error appending environmental record: {str(e)}")
        return False

def read_pest_records_from_sheets():
    """Read all pest records from Google Sheets"""
    try:
        service = get_google_sheets_service()
        if not service:
            return pd.DataFrame()
        
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{PEST_RECORDS_SHEET}!A:O"
        ).execute()
        
        rows = result.get("values", [])
        if len(rows) <= 1:
            return pd.DataFrame()
        
        df = pd.DataFrame(rows[1:], columns=rows[0])
        
        # Convert numeric columns
        numeric_cols = ['Year', 'Month', 'Day', 'Latitude', 'Longitude', 'Cluster',
                       'RBB Count', 'WSB Count', 'Temperature', 'Max Temp', 'Min Temp',
                       'Humidity', 'Precipitation']
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Error reading pest records: {str(e)}")
        return pd.DataFrame()

def read_environmental_records_from_sheets():
    """Read all environmental records from Google Sheets"""
    try:
        service = get_google_sheets_service()
        if not service:
            return pd.DataFrame()
        
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{ENVIRONMENTAL_SHEET}!A:U"
        ).execute()
        
        rows = result.get("values", [])
        if len(rows) <= 1:
            return pd.DataFrame()
        
        df = pd.DataFrame(rows[1:], columns=rows[0])
        
        # Convert numeric columns
        numeric_cols = ['Year', 'Week Number', 'Month', 'Day', 'Moon Category',
                       'RBB Weekly', 'WSB Weekly', 'Clear Sky PAR', 'AllSky UVA',
                       'AllSky UVB', 'Temp 2m', 'Temp 2m Min', 'Temp 2m Max',
                       'Humidity 2m', 'Precipitation', 'Wind Speed 2m',
                       'Wind Speed 2m Max', 'Wind Speed 2m Min', 'Wind Direction', 'GWE Top']
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Error reading environmental records: {str(e)}")
        return pd.DataFrame()

def update_pest_record_in_sheets(row_index, record_data):
    """Update a pest record in Google Sheets"""
    try:
        service = get_google_sheets_service()
        if not service:
            return False
        
        from datetime import datetime
        
        row_data = [[
            record_data.get('year'),
            record_data.get('month'),
            record_data.get('day'),
            record_data.get('latitude'),
            record_data.get('longitude'),
            record_data.get('cluster'),
            record_data.get('area_code'),
            record_data.get('rbb_count'),
            record_data.get('wsb_count'),
            record_data.get('temperature'),
            record_data.get('max_temp'),
            record_data.get('min_temp'),
            record_data.get('humidity'),
            record_data.get('precipitation'),
            datetime.now().isoformat()
        ]]
        
        # Row index in sheets is 1-indexed, and we need to account for header row
        range_name = f"{PEST_RECORDS_SHEET}!A{row_index + 2}:O{row_index + 2}"
        
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body={"values": row_data}
        ).execute()
        
        return True
    except Exception as e:
        st.error(f"Error updating pest record: {str(e)}")
        return False

def delete_pest_record_from_sheets(row_index):
    """Delete a pest record from Google Sheets"""
    try:
        service = get_google_sheets_service()
        if not service:
            return False
        
        spreadsheet = service.spreadsheets().get(
            spreadsheetId=SPREADSHEET_ID
        ).execute()
        
        sheet_id = None
        for sheet in spreadsheet["sheets"]:
            if sheet["properties"]["title"] == PEST_RECORDS_SHEET:
                sheet_id = sheet["properties"]["sheetId"]
                break
        
        if sheet_id is None:
            st.error("Sheet not found")
            return False
        
        request = {
            "deleteRows": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "ROWS",
                    "startIndex": row_index + 1,
                    "endIndex": row_index + 2
                }
            }
        }
        
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"requests": [request]}
        ).execute()
        
        return True
    except Exception as e:
        st.error(f"Error deleting pest record: {str(e)}")
        return False
