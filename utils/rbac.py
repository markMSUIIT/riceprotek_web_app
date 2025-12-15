import streamlit as st
import sqlite3
from pathlib import Path
from datetime import datetime
import hashlib

# Database initialization
DB_PATH = Path("data/pest_management.db")

# Role-based permissions mapping
ROLE_PERMISSIONS = {
    'super_admin': [
        'User Management',
        'View Reports',
        'Manage Settings',
        'Data Entry',
        'View Analytics',
        'Filter Data'
    ],
    'admin': [
        'User Management',
        'View Reports',
        'Data Entry',
        'View Analytics',
        'Filter Data'
    ],
    'encoder': [
        'Data Entry'
    ],
    'analyst': [
        'View Analytics',
        'Filter Data',
        'View Reports'
    ]
}

def init_roles_and_users():
    """Initialize roles and super admin user"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create roles table
    c.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            permissions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create users table with role
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            role_id INTEGER NOT NULL,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (role_id) REFERENCES roles(id)
        )
    ''')
    
    # Create user activity log
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default roles if not exist
    roles_data = [
        ('super_admin', 'Super Administrator - Full system access', 'all'),
        ('admin', 'Administrator - User and role management', 'user_management,view_reports'),
        ('encoder', 'Data Encoder - Data entry only', 'data_entry'),
        ('analyst', 'Data Analyst - View and analyze data', 'view_data,view_analytics,filter_data')
    ]
    
    for role_name, description, permissions in roles_data:
        try:
            c.execute('INSERT INTO roles (name, description, permissions) VALUES (?, ?, ?)',
                     (role_name, description, permissions))
        except sqlite3.IntegrityError:
            pass
    
    # Insert super admin user if not exist
    super_admin_password = hash_password("admin123")
    try:
        c.execute('''
            INSERT INTO users (username, email, password_hash, role_id, created_by, is_active)
            VALUES (?, ?, ?, (SELECT id FROM roles WHERE name = 'super_admin'), ?, 1)
        ''', ("18markian", "superadmin@riceprotek.com", super_admin_password, "system"))
    except sqlite3.IntegrityError:
        pass
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """Verify password against hash"""
    return hash_password(password) == password_hash

def authenticate_user(username, password):
    """Authenticate user and return user info"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        SELECT u.id, u.username, u.email, u.role_id, r.name as role_name, r.permissions
        FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.username = ? AND u.is_active = 1
    ''', (username,))
    
    user = c.fetchone()
    
    if user:
        user_id, uname, email, role_id, role_name, permissions = user
        
        # Check password
        c.execute('SELECT password_hash FROM users WHERE id = ?', (user_id,))
        password_hash = c.fetchone()[0]
        
        if verify_password(password, password_hash):
            # Update last login
            c.execute('UPDATE users SET last_login = ? WHERE id = ?', 
                     (datetime.now(), user_id))
            
            # Log activity
            c.execute('INSERT INTO user_activity (username, action, details) VALUES (?, ?, ?)',
                     (username, 'LOGIN', 'User logged in'))
            conn.commit()
            conn.close()
            
            return {
                'id': user_id,
                'username': uname,
                'email': email,
                'role_id': role_id,
                'role': role_name,
                'permissions': permissions.split(',') if permissions else []
            }
    
    conn.close()
    return None

def create_user(username, email, password, role_name, created_by):
    """Create new user (only super_admin and admin can do this)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get role id
        c.execute('SELECT id FROM roles WHERE name = ?', (role_name,))
        role = c.fetchone()
        
        if not role:
            return False, "❌ Role not found"
        
        role_id = role[0]
        password_hash = hash_password(password)
        
        c.execute('''
            INSERT INTO users (username, email, password_hash, role_id, created_by, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (username, email, password_hash, role_id, created_by))
        
        # Log activity
        c.execute('INSERT INTO user_activity (username, action, details) VALUES (?, ?, ?)',
                 (created_by, 'CREATE_USER', f'Created user {username} with role {role_name}'))
        
        conn.commit()
        conn.close()
        
        return True, f"✅ User '{username}' created successfully with role '{role_name}'"
    
    except sqlite3.IntegrityError as e:
        if 'username' in str(e):
            return False, "❌ Username already exists"
        elif 'email' in str(e):
            return False, "❌ Email already exists"
        else:
            return False, f"❌ Error: {str(e)}"
    
    except Exception as e:
        return False, f"❌ Error creating user: {str(e)}"

def get_all_users():
    """Get all users with their roles"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        SELECT u.id, u.username, u.email, r.name as role, u.is_active, u.created_at, u.last_login
        FROM users u
        JOIN roles r ON u.role_id = r.id
        ORDER BY u.created_at DESC
    ''')
    
    users = c.fetchall()
    conn.close()
    
    return users

def delete_user(user_id, deleted_by):
    """Deactivate user"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get username before deletion
        c.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        result = c.fetchone()
        
        if result:
            username = result[0]
            c.execute('UPDATE users SET is_active = 0 WHERE id = ?', (user_id,))
            
            # Log activity
            c.execute('INSERT INTO user_activity (username, action, details) VALUES (?, ?, ?)',
                     (deleted_by, 'DELETE_USER', f'Deactivated user {username}'))
            
            conn.commit()
            conn.close()
            return True, f"✅ User '{username}' deactivated"
        
        conn.close()
        return False, "❌ User not found"
    
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

def update_user_role(user_id, new_role_name, updated_by):
    """Update user role"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get role id
        c.execute('SELECT id FROM roles WHERE name = ?', (new_role_name,))
        role = c.fetchone()
        
        if not role:
            return False, "❌ Role not found"
        
        role_id = role[0]
        
        # Get username
        c.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        result = c.fetchone()
        
        if result:
            username = result[0]
            c.execute('UPDATE users SET role_id = ? WHERE id = ?', (role_id, user_id))
            
            # Log activity
            c.execute('INSERT INTO user_activity (username, action, details) VALUES (?, ?, ?)',
                     (updated_by, 'UPDATE_ROLE', f'Changed {username} role to {new_role_name}'))
            
            conn.commit()
            conn.close()
            return True, f"✅ User '{username}' role updated to '{new_role_name}'"
        
        conn.close()
        return False, "❌ User not found"
    
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

def has_permission(user_info, required_permission):
    """Check if user has required permission"""
    if not user_info:
        return False
    
    # Super admin has all permissions
    if user_info['role'] == 'super_admin':
        return True
    
    return required_permission in user_info['permissions']

def can_manage_users(user_info):
    """Check if user can manage other users"""
    if not user_info:
        return False
    
    return user_info['role'] in ['super_admin', 'admin']

def can_encode_data(user_info):
    """Check if user can encode data"""
    if not user_info:
        return False
    
    return user_info['role'] in ['super_admin', 'encoder']

def can_view_analytics(user_info):
    """Check if user can view analytics"""
    if not user_info:
        return False
    
    return user_info['role'] in ['super_admin', 'analyst']

def get_activity_log(limit=50):
    """Get user activity log"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        SELECT username, action, details, timestamp
        FROM user_activity
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    
    activities = c.fetchall()
    conn.close()
    
    return activities

def log_action(username, action, details=""):
    """Log user action"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('INSERT INTO user_activity (username, action, details) VALUES (?, ?, ?)',
             (username, action, details))
    
    conn.commit()
    conn.close()
