from flask import Blueprint
from flask_restx import Api, Namespace

restore_bp = Blueprint('restore', __name__, url_prefix='/api/restore')
api = Api(restore_bp, title='Restore API', description='API for restoring files and collections from trash')

# Create a namespace for trash operations that can be imported elsewhere
trash_namespace = Namespace('trash', description='Trash operations')

from RestoreController.routes.restore_routes import api as restore_namespace
api.add_namespace(restore_namespace)

# Export trash-related classes to be used elsewhere
from RestoreController.routes.restore_routes import TrashList, trash_item_model 