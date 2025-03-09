from flask import Blueprint
from flask_restx import Api, Namespace

# Create the restore blueprint with url_prefix
restore_bp = Blueprint('restore', __name__, url_prefix='/api/restore')

# Create a namespace for trash operations that can be imported elsewhere
trash_namespace = Namespace('trash', description='Trash operations')

# Create the API on the blueprint
api = Api(restore_bp, 
          title='Restore API', 
          description='API for restoring files and collections from trash',
          doc='/doc')

# Import routes
from RestoreController.routes.restore_routes import api as restore_namespace

# Add namespace to API
api.add_namespace(restore_namespace, path='')

# Export trash-related classes to be used elsewhere
from RestoreController.routes.restore_routes import TrashList, trash_item_model 