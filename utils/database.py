from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError, ConnectionFailure
import pandas as pd
from datetime import datetime
import json
from typing import Optional, List, Dict, Any
import certifi
import urllib.parse

# MongoDB connection string with URL encoding for password
username = "reymarkdelena_db_user"
password = urllib.parse.quote_plus("yxjFkimMsVaRx1jf")
MONGO_URI = f"mongodb+srv://{username}:{password}@cluster0.082yzmb.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = "riceprotek_db"

# Global connection
_client = None
_db = None

def get_db():
    """Get MongoDB database connection"""
    global _client, _db
    if _client is None:
        try:
            # Use certifi for SSL certificates with additional options
            _client = MongoClient(
                MONGO_URI,
                tlsCAFile=certifi.where(),
                tlsAllowInvalidCertificates=False,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000
            )
            _db = _client[DB_NAME]
            # Test connection
            _client.admin.command('ping')
            print("Connected to MongoDB successfully!")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            print("Please check:")
            print("1. MongoDB Atlas cluster is running")
            print("2. IP address is whitelisted in MongoDB Atlas")
            print("3. Username and password are correct")
            raise
    return _db

def close_connection():
    """Close MongoDB connection"""
    global _client
    if _client:
        _client.close()
        _client = None

def init_database():
    """Initialize MongoDB database with collections and indexes"""
    db = get_db()
    
    # Create collections with validation
    
    # Area Points collection
    if "area_points" not in db.list_collection_names():
        db.create_collection("area_points")
    db.area_points.create_index([("area_point_id", ASCENDING)], unique=True)
    db.area_points.create_index([("is_active", ASCENDING)])
    
    # Environmental Data collection
    if "environmental_data" not in db.list_collection_names():
        db.create_collection("environmental_data")
    db.environmental_data.create_index([("area_point_id", ASCENDING), ("date", ASCENDING), ("source", ASCENDING)], unique=True)
    db.environmental_data.create_index([("area_point_id", ASCENDING)])
    db.environmental_data.create_index([("date", DESCENDING)])
    
    # Pest Records collection
    if "pest_records" not in db.list_collection_names():
        db.create_collection("pest_records")
    db.pest_records.create_index([("area_point_id", ASCENDING)])
    db.pest_records.create_index([("pest_type", ASCENDING)])
    db.pest_records.create_index([("date", DESCENDING)])
    
    # Dataset Uploads collection
    if "dataset_uploads" not in db.list_collection_names():
        db.create_collection("dataset_uploads")
    db.dataset_uploads.create_index([("uploaded_at", DESCENDING)])
    db.dataset_uploads.create_index([("uploaded_by", ASCENDING)])
    
    # Dataset Processing collection
    if "dataset_processing" not in db.list_collection_names():
        db.create_collection("dataset_processing")
    db.dataset_processing.create_index([("upload_id", ASCENDING)])
    
    # Activity Logs collection
    if "activity_logs" not in db.list_collection_names():
        db.create_collection("activity_logs")
    db.activity_logs.create_index([("timestamp", DESCENDING)])
    db.activity_logs.create_index([("user", ASCENDING)])
    db.activity_logs.create_index([("module", ASCENDING)])
    
    # Monitoring Points collection (legacy - keep for compatibility)
    if "monitoring_points" not in db.list_collection_names():
        db.create_collection("monitoring_points")
    
    print("Database initialized successfully!")

# ==================== AREA POINTS ====================

def create_area_point(area_point_id: str, name: str, latitude: float, longitude: float,
                     cluster: Optional[int] = None, municipality: Optional[str] = None,
                     barangay: Optional[str] = None, description: Optional[str] = None,
                     created_by: str = "system") -> Optional[str]:
    """Create a new area point"""
    db = get_db()
    try:
        doc = {
            "area_point_id": area_point_id,
            "name": name,
            "latitude": latitude,
            "longitude": longitude,
            "cluster": cluster,
            "municipality": municipality,
            "barangay": barangay,
            "description": description,
            "is_active": True,
            "created_by": created_by,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        result = db.area_points.insert_one(doc)
        log_activity(created_by, "create", "area_point", "area_point", area_point_id)
        return str(result.inserted_id)
    except DuplicateKeyError:
        print(f"Area point {area_point_id} already exists")
        return None

def get_area_points(is_active: Optional[bool] = None) -> pd.DataFrame:
    """Get all area points"""
    db = get_db()
    query = {}
    if is_active is not None:
        query["is_active"] = is_active
    
    cursor = db.area_points.find(query).sort("created_at", DESCENDING)
    data = list(cursor)
    
    if not data:
        return pd.DataFrame()
    
    # Convert ObjectId to string and format dates
    for doc in data:
        doc["_id"] = str(doc["_id"])
        if "created_at" in doc:
            doc["created_at"] = doc["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        if "updated_at" in doc:
            doc["updated_at"] = doc["updated_at"].strftime("%Y-%m-%d %H:%M:%S")
    
    return pd.DataFrame(data)

def get_area_point_by_id(area_point_id: str) -> Optional[Dict]:
    """Get specific area point by area_point_id"""
    db = get_db()
    return db.area_points.find_one({"area_point_id": area_point_id})

def validate_area_point_exists(area_point_id: str) -> bool:
    """Validate that area point exists"""
    return get_area_point_by_id(area_point_id) is not None

def update_area_point(area_point_id: str, **kwargs) -> bool:
    """Update area point"""
    db = get_db()
    kwargs["updated_at"] = datetime.now()
    result = db.area_points.update_one(
        {"area_point_id": area_point_id},
        {"$set": kwargs}
    )
    if result.modified_count > 0:
        log_activity(kwargs.get("updated_by", "system"), "update", "area_point", "area_point", area_point_id)
    return result.modified_count > 0

def delete_area_point(area_point_id: str, user: str = "system") -> bool:
    """Soft delete area point"""
    db = get_db()
    result = db.area_points.update_one(
        {"area_point_id": area_point_id},
        {"$set": {"is_active": False, "updated_at": datetime.now()}}
    )
    if result.modified_count > 0:
        log_activity(user, "delete", "area_point", "area_point", area_point_id)
    return result.modified_count > 0

# ==================== ENVIRONMENTAL DATA ====================

def create_environmental_data(area_point_id: str, date: str, source: str, **kwargs) -> Optional[str]:
    """Create environmental data record"""
    db = get_db()
    
    # Validate area point exists
    if not validate_area_point_exists(area_point_id):
        raise ValueError(f"Area point {area_point_id} does not exist")
    
    # Validate source
    if source not in ['nasa_power', 'microclimate', 'manual']:
        raise ValueError(f"Invalid source: {source}")
    
    try:
        doc = {
            "area_point_id": area_point_id,
            "date": date,
            "source": source,
            "created_at": datetime.now()
        }
        doc.update(kwargs)
        
        result = db.environmental_data.insert_one(doc)
        log_activity(kwargs.get("created_by", "system"), "create", "environmental", "environmental_data", area_point_id)
        return str(result.inserted_id)
    except DuplicateKeyError:
        print(f"Environmental data for {area_point_id} on {date} from {source} already exists")
        return None

def get_environmental_data(area_point_id: Optional[str] = None, 
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None,
                          source: Optional[str] = None) -> pd.DataFrame:
    """Get environmental data with filters"""
    db = get_db()
    query = {}
    
    if area_point_id:
        query["area_point_id"] = area_point_id
    if source:
        query["source"] = source
    if start_date or end_date:
        query["date"] = {}
        if start_date:
            query["date"]["$gte"] = start_date
        if end_date:
            query["date"]["$lte"] = end_date
    
    cursor = db.environmental_data.find(query).sort("date", DESCENDING)
    data = list(cursor)
    
    if not data:
        return pd.DataFrame()
    
    for doc in data:
        doc["_id"] = str(doc["_id"])
        if "created_at" in doc:
            doc["created_at"] = doc["created_at"].strftime("%Y-%m-%d %H:%M:%S")
    
    return pd.DataFrame(data)

def bulk_create_environmental_data(records: List[Dict]) -> int:
    """Bulk insert environmental data"""
    db = get_db()
    
    # Validate all area points exist
    area_point_ids = set(r["area_point_id"] for r in records)
    for apid in area_point_ids:
        if not validate_area_point_exists(apid):
            raise ValueError(f"Area point {apid} does not exist")
    
    # Add timestamps
    for record in records:
        record["created_at"] = datetime.now()
    
    try:
        result = db.environmental_data.insert_many(records, ordered=False)
        return len(result.inserted_ids)
    except Exception as e:
        print(f"Bulk insert error: {e}")
        return 0

# ==================== PEST RECORDS ====================

def create_pest_record(area_point_id: str, pest_type: str, date: str, 
                      count: Optional[int] = None, density: Optional[float] = None,
                      notes: Optional[str] = None, image_path: Optional[str] = None,
                      created_by: str = "system", **kwargs) -> Optional[str]:
    """Create pest observation record"""
    db = get_db()
    
    # Validate area point exists
    if not validate_area_point_exists(area_point_id):
        raise ValueError(f"Area point {area_point_id} does not exist")
    
    # Validate pest type
    if pest_type not in ['rbb', 'wsb']:
        raise ValueError(f"Invalid pest_type: {pest_type}. Must be 'rbb' or 'wsb'")
    
    doc = {
        "area_point_id": area_point_id,
        "pest_type": pest_type,
        "date": date,
        "count": count,
        "density": density,
        "notes": notes,
        "image_path": image_path,
        "created_by": created_by,
        "created_at": datetime.now()
    }
    doc.update(kwargs)
    
    result = db.pest_records.insert_one(doc)
    log_activity(created_by, "create", "pest", "pest_record", area_point_id)
    return str(result.inserted_id)

def get_pest_records(area_point_id: Optional[str] = None,
                    pest_type: Optional[str] = None,
                    start_date: Optional[str] = None,
                    end_date: Optional[str] = None) -> pd.DataFrame:
    """Get pest records with filters"""
    db = get_db()
    query = {}
    
    if area_point_id:
        query["area_point_id"] = area_point_id
    if pest_type:
        query["pest_type"] = pest_type
    if start_date or end_date:
        query["date"] = {}
        if start_date:
            query["date"]["$gte"] = start_date
        if end_date:
            query["date"]["$lte"] = end_date
    
    cursor = db.pest_records.find(query).sort("date", DESCENDING)
    data = list(cursor)
    
    if not data:
        return pd.DataFrame()
    
    for doc in data:
        doc["_id"] = str(doc["_id"])
        if "created_at" in doc:
            doc["created_at"] = doc["created_at"].strftime("%Y-%m-%d %H:%M:%S")
    
    return pd.DataFrame(data)

def update_pest_record(record_id: str, **kwargs) -> bool:
    """Update pest record"""
    db = get_db()
    from bson.objectid import ObjectId
    
    kwargs["updated_at"] = datetime.now()
    result = db.pest_records.update_one(
        {"_id": ObjectId(record_id)},
        {"$set": kwargs}
    )
    return result.modified_count > 0

def delete_pest_record(record_id: str, user: str = "system") -> bool:
    """Delete pest record"""
    db = get_db()
    from bson.objectid import ObjectId
    
    result = db.pest_records.delete_one({"_id": ObjectId(record_id)})
    if result.deleted_count > 0:
        log_activity(user, "delete", "pest", "pest_record", record_id)
    return result.deleted_count > 0

def bulk_create_pest_records(records: List[Dict]) -> int:
    """Bulk insert pest records"""
    db = get_db()
    
    # Validate all area points exist
    area_point_ids = set(r["area_point_id"] for r in records)
    for apid in area_point_ids:
        if not validate_area_point_exists(apid):
            raise ValueError(f"Area point {apid} does not exist")
    
    # Validate pest types
    for record in records:
        if record.get("pest_type") not in ['rbb', 'wsb']:
            raise ValueError(f"Invalid pest_type: {record.get('pest_type')}")
        record["created_at"] = datetime.now()
    
    try:
        result = db.pest_records.insert_many(records, ordered=False)
        return len(result.inserted_ids)
    except Exception as e:
        print(f"Bulk insert error: {e}")
        return 0

# ==================== DATASET UPLOADS ====================

def create_dataset_upload(filename: str, uploaded_by: str, row_count: int,
                         file_size: int, columns: List[str], 
                         validation_status: str = "pending") -> str:
    """Create dataset upload record"""
    db = get_db()
    
    doc = {
        "filename": filename,
        "uploaded_by": uploaded_by,
        "row_count": row_count,
        "file_size": file_size,
        "columns": columns,
        "validation_status": validation_status,
        "processing_status": "pending",
        "uploaded_at": datetime.now()
    }
    
    result = db.dataset_uploads.insert_one(doc)
    log_activity(uploaded_by, "upload", "dataset", "dataset_upload", filename)
    return str(result.inserted_id)

def update_dataset_upload(upload_id: str, **kwargs) -> bool:
    """Update dataset upload"""
    db = get_db()
    from bson.objectid import ObjectId
    
    kwargs["updated_at"] = datetime.now()
    result = db.dataset_uploads.update_one(
        {"_id": ObjectId(upload_id)},
        {"$set": kwargs}
    )
    return result.modified_count > 0

def get_dataset_uploads(uploaded_by: Optional[str] = None) -> pd.DataFrame:
    """Get dataset uploads"""
    db = get_db()
    query = {}
    if uploaded_by:
        query["uploaded_by"] = uploaded_by
    
    cursor = db.dataset_uploads.find(query).sort("uploaded_at", DESCENDING)
    data = list(cursor)
    
    if not data:
        return pd.DataFrame()
    
    for doc in data:
        doc["_id"] = str(doc["_id"])
        if "uploaded_at" in doc:
            doc["uploaded_at"] = doc["uploaded_at"].strftime("%Y-%m-%d %H:%M:%S")
    
    return pd.DataFrame(data)

# ==================== DATASET PROCESSING ====================

def create_dataset_processing(upload_id: str, domain: str, records_processed: int,
                              records_failed: int, error_details: Optional[str] = None) -> str:
    """Create dataset processing record"""
    db = get_db()
    
    doc = {
        "upload_id": upload_id,
        "domain": domain,
        "records_processed": records_processed,
        "records_failed": records_failed,
        "error_details": error_details,
        "processed_at": datetime.now()
    }
    
    result = db.dataset_processing.insert_one(doc)
    return str(result.inserted_id)

# ==================== ACTIVITY LOGS ====================

def log_activity(user: str, action: str, module: str, entity_type: str,
                entity_id: Optional[str] = None, details: Optional[Dict] = None,
                ip_address: Optional[str] = None) -> str:
    """Log user activity"""
    db = get_db()
    
    # Validate action and module
    valid_actions = ['upload', 'create', 'read', 'update', 'delete', 'login', 'logout', 'export', 'import']
    valid_modules = ['dataset', 'environmental', 'pest', 'area_point', 'auth', 'visualization', 'settings']
    
    if action not in valid_actions:
        raise ValueError(f"Invalid action: {action}")
    if module not in valid_modules:
        raise ValueError(f"Invalid module: {module}")
    
    doc = {
        "user": user,
        "action": action,
        "module": module,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "details": details or {},
        "ip_address": ip_address,
        "timestamp": datetime.now()
    }
    
    result = db.activity_logs.insert_one(doc)
    return str(result.inserted_id)

def get_activity_logs(user: Optional[str] = None, module: Optional[str] = None,
                     action: Optional[str] = None, limit: int = 100) -> pd.DataFrame:
    """Get activity logs with filters"""
    db = get_db()
    query = {}
    
    if user:
        query["user"] = user
    if module:
        query["module"] = module
    if action:
        query["action"] = action
    
    cursor = db.activity_logs.find(query).sort("timestamp", DESCENDING).limit(limit)
    data = list(cursor)
    
    if not data:
        return pd.DataFrame()
    
    for doc in data:
        doc["_id"] = str(doc["_id"])
        if "timestamp" in doc:
            doc["timestamp"] = doc["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        if "details" in doc and isinstance(doc["details"], dict):
            doc["details"] = json.dumps(doc["details"])
    
    return pd.DataFrame(data)

# ==================== MONITORING POINTS (Legacy) ====================

def get_monitoring_points() -> pd.DataFrame:
    """Get all monitoring points (legacy compatibility)"""
    db = get_db()
    cursor = db.monitoring_points.find()
    data = list(cursor)
    
    if not data:
        return pd.DataFrame()
    
    for doc in data:
        doc["_id"] = str(doc["_id"])
    
    return pd.DataFrame(data)

def save_monitoring_point(point_data: Dict) -> str:
    """Save monitoring point (legacy compatibility)"""
    db = get_db()
    point_data["created_at"] = datetime.now()
    result = db.monitoring_points.insert_one(point_data)
    return str(result.inserted_id)
