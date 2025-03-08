from flask_restx import Namespace

api = Namespace('collections', description='Collection operations')

from CollectionController.routes import collection_routes 