from flask import request
from flask_restx import Resource, fields, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId
from CollectionController import api
from Authenticator import db
from CollectionController.models.collection import Collection
from datetime import datetime
from bson.errors import InvalidId

# Collection model for API documentation
collection_model = api.model('Collection', {
    'id': fields.String(description='Collection ID'),
    'name': fields.String(required=True, description='Collection name'),
    'owner_id': fields.String(description='User ID of the collection owner'),
    'created_at': fields.DateTime(description='Creation timestamp'),
    'updated_at': fields.DateTime(description='Last update timestamp')
})

# Collection creation model
collection_create_model = api.model('CollectionCreate', {
    'name': fields.String(required=True, description='Collection name')
})

# Collection update model
collection_update_model = api.model('CollectionUpdate', {
    'name': fields.String(required=True, description='New collection name')
})

# Collection files model for API documentation
collection_files_model = api.model('CollectionFiles', {
    'collection_id': fields.String(description='Collection ID'),
    'collection_name': fields.String(description='Collection name'),
    'files': fields.List(fields.Nested(api.model('FileInCollection', {
        'id': fields.String(description='File ID'),
        'filename': fields.String(description='Original filename'),
        'file_type': fields.String(description='File type (image, video, document, other)'),
        'file_size': fields.Integer(description='File size in bytes'),
        'upload_date': fields.DateTime(description='Upload date'),
        'description': fields.String(description='File description'),
        'download_url': fields.String(description='URL to download the file')
    })))
})

@api.route('')
class CollectionList(Resource):
    @jwt_required()
    @api.doc(responses={
        200: 'Collections retrieved successfully',
        401: 'Unauthorized'
    })
    def get(self):
        """Get all collections for the current user"""
        current_user = get_jwt_identity()
        
        # Find all collections owned by the current user
        collections = list(db.collections.find({'owner_id': current_user}))
        
        # Format collections for response
        formatted_collections = []
        for collection in collections:
            formatted_collections.append({
                'id': str(collection['_id']),
                'name': collection['name'],
                'owner_id': collection['owner_id'],
                'created_at': collection['created_at'],
                'updated_at': collection['updated_at']
            })
        
        return {'collections': formatted_collections}, 200
    
    @jwt_required()
    @api.expect(collection_create_model)
    @api.doc(responses={
        201: 'Collection created successfully',
        400: 'Invalid input',
        401: 'Unauthorized'
    })
    def post(self):
        """Create a new collection"""
        current_user = get_jwt_identity()
        data = request.json
        
        # Validate input
        if not data or 'name' not in data or not data['name'].strip():
            return {'message': 'Collection name is required'}, 400
        
        # Create a new collection
        collection = {
            'name': data['name'].strip(),
            'owner_id': current_user,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        # Insert into database
        result = db.collections.insert_one(collection)
        
        # Return the created collection
        return {
            'message': 'Collection created successfully',
            'collection': {
                'id': str(result.inserted_id),
                'name': collection['name'],
                'owner_id': collection['owner_id'],
                'created_at': collection['created_at'],
                'updated_at': collection['updated_at']
            }
        }, 201

@api.route('/<string:collection_id>')
class CollectionDetail(Resource):
    @jwt_required()
    @api.doc(responses={
        200: 'Collection details retrieved successfully',
        404: 'Collection not found',
        401: 'Unauthorized'
    })
    def get(self, collection_id):
        """Get a specific collection"""
        current_user = get_jwt_identity()
        
        try:
            # Validate the ObjectId format
            if not collection_id or len(collection_id) != 24:
                return {'message': 'Invalid collection ID format. Must be a 24-character hexadecimal string.'}, 400
                
            try:
                # Try to convert to ObjectId to validate it
                object_id = ObjectId(collection_id)
            except InvalidId:
                return {'message': 'Invalid collection ID format. Must be a valid 24-character hexadecimal string.'}, 400
                
            # Find the collection
            collection = db.collections.find_one({
                '_id': object_id,
                'owner_id': current_user
            })
            
            if not collection:
                return {'message': 'Collection not found'}, 404
                
            # Convert ObjectId to string for JSON serialization
            collection['id'] = str(collection['_id'])
            del collection['_id']
            
            return collection, 200
        except Exception as e:
            print(f"Error getting collection: {str(e)}")
            return {'message': 'An error occurred while processing your request'}, 500
    
    @jwt_required()
    @api.expect(collection_update_model)
    @api.doc(responses={
        200: 'Collection updated successfully',
        400: 'Invalid input',
        404: 'Collection not found',
        401: 'Unauthorized'
    })
    def put(self, collection_id):
        """Update a collection"""
        current_user = get_jwt_identity()
        data = request.json
        
        try:
            # Validate the ObjectId format
            if not collection_id or len(collection_id) != 24:
                return {'message': 'Invalid collection ID format. Must be a 24-character hexadecimal string.'}, 400
                
            try:
                # Try to convert to ObjectId to validate it
                object_id = ObjectId(collection_id)
            except InvalidId:
                return {'message': 'Invalid collection ID format. Must be a valid 24-character hexadecimal string.'}, 400
                
            # Validate input
            if not data or 'name' not in data or not data['name'].strip():
                return {'message': 'Collection name is required'}, 400
                
            # Find the collection
            collection = db.collections.find_one({
                '_id': object_id,
                'owner_id': current_user
            })
            
            if not collection:
                return {'message': 'Collection not found'}, 404
                
            # Update collection
            update_data = {
                'name': data['name'].strip(),
                'updated_at': datetime.now()
            }
            
            db.collections.update_one(
                {'_id': object_id, 'owner_id': current_user},
                {'$set': update_data}
            )
            
            # Get updated collection
            updated_collection = db.collections.find_one({
                '_id': object_id,
                'owner_id': current_user
            })
            
            # Convert ObjectId to string for JSON serialization
            updated_collection['id'] = str(updated_collection['_id'])
            del updated_collection['_id']
            
            return {
                'message': 'Collection updated successfully',
                'collection': updated_collection
            }, 200
        except Exception as e:
            print(f"Error updating collection: {str(e)}")
            return {'message': 'An error occurred while processing your request'}, 500
    
    @jwt_required()
    @api.doc(responses={
        200: 'Collection deleted successfully',
        404: 'Collection not found',
        401: 'Unauthorized'
    })
    def delete(self, collection_id):
        """Delete a collection (move to trash)"""
        current_user = get_jwt_identity()
        
        try:
            # Validate the ObjectId format
            if not collection_id or len(collection_id) != 24:
                return {'message': 'Invalid collection ID format. Must be a 24-character hexadecimal string.'}, 400
                
            try:
                # Try to convert to ObjectId to validate it
                object_id = ObjectId(collection_id)
            except InvalidId:
                return {'message': 'Invalid collection ID format. Must be a valid 24-character hexadecimal string.'}, 400
                
            # Find the collection first
            collection = db.collections.find_one({
                '_id': object_id,
                'owner_id': current_user
            })
            
            if not collection:
                return {'message': 'Collection not found'}, 404
                
            # Move to trash
            trash_item = {
                'name': collection['name'],
                'user_id': current_user,
                'owner_id': current_user,
                'created_at': collection.get('created_at'),
                'updated_at': collection.get('updated_at'),
                'files': collection.get('files', []),
                'type': 'collection',
                'deleted_at': datetime.now(),
                'original_id': str(object_id)
            }
            
            # Insert into TrashBin collection
            db.TrashBin.insert_one(trash_item)
            
            # Delete from collections
            db.collections.delete_one({
                '_id': object_id,
                'owner_id': current_user
            })
            
            return {'message': 'Collection moved to trash'}, 200
        except Exception as e:
            print(f"Error deleting collection: {str(e)}")
            return {'message': 'An error occurred while processing your request'}, 500

@api.route('/<string:collection_id>/files')
class CollectionFiles(Resource):
    @jwt_required()
    @api.doc(responses={
        200: 'Collection files retrieved successfully',
        404: 'Collection not found',
        401: 'Unauthorized'
    })
    def get(self, collection_id):
        """Get all files in a collection"""
        current_user = get_jwt_identity()
        
        try:
            # Find the collection by ID and owner
            collection = db.collections.find_one({
                '_id': ObjectId(collection_id),
                'owner_id': current_user
            })
            
            if not collection:
                return {'message': 'Collection not found'}, 404
            
            # Get file IDs from collection
            file_ids = collection.get('files', [])
            
            # Parse query parameters for filtering
            parser = reqparse.RequestParser()
            parser.add_argument('type', type=str, help='Filter by file type (image, video, document)')
            args = parser.parse_args()
            
            # Build query to get files
            query = {
                '_id': {'$in': [ObjectId(file_id) for file_id in file_ids]}
            }
            
            # Add file type filter if provided
            if args['type'] and args['type'] in ['image', 'video', 'document', 'other']:
                query['file_type'] = args['type']
            
            # Get files from database
            files = []
            for file in db.Files.find(query):
                files.append({
                    'id': str(file['_id']),
                    'filename': file['filename'],
                    'file_type': file['file_type'],
                    'file_size': file['file_size'],
                    'upload_date': file['upload_date'].isoformat(),
                    'description': file.get('description', ''),
                    'download_url': f"/api/files/download/{str(file['_id'])}"
                })
            
            # Return files in collection
            return {
                'collection_id': str(collection['_id']),
                'collection_name': collection['name'],
                'files_count': len(files),
                'files': files
            }, 200
            
        except Exception as e:
            return {'message': f'Error retrieving files: {str(e)}'}, 400 