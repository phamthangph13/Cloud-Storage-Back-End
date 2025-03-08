from flask import request
from flask_restx import Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId
from CollectionController import api
from Authenticator import db
import datetime

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
            'created_at': datetime.datetime.utcnow(),
            'updated_at': datetime.datetime.utcnow()
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
        """Get a specific collection by ID"""
        current_user = get_jwt_identity()
        
        try:
            # Find the collection by ID and owner
            collection = db.collections.find_one({
                '_id': ObjectId(collection_id),
                'owner_id': current_user
            })
            
            if not collection:
                return {'message': 'Collection not found'}, 404
            
            # Format and return the collection
            return {
                'collection': {
                    'id': str(collection['_id']),
                    'name': collection['name'],
                    'owner_id': collection['owner_id'],
                    'created_at': collection['created_at'],
                    'updated_at': collection['updated_at']
                }
            }, 200
        except Exception as e:
            return {'message': 'Invalid collection ID'}, 400
    
    @jwt_required()
    @api.expect(collection_update_model)
    @api.doc(responses={
        200: 'Collection updated successfully',
        400: 'Invalid input',
        404: 'Collection not found',
        401: 'Unauthorized'
    })
    def put(self, collection_id):
        """Update a collection name"""
        current_user = get_jwt_identity()
        data = request.json
        
        # Validate input
        if not data or 'name' not in data or not data['name'].strip():
            return {'message': 'Collection name is required'}, 400
        
        try:
            # Find and update the collection
            result = db.collections.update_one(
                {
                    '_id': ObjectId(collection_id),
                    'owner_id': current_user
                },
                {
                    '$set': {
                        'name': data['name'].strip(),
                        'updated_at': datetime.datetime.utcnow()
                    }
                }
            )
            
            if result.matched_count == 0:
                return {'message': 'Collection not found'}, 404
            
            # Get the updated collection
            updated_collection = db.collections.find_one({'_id': ObjectId(collection_id)})
            
            return {
                'message': 'Collection updated successfully',
                'collection': {
                    'id': str(updated_collection['_id']),
                    'name': updated_collection['name'],
                    'owner_id': updated_collection['owner_id'],
                    'created_at': updated_collection['created_at'],
                    'updated_at': updated_collection['updated_at']
                }
            }, 200
        except Exception as e:
            return {'message': 'Invalid collection ID'}, 400
    
    @jwt_required()
    @api.doc(responses={
        200: 'Collection deleted successfully',
        404: 'Collection not found',
        401: 'Unauthorized'
    })
    def delete(self, collection_id):
        """Delete a collection"""
        current_user = get_jwt_identity()
        
        try:
            # Find and delete the collection
            result = db.collections.delete_one({
                '_id': ObjectId(collection_id),
                'owner_id': current_user
            })
            
            if result.deleted_count == 0:
                return {'message': 'Collection not found'}, 404
            
            return {'message': 'Collection deleted successfully'}, 200
        except Exception as e:
            return {'message': 'Invalid collection ID'}, 400 