from flask_restx import Namespace
from RestoreController.routes.restore_routes import trash_item_model  # Import trash model

api = Namespace('files', description='File operations')

from FileController.routes import file_routes
from RestoreController.routes.restore_routes import TrashList

# Register the TrashList resource to handle /api/files/trash
api.add_resource(TrashList, '/trash')