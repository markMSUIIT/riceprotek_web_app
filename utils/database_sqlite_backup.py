import sqlite3
import pandas as pd
from pathlib import Path
import json

DB_PATH = Path("data/pest_management.db")

def init_database():
    """Initialize SQLite database with tables"""
    DB_PATH.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create area_points table (Core entity - MUST BE FIRST)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS area_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_point_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            cluster INTEGER,
            municipality TEXT,
            barangay TEXT,
            description TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_by TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create environmental_data table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS environmental_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_point_id TEXT NOT NULL,
            date DATE NOT NULL,
            source TEXT NOT NULL CHECK(source IN ('nasa_power', 'microclimate', 'manual')),
            temperature REAL,
            t2m_min REAL,
            t2m_max REAL,
            humidity REAL,
            precipitation REAL,
            wind_speed REAL,
            wind_speed_max REAL,
            wind_speed_min REAL,
            wind_direction REAL,
            solar_radiation REAL,
            uva REAL,
            uvb REAL,
            gwettop REAL,
            soil_temp REAL,
            soil_moisture REAL,
            created_by TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(area_point_id, date, source),
            FOREIGN KEY (area_point_id) REFERENCES area_points(area_point_id) ON DELETE CASCADE
        )
    ''')
    
    # Create pest records table with enhanced schema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pest_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_point_id TEXT,
            pest_type TEXT CHECK(pest_type IN ('rbb', 'wsb')),
            date DATE,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            day INTEGER NOT NULL,
            week_number INTEGER,
            latitude REAL,
            longitude REAL,
            cluster INTEGER,
            area_code TEXT,
            rbb_count INTEGER DEFAULT 0,
            wsb_count INTEGER DEFAULT 0,
            count INTEGER,
            density REAL,
            temperature REAL,
            max_temp REAL,
            min_temp REAL,
            humidity REAL,
            precipitation REAL,
            insect_id INTEGER,
            time_observed TEXT,
            notes TEXT,
            image_path TEXT,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (area_point_id) REFERENCES area_points(area_point_id) ON DELETE SET NULL
        )
    ''')
    
    # Create dataset_uploads table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dataset_uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            uploader TEXT NOT NULL,
            upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            row_count INTEGER,
            validation_status TEXT CHECK(validation_status IN ('valid', 'invalid', 'partial')),
            validation_errors TEXT,
            file_path TEXT,
            file_size INTEGER,
            columns_detected TEXT,
            processing_status TEXT DEFAULT 'pending' CHECK(processing_status IN ('pending', 'processing', 'completed', 'failed'))
        )
    ''')
    
    # Create dataset_processing table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dataset_processing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upload_id INTEGER NOT NULL,
            domain TEXT NOT NULL CHECK(domain IN ('environmental', 'pest', 'metadata')),
            records_processed INTEGER DEFAULT 0,
            records_failed INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'processing', 'completed', 'failed')),
            error_log TEXT,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (upload_id) REFERENCES dataset_uploads(id) ON DELETE CASCADE
        )
    ''')
    
    # Create activity_logs table (CRITICAL for audit trail)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            action TEXT NOT NULL CHECK(action IN ('upload', 'create', 'read', 'update', 'delete', 'login', 'logout', 'export', 'import')),
            module TEXT NOT NULL CHECK(module IN ('dataset', 'environmental', 'pest', 'area_point', 'auth', 'visualization', 'settings')),
            entity_type TEXT,
            entity_id TEXT,
            details TEXT,
            ip_address TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create monitoring points/locations table (kept for backward compatibility)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monitoring_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            point_number INTEGER UNIQUE NOT NULL,
            municipality TEXT NOT NULL,
            cluster INTEGER,
            barangay TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            area_name TEXT,
            notes TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create insects/pest types table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS insects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            scientific_name TEXT,
            description TEXT,
            image_url TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def load_csv_to_db(csv_path, table_name):
    """Load CSV data into database"""
    df = pd.read_csv(csv_path)
    conn = sqlite3.connect(DB_PATH)
    
    if table_name == "pest_records":
        df.columns = [col.lower().replace(' ', '_').replace('_temp', '_temp') for col in df.columns]
        df.to_sql('pest_records', conn, if_exists='append', index=False)
    elif table_name == "environmental_factors":
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        df.to_sql('environmental_factors', conn, if_exists='append', index=False)
    
    conn.commit()
    conn.close()

def create_record(table_name, data):
    """Create a new record"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['?' for _ in data.keys()])
    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    
    cursor.execute(query, tuple(data.values()))
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    
    return record_id

def read_records(table_name, filters=None):
    """Read records from database"""
    conn = sqlite3.connect(DB_PATH)
    
    try:
        query = f"SELECT * FROM {table_name}"
        
        if filters:
            conditions = [f"{k}=?" for k in filters.keys()]
            query += " WHERE " + " AND ".join(conditions)
            df = pd.read_sql_query(query, conn, params=list(filters.values()))
        else:
            df = pd.read_sql_query(query, conn)
    
    except pd.errors.DatabaseError as e:
        if "no such table" in str(e):
            # Table doesn't exist, create it
            init_database()
            # Try again
            query = f"SELECT * FROM {table_name}"
            if filters:
                conditions = [f"{k}=?" for k in filters.keys()]
                query += " WHERE " + " AND ".join(conditions)
                df = pd.read_sql_query(query, conn, params=list(filters.values()))
            else:
                df = pd.read_sql_query(query, conn)
        else:
            raise
    finally:
        conn.close()
    
    return df

def update_record(table_name, record_id, data):
    """Update a record"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    set_clause = ', '.join([f"{k}=?" for k in data.keys()])
    query = f"UPDATE {table_name} SET {set_clause}, updated_at=CURRENT_TIMESTAMP WHERE id=?"
    
    cursor.execute(query, list(data.values()) + [record_id])
    conn.commit()
    conn.close()

def delete_record(table_name, record_id):
    """Delete a record"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(f"DELETE FROM {table_name} WHERE id=?", (record_id,))
    conn.commit()
    conn.close()

def get_record_by_id(table_name, record_id):
    """Get a single record by ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(f"SELECT * FROM {table_name} WHERE id=?", (record_id,))
    columns = [description[0] for description in cursor.description]
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(zip(columns, row))
    return None

def get_table_columns(table_name):
    """Get column names from a table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    conn.close()
    
    return columns

def get_monitoring_points():
    """Get all monitoring points"""
    return read_records("monitoring_points")

def get_monitoring_point_by_number(point_number):
    """Get monitoring point by point number"""
    return read_records("monitoring_points", filters={"point_number": point_number})

def get_monitoring_point_by_id(point_id):
    """Get monitoring point by ID"""
    return get_record_by_id("monitoring_points", point_id)

def create_monitoring_point(data):
    """Create a new monitoring point"""
    return create_record("monitoring_points", data)

def update_monitoring_point(point_id, data):
    """Update a monitoring point"""
    return update_record("monitoring_points", point_id, data)

def delete_monitoring_point(point_id):
    """Delete a monitoring point"""
    return delete_record("monitoring_points", point_id)

# ============================================================================
# AREA POINTS FUNCTIONS
# ============================================================================

def create_area_point(data):
    """Create a new area point - MANDATORY before saving any data"""
    required_fields = ['area_point_id', 'name', 'latitude', 'longitude', 'created_by']
    for field in required_fields:
        if field not in data or not data[field]:
            raise ValueError(f"Missing required field: {field}")
    
    return create_record("area_points", data)

def get_area_points(filters=None, active_only=True):
    """Get area points with optional filters"""
    if active_only:
        filters = filters or {}
        filters['is_active'] = 1
    return read_records("area_points", filters)

def get_area_point_by_id(area_point_id):
    """Get area point by area_point_id"""
    df = read_records("area_points", filters={"area_point_id": area_point_id})
    return df.iloc[0].to_dict() if len(df) > 0 else None

def update_area_point(area_point_id, data):
    """Update an area point"""
    df = read_records("area_points", filters={"area_point_id": area_point_id})
    if len(df) == 0:
        raise ValueError(f"Area point {area_point_id} not found")
    record_id = df.iloc[0]['id']
    return update_record("area_points", record_id, data)

def delete_area_point(area_point_id):
    """Soft delete an area point"""
    df = read_records("area_points", filters={"area_point_id": area_point_id})
    if len(df) == 0:
        raise ValueError(f"Area point {area_point_id} not found")
    record_id = df.iloc[0]['id']
    return update_record("area_points", record_id, {"is_active": 0})

def validate_area_point_exists(area_point_id):
    """Validate that an area point exists and is active"""
    point = get_area_point_by_id(area_point_id)
    if not point:
        raise ValueError(f"Area point '{area_point_id}' does not exist")
    if not point.get('is_active', 0):
        raise ValueError(f"Area point '{area_point_id}' is not active")
    return True

# ============================================================================
# ENVIRONMENTAL DATA FUNCTIONS
# ============================================================================

def create_environmental_data(data):
    """Create environmental data record - requires area_point_id"""
    required_fields = ['area_point_id', 'date', 'source', 'created_by']
    for field in required_fields:
        if field not in data or not data[field]:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate area point exists
    validate_area_point_exists(data['area_point_id'])
    
    # Validate source
    valid_sources = ['nasa_power', 'microclimate', 'manual']
    if data['source'] not in valid_sources:
        raise ValueError(f"Source must be one of: {', '.join(valid_sources)}")
    
    return create_record("environmental_data", data)

def get_environmental_data(area_point_id=None, date_from=None, date_to=None, source=None):
    """Get environmental data with filters"""
    filters = {}
    if area_point_id:
        filters['area_point_id'] = area_point_id
    if source:
        filters['source'] = source
    
    df = read_records("environmental_data", filters if filters else None)
    
    if date_from:
        df = df[pd.to_datetime(df['date']) >= pd.to_datetime(date_from)]
    if date_to:
        df = df[pd.to_datetime(df['date']) <= pd.to_datetime(date_to)]
    
    return df

def bulk_create_environmental_data(data_list, created_by):
    """Bulk insert environmental data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    success_count = 0
    errors = []
    
    for data in data_list:
        try:
            data['created_by'] = created_by
            validate_area_point_exists(data['area_point_id'])
            
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data.keys()])
            query = f"INSERT INTO environmental_data ({columns}) VALUES ({placeholders})"
            
            cursor.execute(query, tuple(data.values()))
            success_count += 1
        except Exception as e:
            errors.append({"data": data, "error": str(e)})
    
    conn.commit()
    conn.close()
    
    return {"success": success_count, "failed": len(errors), "errors": errors}

# ============================================================================
# ENHANCED PEST RECORDS FUNCTIONS
# ============================================================================

def create_pest_record(data):
    """Create pest record - requires area_point_id and pest_type"""
    # Validate required fields
    if 'area_point_id' not in data or not data['area_point_id']:
        raise ValueError("area_point_id is required")
    if 'pest_type' not in data or not data['pest_type']:
        raise ValueError("pest_type is required")
    
    # Validate area point exists
    validate_area_point_exists(data['area_point_id'])
    
    # Validate pest_type
    if data['pest_type'] not in ['rbb', 'wsb']:
        raise ValueError("pest_type must be either 'rbb' or 'wsb'")
    
    return create_record("pest_records", data)

def get_pest_records_by_area(area_point_id, pest_type=None, date_from=None, date_to=None):
    """Get pest records for a specific area point"""
    filters = {'area_point_id': area_point_id}
    if pest_type:
        filters['pest_type'] = pest_type
    
    df = read_records("pest_records", filters)
    
    if date_from:
        df = df[pd.to_datetime(df['date']) >= pd.to_datetime(date_from)]
    if date_to:
        df = df[pd.to_datetime(df['date']) <= pd.to_datetime(date_to)]
    
    return df

# ============================================================================
# DATASET UPLOAD FUNCTIONS
# ============================================================================

def create_dataset_upload(data):
    """Create dataset upload record"""
    required_fields = ['filename', 'original_filename', 'uploader']
    for field in required_fields:
        if field not in data or not data[field]:
            raise ValueError(f"Missing required field: {field}")
    
    return create_record("dataset_uploads", data)

def get_dataset_uploads(uploader=None):
    """Get dataset uploads"""
    filters = {'uploader': uploader} if uploader else None
    return read_records("dataset_uploads", filters)

def update_dataset_upload(upload_id, data):
    """Update dataset upload"""
    return update_record("dataset_uploads", upload_id, data)

def create_dataset_processing(data):
    """Create dataset processing record"""
    required_fields = ['upload_id', 'domain']
    for field in required_fields:
        if field not in data or not data[field]:
            raise ValueError(f"Missing required field: {field}")
    
    return create_record("dataset_processing", data)

def update_dataset_processing(processing_id, data):
    """Update dataset processing"""
    return update_record("dataset_processing", processing_id, data)

# ============================================================================
# ACTIVITY LOGGING FUNCTIONS (CRITICAL)
# ============================================================================

def log_activity(user, action, module, entity_type=None, entity_id=None, details=None, ip_address=None):
    """Log user activity - MUST be called for every action"""
    data = {
        'user': user,
        'action': action,
        'module': module,
        'entity_type': entity_type,
        'entity_id': str(entity_id) if entity_id else None,
        'details': json.dumps(details) if isinstance(details, dict) else details,
        'ip_address': ip_address
    }
    
    # Validate action and module
    valid_actions = ['upload', 'create', 'read', 'update', 'delete', 'login', 'logout', 'export', 'import']
    valid_modules = ['dataset', 'environmental', 'pest', 'area_point', 'auth', 'visualization', 'settings']
    
    if action not in valid_actions:
        raise ValueError(f"Invalid action: {action}")
    if module not in valid_modules:
        raise ValueError(f"Invalid module: {module}")
    
    return create_record("activity_logs", data)

def get_activity_logs(user=None, module=None, action=None, limit=100):
    """Get activity logs with filters"""
    conn = sqlite3.connect(DB_PATH)
    
    query = "SELECT * FROM activity_logs WHERE 1=1"
    params = []
    
    if user:
        query += " AND user=?"
        params.append(user)
    if module:
        query += " AND module=?"
        params.append(module)
    if action:
        query += " AND action=?"
        params.append(action)
    
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return df
