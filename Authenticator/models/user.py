from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from bson import ObjectId

class User:
    @staticmethod
    def create_user(db, email, password):
        """Create a new user in the database"""
        user = {
            'email': email,
            'password_hash': generate_password_hash(password, method='pbkdf2:sha256'),
            'is_active': False,
            'storage_limit': 24576,  # Default storage limit: 24GB (in MB)
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        result = db.Users.insert_one(user)
        user['_id'] = result.inserted_id
        return user
    
    @staticmethod
    def find_by_email(db, email):
        """Find a user by email"""
        return db.Users.find_one({'email': email})
    
    @staticmethod
    def find_by_id(db, user_id):
        """Find a user by ID"""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        return db.Users.find_one({'_id': user_id})
    
    @staticmethod
    def activate_user(db, user_id):
        """Activate a user account"""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        db.Users.update_one(
            {'_id': user_id},
            {'$set': {'is_active': True, 'updated_at': datetime.utcnow()}}
        )
    
    @staticmethod
    def update_password(db, user_id, new_password):
        """Update a user's password"""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        db.Users.update_one(
            {'_id': user_id},
            {'$set': {
                'password_hash': generate_password_hash(new_password),
                'updated_at': datetime.utcnow()
            }}
        )
    
    @staticmethod
    def increase_storage_limit(db, user_id, additional_storage, unit='MB'):
        """Increase a user's storage limit
        
        Args:
            db: Database connection
            user_id: User ID
            additional_storage: Amount of additional storage
            unit: Unit of storage (MB, GB, TB)
        """
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
            
        # Convert additional storage to MB for consistent storage
        if unit.upper() == 'GB':
            additional_storage_mb = additional_storage * 1024
        elif unit.upper() == 'TB':
            additional_storage_mb = additional_storage * 1024 * 1024
        else:  # Default is MB
            additional_storage_mb = additional_storage
            
        # Get current user to find current storage limit
        user = db.Users.find_one({'_id': user_id})
        if not user:
            return False
            
        current_limit = user.get('storage_limit', 0)
        new_limit = current_limit + additional_storage_mb
        
        # Update the storage limit
        db.Users.update_one(
            {'_id': user_id},
            {'$set': {
                'storage_limit': new_limit,
                'updated_at': datetime.utcnow()
            }}
        )
        return True
    
    @staticmethod
    def check_password(user, password):
        """Check if the provided password matches the user's password"""
        return check_password_hash(user['password_hash'], password)
    
    @staticmethod
    def to_dict(user):
        """Convert user document to dictionary for API response"""
        return {
            'id': str(user['_id']),
            'email': user['email'],
            'is_active': user['is_active'],
            'storage_limit': user.get('storage_limit', 0),  # Include storage limit in response
            'created_at': user['created_at'].isoformat(),
            'updated_at': user['updated_at'].isoformat()
        }