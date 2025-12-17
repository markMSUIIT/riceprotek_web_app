#!/usr/bin/env python3
"""Initialize MongoDB database with collections and indexes"""

from utils.database import init_database

if __name__ == "__main__":
    print("Initializing MongoDB database...")
    try:
        init_database()
        print("MongoDB database initialized successfully!")
        print("All collections created with proper indexes.")
    except Exception as e:
        print(f"Error initializing database: {e}")
