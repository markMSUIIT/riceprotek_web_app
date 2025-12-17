import requests
import pandas as pd
from datetime import datetime
import streamlit as st

# NASA POWER API Configuration
NASA_POWER_API_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
AUTO_USE_MOCK_ON_ERROR = True  # Automatically use mock data if API request fails

# PhilRice (Lot 64) Location
LOCATION = {
    "latitude": 7.178,
    "longitude": 124.5006,
    "elevation": 213.14,
    "name": "PhilRice (Lot 64)"
}

# Parameters to fetch
PARAMETERS = {
    "CLRSKY_SFC_PAR_TOT": "Clear Sky Surface Total PAR (MJ/m²/day)",
    "ALLSKY_SFC_UVA": "All Sky Surface UVA Irradiance (MJ/m²/day)",
    "ALLSKY_SFC_UVB": "All Sky Surface UVB Irradiance (MJ/m²/day)",
    "T2M": "Temperature at 2 Meters (°C)",
    "T2M_MIN": "Min Temperature at 2 Meters (°C)",
    "T2M_MAX": "Max Temperature at 2 Meters (°C)",
    "RH2M": "Relative Humidity at 2 Meters (%)",
    "PRECTOTCORR": "Precipitation Corrected (mm/day)",
    "WS2M": "Wind Speed at 2 Meters (m/s)",
    "WS2M_MAX": "Max Wind Speed at 2 Meters (m/s)",
    "WS2M_MIN": "Min Wind Speed at 2 Meters (m/s)",
    "WD2M": "Wind Direction at 2 Meters (Degrees)",
    "GWETTOP": "Surface Soil Wetness (0-1)"
}

def fetch_nasa_power_data(start_date=None, end_date=None, latitude=None, longitude=None, parameters=None):
    """
    Fetch NASA POWER data for specified date range and location
    
    Args:
        start_date: Start date (YYYYMMDD format or datetime object)
        end_date: End date (YYYYMMDD format or datetime object)
        latitude: Latitude (default: PhilRice latitude)
        longitude: Longitude (default: PhilRice longitude)
        parameters: List of parameter codes to fetch. If None, fetches all available parameters
    
    Returns:
        DataFrame with NASA POWER data or None if request fails
    """
    try:
        # Use defaults if not provided
        if latitude is None:
            latitude = LOCATION["latitude"]
        if longitude is None:
            longitude = LOCATION["longitude"]
        
        # Default dates if not provided (last 1 year)
        if start_date is None:
            start_date = pd.Timestamp.now() - pd.Timedelta(days=365)
        if end_date is None:
            end_date = pd.Timestamp.now()
        
        # Convert to datetime if string
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)
        
        # Ensure dates are at least 1 day apart
        if start_date >= end_date:
            st.error("❌ Start date must be before end date")
            return None
        
        # Format dates as YYYYMMDD
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        
        # Round coordinates to reasonable precision (4 decimal places)
        latitude = round(float(latitude), 4)
        longitude = round(float(longitude), 4)
        
        # Build parameters string - use selected parameters or all if none specified
        if parameters is None:
            params_str = ",".join(PARAMETERS.keys())
        else:
            # Filter parameters to only include valid ones
            valid_params = [p for p in parameters if p in PARAMETERS.keys()]
            if not valid_params:
                st.error("❌ No valid parameters selected. Please select at least one parameter.")
                return None
            params_str = ",".join(valid_params)
        
        # API request parameters - use proper format for POWER API
        api_params = {
            "start": start_str,
            "end": end_str,
            "latitude": latitude,
            "longitude": longitude,
            "parameters": params_str,
            "community": "RE",
            "format": "JSON"
        }
        
        # Make request with timeout
        try:
            response = requests.get(NASA_POWER_API_URL, params=api_params, timeout=30)
            
            # Debug: show the request URL
            st.write(f"🔗 Request URL: {response.url[:100]}...")
            
            response.raise_for_status()
            
            data = response.json()
            
            # Check if request was successful
            if data.get("properties", {}).get("parameter") is None:
                error_msg = data.get('messages', ['Unknown error'])
                st.warning(f"⚠️ NASA POWER API warning: {error_msg}")
                if AUTO_USE_MOCK_ON_ERROR:
                    st.info("🧪 Falling back to mock data...")
                    return generate_mock_nasa_data(start_date, end_date, latitude, longitude, parameters)
                return None
            
            # Parse the data
            df = parse_nasa_power_response(data)
            return df
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                error_text = f"""
                ⚠️ NASA POWER API returned 404
                
                **Tried endpoint:** {NASA_POWER_API_URL}
                
                **Debug Info:**
                - Coordinates: {latitude}, {longitude}
                - Parameters: {params_str[:50]}...
                - Date range: {start_str} to {end_str}
                
                **Note:** The API may not support this location or region.
                """
                st.warning(error_text)
                if AUTO_USE_MOCK_ON_ERROR:
                    st.info("🧪 Using mock data for testing...")
                    return generate_mock_nasa_data(start_date, end_date, latitude, longitude, parameters)
            else:
                st.error(f"❌ NASA POWER API HTTP Error {e.response.status_code}: {e.response.reason}")
            return None
    
    except requests.exceptions.Timeout:
        st.warning("⚠️ NASA POWER API request timed out (>30s).")
        if AUTO_USE_MOCK_ON_ERROR:
            st.info("🧪 Using mock data instead...")
            return generate_mock_nasa_data(start_date, end_date, latitude, longitude, parameters)
        return None
    except requests.exceptions.ConnectionError:
        st.warning("⚠️ Failed to connect to NASA POWER API.")
        if AUTO_USE_MOCK_ON_ERROR:
            st.info("🧪 Using mock data instead...")
            return generate_mock_nasa_data(start_date, end_date, latitude, longitude, parameters)
        return None
    except requests.exceptions.HTTPError as e:
        # Handled above in the try block
        return None
    except Exception as e:
        st.warning(f"⚠️ Error fetching NASA POWER data: {str(e)}")
        if AUTO_USE_MOCK_ON_ERROR:
            st.info("🧪 Using mock data instead...")
            return generate_mock_nasa_data(start_date, end_date, latitude, longitude, parameters)
        return None

def parse_nasa_power_response(response_data):
    """
    Parse NASA POWER API JSON response into a DataFrame
    
    Args:
        response_data: JSON response from NASA POWER API
    
    Returns:
        DataFrame with parsed data
    """
    try:
        parameters = response_data["properties"]["parameter"]
        
        # Extract dates and create dataframe
        dates = []
        data_dict = {}
        
        # Get first parameter to extract dates
        first_param = next(iter(parameters.values()))
        
        for date_str in first_param.keys():
            try:
                # Parse date (YYYYMMDD format)
                date_obj = datetime.strptime(date_str, "%Y%m%d")
                dates.append(date_obj)
            except:
                continue
        
        # Sort dates
        dates.sort()
        
        # Extract data for each parameter that was in the response
        for param_code in parameters.keys():
            # Use the full parameter name if available, otherwise use code
            param_name = PARAMETERS.get(param_code, param_code)
            param_data = parameters[param_code]
            values = []
            
            for date_obj in dates:
                date_str = date_obj.strftime("%Y%m%d")
                
                if date_str in param_data:
                    value = param_data[date_str]
                    # Handle missing values (-999)
                    if value == -999:
                        values.append(None)
                    else:
                        values.append(value)
                else:
                    values.append(None)
            
            data_dict[param_name] = values
        
        # Create DataFrame
        df = pd.DataFrame({
            "Date": dates,
            **data_dict
        })
        
        # Convert Date to datetime
        df["Date"] = pd.to_datetime(df["Date"])
        
        # Sort by date
        df = df.sort_values("Date").reset_index(drop=True)
        
        return df
    
    except Exception as e:
        st.error(f"❌ Error parsing NASA POWER data: {str(e)}")
        return None

def get_location_info():
    """Return PhilRice location information"""
    return LOCATION

def get_available_parameters():
    """Return dictionary of available parameters and descriptions"""
    return PARAMETERS

def validate_coordinates(latitude, longitude):
    """Validate latitude and longitude coordinates"""
    if not (-90 <= latitude <= 90):
        return False, "Latitude must be between -90 and 90"
    if not (-180 <= longitude <= 180):
        return False, "Longitude must be between -180 and 180"
    return True, "Valid coordinates"

def format_nasa_data_for_db(df, location_name="PhilRice"):
    """
    Format NASA POWER data for insertion into environmental_factors table
    
    Args:
        df: DataFrame from parse_nasa_power_response
        location_name: Location name for the records
    
    Returns:
        List of dictionaries ready for database insertion
    """
    records = []
    
    for idx, row in df.iterrows():
        record = {
            "date": row["Date"],
            "area": location_name,
            "temperature": row.get("Temperature at 2 Meters (°C)"),
            "temperature_min": row.get("Min Temperature at 2 Meters (°C)"),
            "temperature_max": row.get("Max Temperature at 2 Meters (°C)"),
            "humidity": row.get("Relative Humidity at 2 Meters (%)"),
            "rainfall": row.get("Precipitation Corrected (mm/day)"),
            "wind_speed": row.get("Wind Speed at 2 Meters (m/s)"),
            "wind_speed_max": row.get("Max Wind Speed at 2 Meters (m/s)"),
            "wind_speed_min": row.get("Min Wind Speed at 2 Meters (m/s)"),
            "wind_direction": row.get("Wind Direction at 2 Meters (Degrees)"),
            "soil_wetness": row.get("Surface Soil Wetness (0-1)"),
            "uva_irradiance": row.get("All Sky Surface UVA Irradiance (MJ/m²/day)"),
            "uvb_irradiance": row.get("All Sky Surface UVB Irradiance (MJ/m²/day)"),
            "par_irradiance": row.get("Clear Sky Surface Total PAR (MJ/m²/day)"),
            "source": "NASA POWER"
        }
        records.append(record)
    
    return records

def get_latest_nasa_data(latitude=None, longitude=None):
    """
    Fetch only the latest NASA POWER data (last 30 days)
    
    
    Args:
        latitude: Latitude (default: PhilRice)
        longitude: Longitude (default: PhilRice)
    
    Returns:
        DataFrame or None
    """
    end_date = pd.Timestamp.now()
    start_date = end_date - pd.Timedelta(days=30)
    
    return fetch_nasa_power_data(start_date, end_date, latitude, longitude)

def generate_mock_nasa_data(start_date, end_date, latitude=None, longitude=None, parameters=None):
    """
    Generate mock NASA POWER data for testing when the API is unavailable
    
    Args:
        start_date: Start date
        end_date: End date
        latitude: Latitude
        longitude: Longitude
        parameters: List of parameters to include
    
    Returns:
        DataFrame with mock data
    """
    import numpy as np
    
    # Create date range
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Use all parameters if none specified
    if parameters is None:
        params_to_use = list(PARAMETERS.keys())
    else:
        params_to_use = [p for p in parameters if p in PARAMETERS.keys()]
    
    # Generate random data based on parameter type
    data_dict = {"Date": dates}
    
    np.random.seed(42)  # For reproducibility
    
    for param_code in params_to_use:
        param_name = PARAMETERS[param_code]
        
        # Generate realistic data based on parameter type
        if "Temperature" in param_name:
            if "Max" in param_name:
                data_dict[param_name] = np.random.uniform(28, 35, len(dates))
            elif "Min" in param_name:
                data_dict[param_name] = np.random.uniform(20, 26, len(dates))
            else:
                data_dict[param_name] = np.random.uniform(24, 30, len(dates))
        elif "Humidity" in param_name:
            data_dict[param_name] = np.random.uniform(60, 95, len(dates))
        elif "Precipitation" in param_name:
            data_dict[param_name] = np.abs(np.random.normal(5, 3, len(dates)))
        elif "Wind Speed" in param_name:
            if "Max" in param_name:
                data_dict[param_name] = np.random.uniform(3, 6, len(dates))
            elif "Min" in param_name:
                data_dict[param_name] = np.random.uniform(0.5, 2, len(dates))
            else:
                data_dict[param_name] = np.random.uniform(1.5, 4, len(dates))
        elif "Wind Direction" in param_name:
            data_dict[param_name] = np.random.uniform(0, 360, len(dates))
        elif "Irradiance" in param_name or "PAR" in param_name:
            data_dict[param_name] = np.random.uniform(5, 25, len(dates))
        elif "Soil Wetness" in param_name:
            data_dict[param_name] = np.random.uniform(0.3, 0.8, len(dates))
        else:
            data_dict[param_name] = np.random.uniform(0, 100, len(dates))
    
    df = pd.DataFrame(data_dict)
    df["Date"] = pd.to_datetime(df["Date"])
    
    return df

# ============================================================================
# AREA POINT VALIDATION & SAVING FUNCTIONS
# ============================================================================

def validate_nasa_data_for_save(data_df, area_point_id):
    """
    Validate NASA POWER data before saving to database
    Enforces area_point_id requirement
    """
    errors = []
    
    # Check area_point_id
    if not area_point_id or area_point_id.strip() == "":
        errors.append("Area Point ID is required - cannot save data without selecting an area point")
    
    # Check if dataframe is empty
    if data_df is None or len(data_df) == 0:
        errors.append("No data to save")
    
    # Check required columns
    if 'Date' not in data_df.columns:
        errors.append("Date column is missing")
    
    # Check for at least one environmental variable
    env_vars = ['T2M', 'RH2M', 'PRECTOTCORR', 'WS2M']
    has_env_var = any(var in data_df.columns for var in env_vars)
    if not has_env_var:
        errors.append("No environmental variables found in data")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

def prepare_nasa_data_for_db(data_df, area_point_id, created_by):
    """
    Prepare NASA POWER data for database insertion
    Transforms DataFrame to match environmental_data table schema
    """
    from utils.database import validate_area_point_exists
    
    # Validate area point exists
    validate_area_point_exists(area_point_id)
    
    records = []
    
    for _, row in data_df.iterrows():
        record = {
            'area_point_id': area_point_id,
            'date': row['Date'].strftime('%Y-%m-%d') if isinstance(row['Date'], pd.Timestamp) else str(row['Date']),
            'source': 'nasa_power',
            'created_by': created_by
        }
        
        # Map NASA POWER columns to database columns
        column_mapping = {
            'T2M': 'temperature',
            'T2M_MIN': 't2m_min',
            'T2M_MAX': 't2m_max',
            'RH2M': 'humidity',
            'PRECTOTCORR': 'precipitation',
            'WS2M': 'wind_speed',
            'WS2M_MAX': 'wind_speed_max',
            'WS2M_MIN': 'wind_speed_min',
            'WD2M': 'wind_direction',
            'CLRSKY_SFC_PAR_TOT': 'solar_radiation',
            'ALLSKY_SFC_UVA': 'uva',
            'ALLSKY_SFC_UVB': 'uvb',
            'GWETTOP': 'gwettop'
        }
        
        for nasa_col, db_col in column_mapping.items():
            if nasa_col in row and pd.notna(row[nasa_col]):
                record[db_col] = float(row[nasa_col])
        
        records.append(record)
    
    return records

def save_nasa_data_to_db(data_df, area_point_id, created_by):
    """
    Save NASA POWER data to database with validation
    Returns success/failure counts
    """
    from utils.database import create_environmental_data, log_activity
    
    # Validate before saving
    validation = validate_nasa_data_for_save(data_df, area_point_id)
    if not validation['valid']:
        raise ValueError(f"Validation failed: {', '.join(validation['errors'])}")
    
    # Prepare records
    records = prepare_nasa_data_for_db(data_df, area_point_id, created_by)
    
    success_count = 0
    errors = []
    
    for record in records:
        try:
            create_environmental_data(record)
            success_count += 1
        except Exception as e:
            errors.append({
                'date': record['date'],
                'error': str(e)
            })
    
    # Log activity
    log_activity(
        user=created_by,
        action='import',
        module='environmental',
        entity_type='environmental_data',
        entity_id=area_point_id,
        details={
            'source': 'nasa_power',
            'success_count': success_count,
            'error_count': len(errors),
            'total_records': len(records)
        }
    )
    
    return {
        'success': success_count,
        'failed': len(errors),
        'errors': errors,
        'total': len(records)
    }
