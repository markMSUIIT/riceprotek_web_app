"""
Pest Management Module
Handles pest record creation, validation, and retrieval with mandatory area point enforcement
"""

import pandas as pd
from datetime import datetime
from utils.database import (
    create_pest_record, read_records, update_record, delete_record,
    validate_area_point_exists, log_activity
)
from utils.data_processing import validate_pest_record
from pathlib import Path
import json

# Pest type ENUM - ONLY these values allowed
PEST_TYPES = ['rbb', 'wsb']

PEST_INFO = {
    'rbb': {
        'name': 'Rice Black Bug',
        'scientific_name': 'Scotinophara coarctata',
        'description': 'A major rice pest that feeds on the rice plant sap'
    },
    'wsb': {
        'name': 'White Stem Borer',
        'scientific_name': 'Scirpophaga innotata',
        'description': 'A moth larvae that bores into rice stems'
    }
}

def create_pest_observation(data, created_by, image_file=None):
    """
    Create a new pest observation record
    
    Required fields:
    - area_point_id: Must exist and be active
    - pest_type: Must be 'rbb' or 'wsb'
    - date: Observation date
    - count or density: Pest population measure
    
    Optional fields:
    - notes: Additional observations
    - image_file: Image upload
    """
    
    # Validate required fields
    validation = validate_pest_record(data)
    if not validation['valid']:
        raise ValueError(f"Validation failed: {', '.join(validation['errors'])}")
    
    # Validate area point exists
    validate_area_point_exists(data['area_point_id'])
    
    # Add metadata
    data['created_by'] = created_by
    
    # Handle image upload if provided
    if image_file:
        image_path = save_pest_image(image_file, data['area_point_id'], data['pest_type'])
        data['image_path'] = image_path
    
    # Create record
    record_id = create_pest_record(data)
    
    # Log activity
    log_activity(
        user=created_by,
        action='create',
        module='pest',
        entity_type='pest_records',
        entity_id=record_id,
        details={'pest_type': data['pest_type'], 'area_point_id': data['area_point_id']}
    )
    
    return record_id

def get_pest_observations(area_point_id=None, pest_type=None, date_from=None, date_to=None):
    """Get pest observations with filters"""
    
    filters = {}
    if area_point_id:
        filters['area_point_id'] = area_point_id
    if pest_type:
        if pest_type not in PEST_TYPES:
            raise ValueError(f"Invalid pest_type. Must be one of: {', '.join(PEST_TYPES)}")
        filters['pest_type'] = pest_type
    
    df = read_records("pest_records", filters if filters else None)
    
    # Apply date filters
    if len(df) > 0 and 'date' in df.columns:
        if date_from:
            df = df[pd.to_datetime(df['date']) >= pd.to_datetime(date_from)]
        if date_to:
            df = df[pd.to_datetime(df['date']) <= pd.to_datetime(date_to)]
    
    return df

def update_pest_observation(record_id, data, updated_by):
    """Update a pest observation"""
    
    # Validate if pest_type is being changed
    if 'pest_type' in data and data['pest_type'] not in PEST_TYPES:
        raise ValueError(f"Invalid pest_type. Must be one of: {', '.join(PEST_TYPES)}")
    
    # Validate if area_point_id is being changed
    if 'area_point_id' in data:
        validate_area_point_exists(data['area_point_id'])
    
    # Update record
    update_record("pest_records", record_id, data)
    
    # Log activity
    log_activity(
        user=updated_by,
        action='update',
        module='pest',
        entity_type='pest_records',
        entity_id=record_id,
        details={'updated_fields': list(data.keys())}
    )
    
    return True

def delete_pest_observation(record_id, deleted_by):
    """Delete a pest observation"""
    
    delete_record("pest_records", record_id)
    
    # Log activity
    log_activity(
        user=deleted_by,
        action='delete',
        module='pest',
        entity_type='pest_records',
        entity_id=record_id,
        details=None
    )
    
    return True

def calculate_pest_density(count, area_sq_meters):
    """Calculate pest density per square meter"""
    if area_sq_meters <= 0:
        raise ValueError("Area must be greater than 0")
    return count / area_sq_meters

def get_pest_summary(area_point_id=None, date_from=None, date_to=None):
    """Get summary statistics for pest observations"""
    
    df = get_pest_observations(area_point_id, None, date_from, date_to)
    
    if len(df) == 0:
        return {
            'total_observations': 0,
            'rbb_total': 0,
            'wsb_total': 0,
            'rbb_avg': 0,
            'wsb_avg': 0
        }
    
    summary = {
        'total_observations': len(df),
        'rbb_total': df[df['pest_type'] == 'rbb']['count'].sum() if 'count' in df.columns else 0,
        'wsb_total': df[df['pest_type'] == 'wsb']['count'].sum() if 'count' in df.columns else 0,
        'rbb_avg': df[df['pest_type'] == 'rbb']['count'].mean() if 'count' in df.columns else 0,
        'wsb_avg': df[df['pest_type'] == 'wsb']['count'].mean() if 'count' in df.columns else 0,
        'date_range': {
            'from': df['date'].min() if 'date' in df.columns else None,
            'to': df['date'].max() if 'date' in df.columns else None
        }
    }
    
    return summary

def get_pest_info(pest_type):
    """Get information about a pest type"""
    if pest_type not in PEST_TYPES:
        raise ValueError(f"Invalid pest_type. Must be one of: {', '.join(PEST_TYPES)}")
    return PEST_INFO.get(pest_type, {})

def save_pest_image(image_file, area_point_id, pest_type):
    """Save uploaded pest image"""
    
    # Create images directory
    img_dir = Path("data/pest_images")
    img_dir.mkdir(exist_ok=True, parents=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = Path(image_file.name).suffix
    filename = f"{area_point_id}_{pest_type}_{timestamp}{ext}"
    
    filepath = img_dir / filename
    
    # Save file
    with open(filepath, 'wb') as f:
        f.write(image_file.getbuffer())
    
    return str(filepath)

def bulk_import_pest_data(df, area_point_id, created_by):
    """
    Bulk import pest data from DataFrame
    Requires area_point_id to be specified - cannot be null
    """
    
    if not area_point_id:
        raise ValueError("area_point_id is required for bulk import")
    
    # Validate area point exists
    validate_area_point_exists(area_point_id)
    
    success_count = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            # Prepare record
            record = {
                'area_point_id': area_point_id,
                'date': row.get('date'),
                'year': row.get('Year', row.get('year')),
                'month': row.get('Month', row.get('month')),
                'day': row.get('Day', row.get('day')),
                'week_number': row.get('Week_Number', row.get('week_number')),
                'created_by': created_by
            }
            
            # Add RBB data
            if 'RBB' in row and row['RBB'] > 0:
                rbb_record = record.copy()
                rbb_record['pest_type'] = 'rbb'
                rbb_record['count'] = int(row['RBB'])
                rbb_record['rbb_count'] = int(row['RBB'])
                create_pest_record(rbb_record)
                success_count += 1
            
            # Add WSB data
            if 'WSB' in row and row['WSB'] > 0:
                wsb_record = record.copy()
                wsb_record['pest_type'] = 'wsb'
                wsb_record['count'] = int(row['WSB'])
                wsb_record['wsb_count'] = int(row['WSB'])
                create_pest_record(wsb_record)
                success_count += 1
                
        except Exception as e:
            errors.append({'row': idx, 'error': str(e)})
    
    # Log activity
    log_activity(
        user=created_by,
        action='import',
        module='pest',
        entity_type='pest_records',
        entity_id=area_point_id,
        details={
            'success_count': success_count,
            'error_count': len(errors),
            'total_rows': len(df)
        }
    )
    
    return {
        'success': success_count,
        'failed': len(errors),
        'errors': errors
    }
