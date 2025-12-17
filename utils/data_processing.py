import pandas as pd
import numpy as np
from datetime import datetime

def process_pest_data(df):
    """Process and clean pest data"""
    df = df.copy()
    
    # Convert date columns
    if 'year' in df.columns and 'month' in df.columns and 'day' in df.columns:
        try:
            df['date'] = pd.to_datetime(df[['year', 'month', 'day']].rename(
                columns={'year': 'year', 'month': 'month', 'day': 'day'}
            ))
        except:
            pass
    
    # Fill missing numeric values with 0
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)
    
    return df

def get_summary_statistics(df, pest_column):
    """Get summary statistics for pest counts"""
    stats = {
        'Total Count': df[pest_column].sum(),
        'Average': df[pest_column].mean(),
        'Median': df[pest_column].median(),
        'Min': df[pest_column].min(),
        'Max': df[pest_column].max(),
        'Std Dev': df[pest_column].std()
    }
    return stats

def get_temporal_aggregation(df, group_by='month'):
    """Aggregate data by time period"""
    if group_by == 'month':
        agg = df.groupby(['year', 'month']).agg({
            'rbb_count': 'sum',
            'wsb_count': 'sum',
            'temperature': 'mean',
            'humidity': 'mean',
            'precipitation': 'sum'
        }).reset_index()
        agg['period'] = agg['year'].astype(str) + '-' + agg['month'].astype(str).str.zfill(2)
    elif group_by == 'year':
        agg = df.groupby('year').agg({
            'rbb_count': 'sum',
            'wsb_count': 'sum',
            'temperature': 'mean',
            'humidity': 'mean',
            'precipitation': 'sum'
        }).reset_index()
        agg['period'] = agg['year'].astype(str)
    else:
        agg = df
    
    return agg

def correlate_with_environment(pest_df, env_df):
    """Correlate pest data with environmental factors"""
    # Merge data
    merged = pd.merge(pest_df, env_df, on=['year', 'week_number'], how='inner')
    
    # Calculate correlations
    numeric_cols = merged.select_dtypes(include=[np.number]).columns
    correlations = merged[numeric_cols].corr()
    
    return correlations

def detect_outliers(df, column, threshold=2):
    """Detect outliers using z-score"""
    mean = df[column].mean()
    std = df[column].std()
    
    outlier_mask = np.abs((df[column] - mean) / std) > threshold
    return df[outlier_mask]

def export_to_csv(df, filename):
    """Export dataframe to CSV"""
    df.to_csv(filename, index=False)
    return filename

def filter_by_area(df, area_codes):
    """Filter data by area code(s)"""
    if 'area_code' not in df.columns or not area_codes:
        return df
    
    df = df[df['area_code'].isin(area_codes)]
    return df

def get_available_areas(df):
    """Get list of unique area codes"""
    if 'area_code' not in df.columns:
        return []
    
    return sorted(df['area_code'].dropna().unique())

def get_area_summary(df, area_code):
    """Get summary statistics for a specific area"""
    area_data = df[df['area_code'] == area_code]
    
    if len(area_data) == 0:
        return None
    
    summary = {
        'Total Records': len(area_data),
        'RBB Total': area_data['rbb_count'].sum() if 'rbb_count' in area_data.columns else 0,
        'WSB Total': area_data['wsb_count'].sum() if 'wsb_count' in area_data.columns else 0,
        'Avg Temperature': area_data['temperature'].mean() if 'temperature' in area_data.columns else 0,
        'Avg Humidity': area_data['humidity'].mean() if 'humidity' in area_data.columns else 0,
        'Date Range': f"{area_data['year'].min()}/{area_data['month'].min():.0f} - {area_data['year'].max()}/{area_data['month'].max():.0f}" if 'year' in area_data.columns else "N/A"
    }
    
    return summary

def compare_areas(df, area_list):
    """Compare statistics across multiple areas"""
    comparison = []
    
    for area in area_list:
        summary = get_area_summary(df, area)
        if summary:
            summary['Area Code'] = area
            comparison.append(summary)
    
    return pd.DataFrame(comparison) if comparison else pd.DataFrame()

# ============================================================================
# DATASET UPLOAD & VALIDATION FUNCTIONS
# ============================================================================

def validate_dataset_schema(df, required_columns):
    """Validate that dataset contains required columns"""
    errors = []
    missing_cols = []
    
    df_cols = [col.lower().strip() for col in df.columns]
    
    for col in required_columns:
        col_lower = col.lower().strip()
        if col_lower not in df_cols:
            missing_cols.append(col)
            errors.append(f"Missing required column: {col}")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'missing_columns': missing_cols
    }

def validate_pest_dataset(df):
    """Validate pest dataset structure"""
    required_columns = ['Year', 'Week_Number', 'Month', 'Day', 'RBB', 'WSB']
    environmental_columns = ['T2M', 'T2M_MIN', 'T2M_MAX', 'RH2M', 'PRECTOTCORR']
    
    errors = []
    warnings = []
    
    # Check required columns
    df_cols_lower = [col.lower() for col in df.columns]
    required_cols_lower = [col.lower() for col in required_columns]
    
    missing = [col for col in required_columns if col.lower() not in df_cols_lower]
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")
    
    # Check for environmental columns (warnings only)
    missing_env = [col for col in environmental_columns if col.lower() not in df_cols_lower]
    if missing_env:
        warnings.append(f"Missing environmental columns: {', '.join(missing_env)}")
    
    # Validate data types and ranges
    if len(df) > 0 and not errors:
        # Year validation
        if 'Year' in df.columns or 'year' in df.columns:
            year_col = 'Year' if 'Year' in df.columns else 'year'
            invalid_years = df[~df[year_col].between(2000, 2100)]
            if len(invalid_years) > 0:
                errors.append(f"Invalid year values found: {len(invalid_years)} rows")
        
        # Month validation
        if 'Month' in df.columns or 'month' in df.columns:
            month_col = 'Month' if 'Month' in df.columns else 'month'
            invalid_months = df[~df[month_col].between(1, 12)]
            if len(invalid_months) > 0:
                errors.append(f"Invalid month values found: {len(invalid_months)} rows")
        
        # Day validation
        if 'Day' in df.columns or 'day' in df.columns:
            day_col = 'Day' if 'Day' in df.columns else 'day'
            invalid_days = df[~df[day_col].between(1, 31)]
            if len(invalid_days) > 0:
                errors.append(f"Invalid day values found: {len(invalid_days)} rows")
        
        # Pest count validation (should be non-negative)
        for pest_col in ['RBB', 'WSB']:
            if pest_col in df.columns:
                negative_counts = df[df[pest_col] < 0]
                if len(negative_counts) > 0:
                    errors.append(f"Negative {pest_col} values found: {len(negative_counts)} rows")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'row_count': len(df),
        'column_count': len(df.columns)
    }

def chop_dataset_by_domain(df):
    """Split dataset into environmental, pest, and metadata domains"""
    
    # Environmental columns
    env_columns = [
        'Year', 'Month', 'Day', 'Week_Number',
        'CLRSKY_SFC_PAR_TOT', 'ALLSKY_SFC_UVA', 'ALLSKY_SFC_UVB',
        'T2M', 'T2M_MIN', 'T2M_MAX', 'RH2M', 'PRECTOTCORR',
        'WS2M', 'WS2M_MAX', 'WS2M_MIN', 'WD2M', 'GWETTOP'
    ]
    
    # Pest columns
    pest_columns = ['Year', 'Month', 'Day', 'Week_Number', 'RBB', 'WSB', 'Moon_Category']
    
    # Metadata columns
    metadata_columns = ['Year', 'Week_Number', 'Month', 'Day']
    
    # Filter columns that exist
    env_cols_exist = [col for col in env_columns if col in df.columns]
    pest_cols_exist = [col for col in pest_columns if col in df.columns]
    
    environmental_df = df[env_cols_exist].copy() if env_cols_exist else pd.DataFrame()
    pest_df = df[pest_cols_exist].copy() if pest_cols_exist else pd.DataFrame()
    metadata_df = df[metadata_columns].copy() if all(c in df.columns for c in metadata_columns) else pd.DataFrame()
    
    # Add date column to all
    for domain_df in [environmental_df, pest_df, metadata_df]:
        if len(domain_df) > 0 and all(c in domain_df.columns for c in ['Year', 'Month', 'Day']):
            try:
                domain_df['date'] = pd.to_datetime(domain_df[['Year', 'Month', 'Day']].rename(
                    columns={'Year': 'year', 'Month': 'month', 'Day': 'day'}
                ))
            except:
                pass
    
    return {
        'environmental': environmental_df,
        'pest': pest_df,
        'metadata': metadata_df
    }

def normalize_column_names(df):
    """Normalize column names to standard format"""
    column_mapping = {
        'year': 'Year',
        'month': 'Month',
        'day': 'Day',
        'week_number': 'Week_Number',
        'rbb': 'RBB',
        'wsb': 'WSB',
        't2m': 'T2M',
        't2m_min': 'T2M_MIN',
        't2m_max': 'T2M_MAX',
        'rh2m': 'RH2M',
        'prectotcorr': 'PRECTOTCORR',
        'ws2m': 'WS2M',
        'ws2m_max': 'WS2M_MAX',
        'ws2m_min': 'WS2M_MIN',
        'wd2m': 'WD2M',
        'gwettop': 'GWETTOP',
        'allsky_sfc_uva': 'ALLSKY_SFC_UVA',
        'allsky_sfc_uvb': 'ALLSKY_SFC_UVB',
        'clrsky_sfc_par_tot': 'CLRSKY_SFC_PAR_TOT'
    }
    
    df_renamed = df.copy()
    current_cols_lower = {col.lower(): col for col in df.columns}
    
    rename_dict = {}
    for lower_key, standard_name in column_mapping.items():
        if lower_key in current_cols_lower:
            rename_dict[current_cols_lower[lower_key]] = standard_name
    
    df_renamed.rename(columns=rename_dict, inplace=True)
    return df_renamed

def prepare_for_database(df, area_point_id, created_by):
    """Prepare dataset for database insertion with area_point_id"""
    df = df.copy()
    
    # Add required fields
    df['area_point_id'] = area_point_id
    df['created_by'] = created_by
    df['created_at'] = datetime.now().isoformat()
    
    # Create date column if not exists
    if 'date' not in df.columns and all(c in df.columns for c in ['Year', 'Month', 'Day']):
        try:
            df['date'] = pd.to_datetime(df[['Year', 'Month', 'Day']].rename(
                columns={'Year': 'year', 'Month': 'month', 'Day': 'day'}
            )).dt.date
        except:
            pass
    
    return df

def validate_environmental_data(data_dict):
    """Validate environmental data before saving"""
    errors = []
    
    # Required fields
    required = ['area_point_id', 'date', 'source']
    for field in required:
        if field not in data_dict or not data_dict[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate source
    valid_sources = ['nasa_power', 'microclimate', 'manual']
    if 'source' in data_dict and data_dict['source'] not in valid_sources:
        errors.append(f"Invalid source. Must be one of: {', '.join(valid_sources)}")
    
    # Validate date format
    if 'date' in data_dict:
        try:
            pd.to_datetime(data_dict['date'])
        except:
            errors.append(f"Invalid date format: {data_dict['date']}")
    
    # Validate numeric ranges
    if 'temperature' in data_dict and data_dict['temperature'] is not None:
        if not -50 <= data_dict['temperature'] <= 60:
            errors.append(f"Temperature out of range: {data_dict['temperature']}°C")
    
    if 'humidity' in data_dict and data_dict['humidity'] is not None:
        if not 0 <= data_dict['humidity'] <= 100:
            errors.append(f"Humidity out of range: {data_dict['humidity']}%")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

def validate_pest_record(data_dict):
    """Validate pest record before saving"""
    errors = []
    
    # Required fields
    required = ['area_point_id', 'pest_type', 'date']
    for field in required:
        if field not in data_dict or not data_dict[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate pest_type
    if 'pest_type' in data_dict and data_dict['pest_type'] not in ['rbb', 'wsb']:
        errors.append(f"Invalid pest_type. Must be 'rbb' or 'wsb'")
    
    # Validate count (must be non-negative)
    if 'count' in data_dict and data_dict['count'] is not None:
        if data_dict['count'] < 0:
            errors.append(f"Count cannot be negative: {data_dict['count']}")
    
    # Validate density (must be non-negative)
    if 'density' in data_dict and data_dict['density'] is not None:
        if data_dict['density'] < 0:
            errors.append(f"Density cannot be negative: {data_dict['density']}")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }
