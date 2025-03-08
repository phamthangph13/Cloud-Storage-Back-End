from flask import request
from flask_restx import Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId
import os
from datetime import datetime

from RestoreController.routes import api
from Authenticator import db

# Models for documentation
restore_model = api.model('RestoreModel', {
    'item_id': fields.String(required=True, description='ID of the file or collection to restore')
})

trash_item_model = api.model('TrashItemModel', {
    'id': fields.String(description='Item ID'),
    'name': fields.String(description='Item name'),
    'type': fields.String(description='Item type (file or collection)'),
    'deleted_at': fields.DateTime(description='Deletion date'),
    'original_path': fields.String(description='Original file path for files'),
    'size': fields.Integer(description='File size in bytes for files')
})

@api.route('')
class TrashList(Resource):
    @jwt_required()
    @api.doc(responses={
        200: 'Trash items retrieved successfully',
        401: 'Unauthorized'
    })
    @api.marshal_list_with(trash_item_model)
    def get(self):
        """Get all items in trash for the current user"""
        user_id = get_jwt_identity()
        
        # Get files in trash
        trash_files = list(db.TrashBin.find({
            'user_id': user_id,
            'type': 'file'
        }))
        
        # Get collections in trash
        trash_collections = list(db.TrashBin.find({
            'user_id': user_id,
            'type': 'collection'
        }))
        
        # Format response
        trash_items = []
        
        for file in trash_files:
            trash_items.append({
                'id': str(file['_id']),
                'name': file['filename'],
                'type': 'file',
                'deleted_at': file['deleted_at'],
                'original_path': file.get('file_path', ''),
                'size': file.get('file_size', 0)
            })
            
        for collection in trash_collections:
            trash_items.append({
                'id': str(collection['_id']),
                'name': collection['name'],
                'type': 'collection',
                'deleted_at': collection['deleted_at']
            })
            
        return trash_items, 200

@api.route('/file/<string:file_id>')
class RestoreFile(Resource):
    @jwt_required()
    @api.doc(responses={
        200: 'File restored successfully',
        404: 'File not found in trash',
        401: 'Unauthorized'
    })
    def post(self, file_id):
        """Restore a file from trash"""
        user_id = get_jwt_identity()
        
        try:
            # Find file in trash
            trash_file = db.TrashBin.find_one({
                '_id': ObjectId(file_id),
                'user_id': user_id,
                'type': 'file'
            })
            
            if not trash_file:
                return {'message': 'File not found in trash'}, 404
                
            # Restore file to the Files collection
            restored_file = {
                'filename': trash_file['filename'],
                'file_type': trash_file['file_type'],
                'file_size': trash_file['file_size'],
                'file_path': trash_file.get('file_path', ''),
                'upload_date': trash_file.get('upload_date', datetime.now()),
                'description': trash_file.get('description', ''),
                'user_id': user_id,
                'collections': trash_file.get('collections', []),
                'stored_filename': trash_file.get('stored_filename', ''),
                'file_data': trash_file.get('file_data', b'')
            }
            
            # Insert into Files collection
            db.Files.insert_one(restored_file)
            
            # Remove from trash
            db.TrashBin.delete_one({'_id': ObjectId(file_id)})
            
            return {'message': 'File restored successfully'}, 200
            
        except Exception as e:
            return {'message': f'Error: {str(e)}'}, 500

@api.route('/collection/<string:collection_id>')
class RestoreCollection(Resource):
    @jwt_required()
    @api.doc(responses={
        200: 'Collection restored successfully',
        404: 'Collection not found in trash',
        401: 'Unauthorized'
    })
    def post(self, collection_id):
        """Restore a collection from trash"""
        user_id = get_jwt_identity()
        
        try:
            # Find collection in trash
            trash_collection = db.TrashBin.find_one({
                '_id': ObjectId(collection_id),
                'user_id': user_id,
                'type': 'collection'
            })
            
            if not trash_collection:
                return {'message': 'Collection not found in trash'}, 404
                
            # Restore collection
            restored_collection = {
                'name': trash_collection['name'],
                'owner_id': user_id,
                'created_at': trash_collection.get('created_at', datetime.now()),
                'updated_at': datetime.now()
            }
            
            # Insert into collections
            db.collections.insert_one(restored_collection)
            
            # Remove from trash
            db.TrashBin.delete_one({'_id': ObjectId(collection_id)})
            
            return {'message': 'Collection restored successfully'}, 200
            
        except Exception as e:
            return {'message': f'Error: {str(e)}'}, 500

@api.route('/<string:item_id>')
class DeletePermanently(Resource):
    @jwt_required()
    @api.doc(responses={
        200: 'Item deleted permanently',
        404: 'Item not found in trash',
        401: 'Unauthorized'
    })
    def delete(self, item_id):
        """Permanently delete an item from trash"""
        user_id = get_jwt_identity()
        
        try:
            # Find item in trash
            trash_item = db.TrashBin.find_one({
                '_id': ObjectId(item_id),
                'user_id': user_id
            })
            
            if not trash_item:
                return {'message': 'Item not found in trash'}, 404
                
            # If it's a file, also delete the physical file
            if trash_item['type'] == 'file' and 'file_path' in trash_item and trash_item['file_path'] and os.path.exists(trash_item['file_path']):
                os.remove(trash_item['file_path'])
                
            # Remove from trash
            db.TrashBin.delete_one({'_id': ObjectId(item_id)})
            
            return {'message': 'Item deleted permanently'}, 200
            
        except Exception as e:
            return {'message': f'Error: {str(e)}'}, 500 