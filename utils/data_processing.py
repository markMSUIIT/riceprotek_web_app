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
