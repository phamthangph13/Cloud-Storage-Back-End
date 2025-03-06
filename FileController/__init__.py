from flask_restx import Namespace

api = Namespace('files', description='File operations')

from FileController.routes import file_routes