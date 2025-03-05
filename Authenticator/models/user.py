from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from bson import ObjectId

class User:
    @staticmethod
    def create_user(db, email, password):
        """Create a new user in the database"""
        user = {
            'email': email,
            'password_hash': generate_password_hash(password),
            'is_active': False,
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
            'created_at': user['created_at'].isoformat(),
            'updated_at': user['updated_at'].isoformat()
        }