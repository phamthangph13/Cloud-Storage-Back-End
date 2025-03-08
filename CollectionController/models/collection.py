from datetime import datetime
from bson.objectid import ObjectId
from Authenticator import db

class Collection:
    """
    Collection model class for managing user collections
    """
    
    @staticmethod
    def create(name, owner_id):
        """
        Create a new collection
        
        Args:
            name (str): Name of the collection
            owner_id (str): ID of the user owning this collection
            
        Returns:
            dict: The created collection document
        """
        collection = {
            'name': name.strip(),
            'owner_id': owner_id,
            'files': [],  # Initialize an empty array for file IDs
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = db.collections.insert_one(collection)
        collection['_id'] = result.inserted_id
        
        return collection
    
    @staticmethod
    def get_by_id(collection_id, owner_id):
        """
        Get a collection by its ID and owner
        
        Args:
            collection_id (str): ID of the collection
            owner_id (str): ID of the user owning this collection
            
        Returns:
            dict: The collection document or None if not found
        """
        try:
            return db.collections.find_one({
                '_id': ObjectId(collection_id),
                'owner_id': owner_id
            })
        except:
            return None
    
    @staticmethod
    def get_all_by_owner(owner_id):
        """
        Get all collections owned by a user
        
        Args:
            owner_id (str): ID of the owner
            
        Returns:
            list: List of collection documents
        """
        return list(db.collections.find({'owner_id': owner_id}))
    
    @staticmethod
    def update(collection_id, owner_id, data):
        """
        Update a collection
        
        Args:
            collection_id (str): ID of the collection
            owner_id (str): ID of the user owning this collection
            data (dict): Fields to update
            
        Returns:
            dict: The updated collection or None if not found
        """
        try:
            update_data = {k: v for k, v in data.items() if k != '_id'}
            update_data['updated_at'] = datetime.utcnow()
            
            result = db.collections.update_one(
                {
                    '_id': ObjectId(collection_id),
                    'owner_id': owner_id
                },
                {'$set': update_data}
            )
            
            if result.matched_count > 0:
                return db.collections.find_one({'_id': ObjectId(collection_id)})
            return None
        except:
            return None
    
    @staticmethod
    def delete(collection_id, owner_id):
        """
        Delete a collection
        
        Args:
            collection_id (str): ID of the collection
            owner_id (str): ID of the user owning this collection
            
        Returns:
            bool: True if deleted, False otherwise
        """
        try:
            result = db.collections.delete_one({
                '_id': ObjectId(collection_id),
                'owner_id': owner_id
            })
            
            return result.deleted_count > 0
        except:
            return False
            
    @staticmethod
    def add_file(collection_id, owner_id, file_id):
        """
        Add a file to a collection
        
        Args:
            collection_id (str): ID of the collection
            owner_id (str): ID of the user owning this collection
            file_id (str): ID of the file to add
            
        Returns:
            dict: The updated collection or None if not found/updated
        """
        try:
            # Check if the file already exists in the collection
            collection = db.collections.find_one({
                '_id': ObjectId(collection_id),
                'owner_id': owner_id
            })
            
            if not collection:
                return None
                
            # Add file to the collection if it doesn't already exist
            result = db.collections.update_one(
                {
                    '_id': ObjectId(collection_id),
                    'owner_id': owner_id
                },
                {
                    '$addToSet': {'files': file_id},
                    '$set': {'updated_at': datetime.utcnow()}
                }
            )
            
            if result.modified_count > 0 or result.matched_count > 0:
                return db.collections.find_one({'_id': ObjectId(collection_id)})
            return None
        except:
            return None
            
    @staticmethod
    def remove_file(collection_id, owner_id, file_id):
        """
        Remove a file from a collection
        
        Args:
            collection_id (str): ID of the collection
            owner_id (str): ID of the user owning this collection
            file_id (str): ID of the file to remove
            
        Returns:
            dict: The updated collection or None if not found
        """
        try:
            result = db.collections.update_one(
                {
                    '_id': ObjectId(collection_id),
                    'owner_id': owner_id
                },
                {
                    '$pull': {'files': file_id},
                    '$set': {'updated_at': datetime.utcnow()}
                }
            )
            
            if result.matched_count > 0:
                return db.collections.find_one({'_id': ObjectId(collection_id)})
            return None
        except:
            return None
            
    @staticmethod
    def get_files(collection_id, owner_id):
        """
        Get all files in a collection
        
        Args:
            collection_id (str): ID of the collection
            owner_id (str): ID of the user owning this collection
            
        Returns:
            list: List of file IDs or None if collection not found
        """
        try:
            collection = db.collections.find_one({
                '_id': ObjectId(collection_id),
                'owner_id': owner_id
            })
            
            if not collection:
                return None
                
            return collection.get('files', [])
        except:
            return None 