"""
Database Manager Module for HireAI Pro
Handles MongoDB operations for candidate data
"""

import os
import bcrypt
from datetime import datetime
from typing import Dict, Any, Tuple, List, Optional
from pymongo import MongoClient, DESCENDING
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "hireai_pro"
COLLECTION_NAME = "candidates"
HR_COLLECTION = "Registered"
HR_DETAILS_COLLECTION = "hr_details"
LOG_COLLECTION = "unauthorized_attempts"
CONFIG_COLLECTION = "system_settings"
SESSION_COLLECTION = "active_sessions"
EMAIL_LOG_COLLECTION = "Email_Candidated"
DISQUALIFIED_COLLECTION = "Disqualified_Candidate"

# Credentials from Env (Security Hardening)
ORG_KEY = os.getenv("ORG_KEY", "HIREAI_STAFF_2026")
DEFAULT_ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "mumbai2026")

_client = None
_db = None
_collection = None
_hr_collection = None
_hr_details_collection = None
_log_collection = None
_config_collection = None
_session_collection = None
_email_log_collection = None
_disqualified_collection = None

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def check_password(password: str, hashed_password: str) -> bool:
    """Check a password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def init_database() -> bool:
    """
    Initialize database connection and ensure indices.
    Returns True if successful, False otherwise.
    """
    global _client, _db, _collection, _hr_collection, _hr_details_collection, _log_collection, _config_collection, _session_collection, _email_log_collection, _disqualified_collection
    try:
        if _client is None:
            _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            # Trigger connection check
            _client.server_info()
            _db = _client[DB_NAME]
            _collection = _db[COLLECTION_NAME]
            _hr_collection = _db[HR_COLLECTION]
            _hr_details_collection = _db[HR_DETAILS_COLLECTION]
            _log_collection = _db[LOG_COLLECTION]
            _config_collection = _db[CONFIG_COLLECTION]
            _session_collection = _db[SESSION_COLLECTION]
            _email_log_collection = _db[EMAIL_LOG_COLLECTION]
            _disqualified_collection = _db[DISQUALIFIED_COLLECTION]
            
            # Create indices for performance
            _collection.create_index([("email", 1)], unique=True)
            _collection.create_index([("submitted_at", DESCENDING)])
            _collection.create_index([("status", 1)])
            
            # HR Indices (Registered)
            _hr_collection.create_index([("username", 1)], unique=True)
            _hr_collection.create_index([("email", 1)], unique=True)
            
            # HR Details Indices
            _hr_details_collection.create_index([("username", 1)], unique=True)
            _hr_details_collection.create_index([("email", 1)], unique=True)
            
            # Log Indices
            _log_collection.create_index([("timestamp", -1)])
            
            # Session Indices
            _session_collection.create_index([("token", 1)], unique=True)
            _session_collection.create_index([("expires_at", 1)], expireAfterSeconds=86400) # Auto-cleanup after 24h
            
            # Email Log Indices
            _email_log_collection.create_index([("sent_at", 1)])
            _email_log_collection.create_index([("hr_email", 1)])
            
            _disqualified_collection.create_index([("email", 1)])
            _disqualified_collection.create_index([("rejected_at", -1)])
            
            # Ensure at least one admin exists
            initialize_default_admin()
            
        return True
    except Exception:
        # Silently fail to avoid terminal crashes on Windows
        return False


def log_candidate_email(hr_data: Dict[str, Any], candidate_email: str, subject: str, body: str) -> bool:
    """
    Log HR communication with a candidate.
    """
    if not init_database():
        return False
    try:
        _email_log_collection.insert_one({
            "hr_username": hr_data.get('username'),
            "hr_email": hr_data.get('email'),
            "hr_name": hr_data.get('full_name'),
            "candidate_email": candidate_email,
            "subject": subject,
            "body": body,
            "sent_at": datetime.now().isoformat()
        })
        return True
    except Exception:
        return False


def log_disqualified_candidate(candidate_data: Dict[str, Any], hr_data: Dict[str, Any], reason: str = "Evaluation Criteria Not Met", round_name: str = "Screening Round") -> bool:
    """
    Log a disqualified candidate into the dedicated collection.
    """
    if not init_database():
        return False
    try:
        disq_record = {
            "email": candidate_data.get('email'),
            "full_name": candidate_data.get('full_name'),
            "hr_username": hr_data.get('username'),
            "hr_email": hr_data.get('email'),
            "reason": reason,
            "round": round_name,
            "rejected_at": datetime.now().isoformat(),
            "candidate_metadata": {
                "score": candidate_data.get('metrics', {}).get('final_score'),
                "submitted_at": candidate_data.get('submitted_at')
            }
        }
        _disqualified_collection.insert_one(disq_record)
        return True
    except Exception:
        return False


def fetch_disqualified_candidates() -> List[Dict[str, Any]]:
    """
    Fetch all disqualified candidates from the dedicated collection.
    """
    if not init_database():
        return []
    try:
        cursor = _disqualified_collection.find().sort("rejected_at", DESCENDING)
        return list(cursor)
    except Exception:
        return []


def create_session(user_data, role) -> str:
    """Create a new session in MongoDB and return a unique token."""
    if not init_database(): return ""
    import uuid
    token = str(uuid.uuid4())
    try:
        # Strip sensitive data from session storage
        session_data = {k: v for k, v in user_data.items() if k not in ["password"]}
        if "_id" in session_data: session_data["_id"] = str(session_data["_id"])
        
        _session_collection.insert_one({
            "token": token,
            "user": session_data,
            "role": role,
            "created_at": datetime.now().isoformat(),
            "expires_at": datetime.now() + timedelta(days=1)
        })
        return token
    except Exception:
        return ""


def get_session(token) -> Optional[Dict[str, Any]]:
    """Retrieve and validate a session from MongoDB."""
    if not init_database() or not token: return None
    try:
        session = _session_collection.find_one({"token": token})
        return session if session else None
    except Exception:
        return None


def delete_session(token):
    """Delete a session from MongoDB on logout."""
    if not init_database() or not token: return
    try:
        _session_collection.delete_one({"token": token})
    except Exception:
        pass


def get_org_key() -> str:
    """Retrieve the Organization Secret Key from database settings."""
    if not init_database():
        return ORG_KEY
    try:
        config = _config_collection.find_one({"key": "organization_secret_key"})
        return config["value"] if config else ORG_KEY
    except Exception:
        return ORG_KEY


def update_org_key(new_key: str) -> Tuple[bool, str]:
    """Update the Organization Secret Key in the database."""
    if not init_database():
        return False, "Database connection failed"
    try:
        _config_collection.update_one(
            {"key": "organization_secret_key"},
            {"$set": {"value": new_key, "updated_at": datetime.now().isoformat()}},
            upsert=True
        )
        return True, "Secret Key updated successfully"
    except Exception as e:
        return False, f"Update failed: {str(e)}"


def log_unauthorized_access(username, reason, details=None):
    """Log unauthorized HR access attempts."""
    if not init_database():
        return
    try:
        _log_collection.insert_one({
            "username": username,
            "reason": reason,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
    except Exception:
        pass


def register_hr(hr_data, secret_key) -> Tuple[bool, str]:
    """Register a new HR user with Organization Secret Key verification."""
    org_key = get_org_key()
    if secret_key != org_key:
        log_unauthorized_access(
            hr_data.get('username', 'unknown'), 
            "Invalid Secret Key", 
            {"email": hr_data.get('email')}
        )
        return False, "Invalid Organization Secret Key. Access Denied."
        
    if not init_database():
        return False, "Database connection failed"
        
    try:
        # Check if user already exists in either table
        if _hr_collection.find_one({"username": hr_data["username"]}) or _hr_details_collection.find_one({"username": hr_data["username"]}):
            return False, "Username already taken"
        if _hr_collection.find_one({"email": hr_data["email"]}) or _hr_details_collection.find_one({"email": hr_data["email"]}):
            return False, "Email already registered"
            
        hr_data["created_at"] = datetime.now().isoformat()
        if "role" not in hr_data:
            hr_data["role"] = "Screener" # Default role
        
        # Hash password before storage
        if "password" in hr_data:
            hr_data["password"] = hash_password(hr_data["password"])
        
        # Dual storage: Registered and hr_details
        _hr_collection.insert_one(hr_data.copy())
        _hr_details_collection.insert_one(hr_data.copy())
        
        return True, "HR registration successful!"
    except Exception as e:
        return False, f"Registration failed: {str(e)}"


def initialize_default_admin():
    """Ensure a default admin account exists in both HR collections."""
    try:
        admin_doc = {
            "full_name": "System Administrator",
            "username": "admin",
            "password": hash_password(DEFAULT_ADMIN_PASS),
            "email": "admin@hireaipro.com",
            "role": "Technical Lead",
            "mobile": "+91 99999 99999",
            "created_at": datetime.now().isoformat()
        }
        
        if _hr_collection.count_documents({"username": "admin"}) == 0:
            _hr_collection.insert_one(admin_doc.copy())
            
        if _hr_details_collection.count_documents({"username": "admin"}) == 0:
            _hr_details_collection.insert_one(admin_doc.copy())
            
    except Exception:
        pass


def authenticate_hr(username, password) -> Optional[Dict[str, Any]]:
    """Authenticate HR user against database credentials."""
    if not init_database():
        return None
    try:
        user = _hr_collection.find_one({"username": username})
        if user and check_password(password, user.get('password', '')):
            user['_id'] = str(user['_id'])
            return user
        return None
    except Exception:
        return None


def update_hr_profile(hr_id, update_data) -> Tuple[bool, str]:
    """Update HR profile details in both Registered and hr_details collections."""
    if not init_database():
        return False, "Database connection failed"
    try:
        from bson.objectid import ObjectId
        
        # Get existing user to find username for synchronization if ID is specific to one table
        # Since we use Dual storage, we should find by username if we want to sync across both
        # Or better, both tables use the same data.
        user_in_reg = _hr_collection.find_one({"_id": ObjectId(hr_id)})
        if not user_in_reg:
            return False, "User not found"
            
        username = user_in_reg.get('username')
        
        # Prevent duplicate username/email if changed
        if "username" in update_data:
            existing = _hr_collection.find_one({"username": update_data["username"], "_id": {"$ne": ObjectId(hr_id)}})
            if existing: return False, "Username already taken"
            
        if "email" in update_data:
            existing = _hr_collection.find_one({"email": update_data["email"], "_id": {"$ne": ObjectId(hr_id)}})
            if existing: return False, "Email already taken"

        # Update both tables
        set_payload = {**update_data, "last_updated": datetime.now().isoformat()}
        
        _hr_collection.update_one({"_id": ObjectId(hr_id)}, {"$set": set_payload})
        _hr_details_collection.update_one({"username": username}, {"$set": set_payload})
        
        return True, "Profile updated successfully in both collections"
    except Exception as e:
        return False, f"Update failed: {str(e)}"


def save_candidate_to_mongo(
    name: str,
    email: str,
    phone: str,
    ai_result: Dict[str, Any],
    weights: Dict[str, int],
    applied_role: str = "Software Engineer",
    video_result: Optional[Dict[str, Any]] = None,
    cross_ref_result: Optional[Dict[str, Any]] = None
) -> Tuple[bool, str, Optional[str]]:
    """
    Save candidate evaluation to database, including multimodal data.
    Returns: (success: bool, message: str, candidate_id: str or None)
    """
    if not init_database():
        return False, "Database connection failed", None
        
    try:
        from modules.ai_engine import calculate_weighted_score
        
        final_score = calculate_weighted_score(ai_result, weights)
        
        candidate_doc = {
            'full_name': name,
            'email': email.lower(),
            'mobile': phone,
            'applied_role': applied_role,
            'ai_analysis': ai_result,
            'video_analysis': video_result,
            'multimodal_insights': cross_ref_result,
            'metrics': {
                'final_score': final_score,
                'resume_score': ai_result.get('score', 0)
            },
            'status': 'New',
            'submitted_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
        
        # Use upsert to prevent duplicates based on email
        # If updating, $set will merge existing fields
        result = _collection.update_one(
            {"email": email.lower()},
            {"$set": candidate_doc},
            upsert=True
        )
        
        candidate_id = str(result.upserted_id) if result.upserted_id else email.lower()
        return True, "Candidate saved successfully", candidate_id
        
    except Exception as e:
        return False, f"Database error: {str(e)}", None


def fetch_all_candidates(status_filter: str = "All") -> List[Dict[str, Any]]:
    """
    Fetch all candidates from MongoDB, optionally filtered by status.
    """
    if not init_database():
        return []
    
    try:
        query = {}
        if status_filter != "All":
            query["status"] = status_filter
            
        # Sort by submission date descending
        cursor = _collection.find(query).sort("submitted_at", DESCENDING)
        
        candidates = []
        for doc in cursor:
            # Convert ObjectId or other BSON types if necessary
            doc['_id'] = str(doc.get('_id', ''))
            candidates.append(doc)
            
        return candidates
    except Exception:
        return []


def update_candidate_status(candidate_id_or_email: str, new_status: str) -> Tuple[bool, str]:
    """
    Update candidate application status in MongoDB.
    """
    if not init_database():
        return False, "Database connection failed"
        
    try:
        from bson.objectid import ObjectId
        
        # Try both ObjectId and Email as matching criteria
        query = {}
        try:
            query = {"_id": ObjectId(candidate_id_or_email)}
        except Exception:
            query = {"email": candidate_id_or_email.lower()}
            
        result = _collection.update_one(
            query,
            {
                "$set": {
                    "status": new_status,
                    "last_updated": datetime.now().isoformat()
                }
            }
        )
        
        if result.modified_count > 0 or result.matched_count > 0:
            return True, f"Status updated to {new_status}"
        return False, "Candidate not found"
        
    except Exception as e:
        return False, f"Update failed: {str(e)}"


def get_statistics() -> Dict[str, Any]:
    """
    Get real-time recruitment statistics from MongoDB.
    """
    default_stats = {
        'total': 0, 'shortlisted': 0, 'evaluated': 0,
        'disqualified': 0, 'new': 0, 'average_score': 0
    }
    
    if not init_database():
        return default_stats
    
    try:
        # Get counts for each status
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}, "avg_score": {"$avg": "$metrics.final_score"}}}
        ]
        results = list(_collection.aggregate(pipeline))
        
        stats = default_stats.copy()
        total = 0
        sum_scores = 0
        count_with_scores = 0
        
        for res in results:
            status = res['_id']
            count = res['count']
            avg = res['avg_score'] or 0
            
            total += count
            sum_scores += (avg * count)
            count_with_scores += count
            
            if status == 'Shortlisted': stats['shortlisted'] = count
            elif status == 'Evaluated': stats['evaluated'] = count
            elif status == 'Disqualified': stats['disqualified'] = count
            elif status == 'New': stats['new'] = count
            
        stats['total'] = total
        if count_with_scores > 0:
            stats['average_score'] = round(sum_scores / count_with_scores, 2)
            
        return stats
    except Exception:
        return default_stats