from flask import request, send_file
from flask_restx import Resource, fields, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import os
import uuid
import datetime
from bson.objectid import ObjectId
from FileController import api
from Authenticator import db

# Define storage directory
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Create subdirectories for different file types
IMAGE_FOLDER = os.path.join(UPLOAD_FOLDER, 'images')
VIDEO_FOLDER = os.path.join(UPLOAD_FOLDER, 'videos')
DOCUMENT_FOLDER = os.path.join(UPLOAD_FOLDER, 'documents')

os.makedirs(IMAGE_FOLDER, exist_ok=True)
os.makedirs(VIDEO_FOLDER, exist_ok=True)
os.makedirs(DOCUMENT_FOLDER, exist_ok=True)

# Define allowed file extensions
IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg'}
VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm'}
DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv', 'json', 'xml'}

# Helper function to determine file type
def get_file_type(filename):
    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if extension in IMAGE_EXTENSIONS:
        return 'image', IMAGE_FOLDER
    elif extension in VIDEO_EXTENSIONS:
        return 'video', VIDEO_FOLDER
    elif extension in DOCUMENT_EXTENSIONS:
        return 'document', DOCUMENT_FOLDER
    else:
        return 'other', UPLOAD_FOLDER

# File upload parser
upload_parser = api.parser()
upload_parser.add_argument('file', location='files', type=FileStorage, required=True, help='File to upload')
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
        uploaded_file = args['file']
        description = args.get('description', '')
        
        if not uploaded_file:
            return {'message': 'No file provided'}, 400
        
        # Secure the filename
        original_filename = secure_filename(uploaded_file.filename)
        
        # Determine file type and storage location
        file_type, storage_folder = get_file_type(original_filename)
        
        # Generate a unique filename
        unique_filename = f"{uuid.uuid4()}_{original_filename}"
        file_path = os.path.join(storage_folder, unique_filename)
        
        # Save the file
        uploaded_file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Get user ID from JWT token
        user_id = get_jwt_identity()
        
        # Create file record in database
        file_record = {
            'filename': original_filename,
            'stored_filename': unique_filename,
            'file_path': file_path,
            'file_type': file_type,
            'file_size': file_size,
            'upload_date': datetime.datetime.now(),
            'description': description,
            'user_id': user_id
        }
        
        # Insert into MongoDB
        result = db.Files.insert_one(file_record)
        file_id = str(result.inserted_id)
        
        # Generate download URL
        download_url = f"/api/files/download/{file_id}"
        
        return {
            'message': 'File uploaded successfully',
            'file': {
                'id': file_id,
                'filename': original_filename,
                'stored_filename': unique_filename,
                'file_type': file_type,
                'file_size': file_size,
                'upload_date': file_record['upload_date'].isoformat(),
                'description': description,
                'user_id': user_id,
                'download_url': download_url
            }
        }, 200

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
            
            # Return the file
            return send_file(
                file_record['file_path'],
                as_attachment=True,
                download_name=file_record['filename']
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
                'stored_filename': file['stored_filename'],
                'file_type': file['file_type'],
                'file_size': file['file_size'],
                'upload_date': file['upload_date'].isoformat(),
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
                'stored_filename': file_record['stored_filename'],
                'file_type': file_record['file_type'],
                'file_size': file_record['file_size'],
                'upload_date': file_record['upload_date'].isoformat(),
                'description': file_record.get('description', ''),
                'user_id': file_record['user_id'],
                'download_url': f"/api/files/download/{file_id}"
            }, 200
            
        except Exception as e:
            return {'message': f'Error retrieving file details: {str(e)}'}, 500
    
    @jwt_required()
    @api.doc(responses={
        200: 'File deleted successfully',
        404: 'File not found',
        401: 'Unauthorized'
    })
    def delete(self, file_id):
        """Delete a file by ID"""
        try:
            # Find file in database
            file_record = db.Files.find_one({'_id': ObjectId(file_id)})
            
            if not file_record:
                return {'message': 'File not found'}, 404
            
            # Check if user has access to this file
            user_id = get_jwt_identity()
            if file_record['user_id'] != user_id:
                return {'message': 'You do not have permission to delete this file'}, 403
            
            # Delete file from storage
            if os.path.exists(file_record['file_path']):
                os.remove(file_record['file_path'])
            
            # Delete file record from database
            db.Files.delete_one({'_id': ObjectId(file_id)})
            
            return {'message': 'File deleted successfully'}, 200
            
        except Exception as e:
            return {'message': f'Error deleting file: {str(e)}'}, 500