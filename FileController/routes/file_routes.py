from flask import request, send_file
from flask_restx import Resource, fields, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import os
import uuid
from datetime import datetime
from bson.objectid import ObjectId
from FileController import api 
from Authenticator import db
from io import BytesIO 
from CollectionController.models.collection import Collection
import re

# Remove filesystem storage related code

# Define allowed file extensions
IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg'}
VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm'}
DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv', 'json', 'xml'}

# File rename model
file_rename_model = api.model('FileRename', {
    'new_filename': fields.String(required=True, description='New filename for the file')
})

# Helper function to determine file type
def get_file_type(filename):
    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if extension in IMAGE_EXTENSIONS:
        return 'image'
    elif extension in VIDEO_EXTENSIONS:
        return 'video'
    elif extension in DOCUMENT_EXTENSIONS:
        return 'document'
    else:
        return 'other'

# File upload parser
upload_parser = api.parser()
upload_parser.add_argument('file', location='files', type=FileStorage, required=True, action='append', help='Files to upload (multiple allowed)')
upload_parser.add_argument('description', type=str, help='File description')

# File response model
file_model = api.model('File', {
    'id': fields.String(description='File ID'),
    'filename': fields.String(description='Original filename'),
    'stored_filename': fields.String(description='Stored filename'),
    'file_type': fields.String(description='File type (image, video, document, other)'),
    'file_size': fields.Integer(description='File size in bytes'),
    'upload_date': fields.DateTime(description='Upload date'),
    'description': fields.String(description='File description'),
    'user_id': fields.String(description='User ID who uploaded the file'),
    'download_url': fields.String(description='URL to download the file')
})

# File list model
file_list_model = api.model('FileList', {
    'files': fields.List(fields.Nested(file_model)),
    'total': fields.Integer(description='Total number of files')
})

# Add to collection request model
add_to_collection_model = api.model('AddToCollection', {
    'collection_id': fields.String(required=True, description='ID of the collection to add the file to')
})

@api.route('/upload')
class FileUpload(Resource):
    @jwt_required()
    @api.expect(upload_parser)
    @api.doc(responses={
        200: 'File uploaded successfully',
        400: 'Invalid file or file type',
        401: 'Unauthorized'
    })
    def post(self):
        """Upload a file (image, video, document)"""
        args = upload_parser.parse_args()
        uploaded_files = args['file']
        description = args.get('description', '')
        results = []
        errors = []
        
        if not uploaded_files:
            return {'message': 'No files provided'}, 400
        
        # Secure the filename
        for uploaded_file in uploaded_files:
            try:
                original_filename = secure_filename(uploaded_file.filename)
                
                # Determine file type and storage location
                file_type = get_file_type(original_filename)
                
                # Generate a unique filename
                unique_filename = f"{uuid.uuid4()}_{original_filename}"
                # Read file content as binary
                file_data = uploaded_file.read()
                if len(file_data) == 0:
                    errors.append(f'Empty file: {original_filename}')
                    continue
                
                # Get file size from content length
                file_size = len(file_data)
                
                # Get user ID from JWT token
                user_id = get_jwt_identity()
                
                # Create file record in database
                file_record = {
                    'filename': original_filename,
                    'stored_filename': unique_filename,
                    'file_data': file_data,
                    'file_type': file_type,
                    'file_size': file_size,
                    'upload_date': datetime.now(),
                    'description': description,
                    'user_id': user_id
                }
                
                # Insert into MongoDB
                result = db.Files.insert_one(file_record)
                file_id = str(result.inserted_id)
                download_url = f"/api/files/download/{file_id}"
                
                results.append({
                    'id': file_id,
                    'filename': original_filename,
                    'stored_filename': unique_filename,
                    'file_type': file_type,
                    'file_size': file_size,
                    'upload_date': file_record['upload_date'].isoformat(),
                    'description': description,
                    'user_id': user_id,
                    'download_url': download_url
                })
            except Exception as e:
                errors.append(f'Error uploading {original_filename}: {str(e)}')
        response = {'message': 'Batch upload completed', 'success_count': len(results), 'files': results}
        if errors:
            response['error_count'] = len(errors)
            response['errors'] = errors
        return response, 200 if not errors else 207

@api.route('/download/<string:file_id>')
class FileDownload(Resource):
    @jwt_required()
    @api.doc(responses={
        200: 'File downloaded successfully',
        404: 'File not found',
        401: 'Unauthorized'
    })
    def get(self, file_id):
        """Download a file by ID"""
        try:
            # Find file in database
            file_record = db.Files.find_one({'_id': ObjectId(file_id)})
            
            if not file_record:
                return {'message': 'File not found'}, 404
            
            # Check if user has access to this file
            user_id = get_jwt_identity()
            if file_record['user_id'] != user_id:
                # In a real app, you might want to check if the file is shared with this user
                return {'message': 'You do not have permission to access this file'}, 403
            
            # Check if file data exists
            if 'file_data' not in file_record or not file_record['file_data']:
                return {'message': 'File data is missing or corrupted'}, 404
            
            # Return the file
            return send_file(
                BytesIO(file_record['file_data']),
                as_attachment=True,
                download_name=file_record['filename'],
                mimetype='application/octet-stream'
            )
            
            
        except Exception as e:
            return {'message': f'Error downloading file: {str(e)}'}, 500

@api.route('/files')
class FileList(Resource):
    @jwt_required()
    @api.doc(responses={
        200: 'Files retrieved successfully',
        401: 'Unauthorized'
    })
    def get(self):
        """Get list of files for current user"""
        user_id = get_jwt_identity()
        
        # Parse query parameters
        parser = reqparse.RequestParser()
        parser.add_argument('type', type=str, help='Filter by file type (image, video, document)')
        parser.add_argument('page', type=int, default=1, help='Page number')
        parser.add_argument('per_page', type=int, default=10, help='Items per page')
        args = parser.parse_args()
        
        # Build query
        query = {'user_id': user_id}
        if args['type'] and args['type'] in ['image', 'video', 'document', 'other']:
            query['file_type'] = args['type']
        
        # Calculate pagination
        skip = (args['page'] - 1) * args['per_page']
        
        # Get files from database
        files_cursor = db.Files.find(query).skip(skip).limit(args['per_page']).sort('upload_date', -1)
        total_files = db.Files.count_documents(query)
        
        # Format response
        files = []
        for file in files_cursor:
            files.append({
                'id': str(file['_id']),
                'filename': file['filename'],
                'stored_filename': file.get('stored_filename', file.get('filename', '')),
                'file_type': file['file_type'],
                'file_size': file['file_size'],
                'upload_date': file['upload_date'].isoformat() if file.get('upload_date') else '',
                'description': file.get('description', ''),
                'user_id': file['user_id'],
                'download_url': f"/api/files/download/{str(file['_id'])}"
            })
        
        return {
            'files': files,
            'total': total_files,
            'page': args['page'],
            'per_page': args['per_page'],
            'pages': (total_files + args['per_page'] - 1) // args['per_page']
        }, 200

@api.route('/files/<string:file_id>')
class FileDetail(Resource):
    @jwt_required()
    @api.doc(responses={
        200: 'File details retrieved successfully',
        404: 'File not found',
        401: 'Unauthorized'
    })
    def get(self, file_id):
        """Get file details by ID"""
        try:
            # Find file in database
            file_record = db.Files.find_one({'_id': ObjectId(file_id)})
            
            if not file_record:
                return {'message': 'File not found'}, 404
            
            # Check if user has access to this file
            user_id = get_jwt_identity()
            if file_record['user_id'] != user_id:
                # In a real app, you might want to check if the file is shared with this user
                return {'message': 'You do not have permission to access this file'}, 403
            
            # Return file details
            return {
                'id': str(file_record['_id']),
                'filename': file_record['filename'],
                'stored_filename': file_record.get('stored_filename', file_record.get('filename', '')),
                'file_type': file_record['file_type'],
                'file_size': file_record['file_size'],
                'upload_date': file_record['upload_date'].isoformat() if file_record.get('upload_date') else '',
                'description': file_record.get('description', ''),
                'user_id': file_record['user_id'],
                'download_url': f"/api/files/download/{file_id}"
            }, 200
            
        except Exception as e:
            return {'message': f'Error retrieving file details: {str(e)}'}, 500
    
    @jwt_required()
    @api.expect(file_rename_model)
    @api.doc(responses={
        200: 'File renamed successfully',
        400: 'Invalid filename',
        404: 'File not found',
        401: 'Unauthorized',
        403: 'Permission denied'
    })
    def put(self, file_id):
        """Rename a file by ID"""
        try:
            data = request.json
            
            # Validate input
            if not data or 'new_filename' not in data or not data['new_filename'].strip():
                return {'message': 'New filename is required'}, 400
            
            new_filename = secure_filename(data['new_filename'].strip())
            
            # Check if filename is valid
            if not new_filename:
                return {'message': 'Invalid filename'}, 400
            
            # Find file in database
            file_record = db.Files.find_one({'_id': ObjectId(file_id)})
            
            if not file_record:
                return {'message': 'File not found'}, 404
            
            # Check if user has access to this file
            user_id = get_jwt_identity()
            if file_record['user_id'] != user_id:
                return {'message': 'You do not have permission to modify this file'}, 403
            
            # Get file extension from original filename
            old_filename = file_record['filename']
            if '.' in old_filename:
                extension = old_filename.rsplit('.', 1)[1].lower()
                
                # Make sure new filename has extension
                if '.' not in new_filename:
                    new_filename = f"{new_filename}.{extension}"
            
            # Check if file with the same name already exists for this user
            name_without_ext = new_filename
            ext = ""
            if '.' in new_filename:
                name_without_ext, ext = new_filename.rsplit('.', 1)
                ext = f".{ext}"
            
            # Find if there are any files with the same name (excluding current file)
            existing_files = list(db.Files.find({
                '_id': {'$ne': ObjectId(file_id)},
                'user_id': user_id,
                'filename': new_filename
            }))
            
            # If a file with the same name exists, suggest a new name
            if existing_files:
                # Count files with similar names (e.g. name(1).ext, name(2).ext)
                similar_files = list(db.Files.find({
                    '_id': {'$ne': ObjectId(file_id)},
                    'user_id': user_id,
                    'filename': {'$regex': f"^{re.escape(name_without_ext)}\\(\\d+\\){re.escape(ext)}$"}
                }))
                
                # Calculate the next number
                highest_num = 0
                for file in similar_files:
                    filename = file['filename']
                    match = re.search(r'\((\d+)\)', filename)
                    if match:
                        num = int(match.group(1))
                        if num > highest_num:
                            highest_num = num
                
                # Generate suggestion with the next number
                suggested_name = f"{name_without_ext}({highest_num + 1}){ext}"
                
                # If the force flag is set, use the suggested name, otherwise return a suggestion
                if data.get('force', False):
                    new_filename = suggested_name
                else:
                    return {
                        'message': 'A file with this name already exists',
                        'suggestion': suggested_name,
                        'requires_confirmation': True
                    }, 409
            
            # Update stored_filename if it exists
            if 'stored_filename' in file_record:
                old_stored = file_record['stored_filename']
                if '_' in old_stored:
                    prefix = old_stored.split('_', 1)[0]
                    new_stored_filename = f"{prefix}_{new_filename}"
                else:
                    # If stored_filename doesn't have UUID prefix
                    new_stored_filename = f"{uuid.uuid4()}_{new_filename}"
                
                # Update to new stored filename
                db.Files.update_one(
                    {'_id': ObjectId(file_id)},
                    {'$set': {'stored_filename': new_stored_filename}}
                )
            
            # Update filename
            db.Files.update_one(
                {'_id': ObjectId(file_id)},
                {'$set': {'filename': new_filename}}
            )
            
            # Get updated file
            updated_file = db.Files.find_one({'_id': ObjectId(file_id)})
            
            # Return updated file details
            return {
                'message': 'File renamed successfully',
                'file': {
                    'id': str(updated_file['_id']),
                    'filename': updated_file['filename'],
                    'stored_filename': updated_file.get('stored_filename', updated_file.get('filename', '')),
                    'file_type': updated_file['file_type'],
                    'file_size': updated_file['file_size'],
                    'upload_date': updated_file['upload_date'].isoformat() if updated_file.get('upload_date') else '',
                    'description': updated_file.get('description', ''),
                    'user_id': updated_file['user_id'],
                    'download_url': f"/api/files/download/{file_id}"
                }
            }, 200
            
        except Exception as e:
            return {'message': f'Error renaming file: {str(e)}'}, 500
    
    @jwt_required()
    @api.doc(responses={
        200: 'File deleted successfully',
        404: 'File not found',
        401: 'Unauthorized'
    })
    def delete(self, file_id):
        """Delete a file by ID (move to trash)"""
        try:
            # Find file in database
            file_record = db.Files.find_one({'_id': ObjectId(file_id)})
            
            if not file_record:
                return {'message': 'File not found'}, 404
            
            # Check if user has access to this file
            user_id = get_jwt_identity()
            if file_record['user_id'] != user_id:
                return {'message': 'You do not have permission to delete this file'}, 403
            
            # Move file to trash instead of deleting
            trash_item = {
                'filename': file_record['filename'],
                'file_type': file_record['file_type'],
                'file_size': file_record['file_size'],
                'file_path': file_record.get('file_path', ''),
                'upload_date': file_record.get('upload_date'),
                'description': file_record.get('description', ''),
                'user_id': user_id,
                'collections': file_record.get('collections', []),
                'stored_filename': file_record.get('stored_filename', ''),
                'file_data': file_record.get('file_data', b''),
                'type': 'file',
                'deleted_at': datetime.now(),
                'original_id': str(file_id)  # Lưu ID gốc của file
            }
            
            # Insert into TrashBin collection
            db.TrashBin.insert_one(trash_item)
            
            # Delete file record from database
            db.Files.delete_one({'_id': ObjectId(file_id)})
            
            return {'message': 'File moved to trash'}, 200
            
        except Exception as e:
            return {'message': f'Error deleting file: {str(e)}'}, 500

@api.route('/files/<string:file_id>/add-to-collection')
class AddFileToCollection(Resource):
    @jwt_required()
    @api.expect(add_to_collection_model)
    @api.doc(responses={
        200: 'File added to collection successfully',
        400: 'Invalid input',
        404: 'File or collection not found',
        401: 'Unauthorized'
    })
    def post(self, file_id):
        """Add a file to a collection"""
        try:
            current_user = get_jwt_identity()
            data = request.json
            
            # Validate input
            if not data or 'collection_id' not in data:
                return {'message': 'Collection ID is required'}, 400
            
            collection_id = data['collection_id']
            
            # Check if file exists and belongs to the user
            file_record = db.Files.find_one({
                '_id': ObjectId(file_id),
                'user_id': current_user
            })
            
            if not file_record:
                return {'message': 'File not found or you do not have permission to access it'}, 404
            
            # Add file to collection
            updated_collection = Collection.add_file(collection_id, current_user, file_id)
            
            if not updated_collection:
                return {'message': 'Collection not found or you do not have permission to access it'}, 404
            
            return {
                'message': 'File added to collection successfully',
                'collection': {
                    'id': str(updated_collection['_id']),
                    'name': updated_collection['name'],
                    'files_count': len(updated_collection.get('files', [])),
                    'updated_at': updated_collection['updated_at']
                }
            }, 200
        except Exception as e:
            return {'message': f'Error adding file to collection: {str(e)}'}, 400

@api.route('/files/<string:file_id>/remove-from-collection/<string:collection_id>')
class RemoveFileFromCollection(Resource):
    @jwt_required()
    @api.doc(responses={
        200: 'File removed from collection successfully',
        404: 'File or collection not found',
        401: 'Unauthorized'
    })
    def delete(self, file_id, collection_id):
        """Remove a file from a collection"""
        try:
            current_user = get_jwt_identity()
            
            # Check if file exists and belongs to the user
            file_record = db.Files.find_one({
                '_id': ObjectId(file_id),
                'user_id': current_user
            })
            
            if not file_record:
                return {'message': 'File not found or you do not have permission to access it'}, 404
            
            # Remove file from collection
            updated_collection = Collection.remove_file(collection_id, current_user, file_id)
            
            if not updated_collection:
                return {'message': 'Collection not found or you do not have permission to access it'}, 404
            
            return {
                'message': 'File removed from collection successfully',
                'collection': {
                    'id': str(updated_collection['_id']),
                    'name': updated_collection['name'],
                    'files_count': len(updated_collection.get('files', [])),
                    'updated_at': updated_collection['updated_at']
                }
            }, 200
        except Exception as e:
            return {'message': f'Error removing file from collection: {str(e)}'}, 400