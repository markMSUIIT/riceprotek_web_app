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
    
    # Create pest records table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pest_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            day INTEGER NOT NULL,
            latitude REAL,
            longitude REAL,
            cluster INTEGER,
            area_code TEXT,
            rbb_count INTEGER,
            wsb_count INTEGER,
            temperature REAL,
            max_temp REAL,
            min_temp REAL,
            humidity REAL,
            precipitation REAL,
            insect_id INTEGER,
            count INTEGER,
            time_observed TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create monitoring points/locations table
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
