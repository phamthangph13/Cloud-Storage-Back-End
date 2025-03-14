from flask import Flask
import json
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from flask_restx import Api
from flask_cors import CORS
import os
from pymongo import MongoClient
from datetime import datetime

# Custom JSON encoder to handle datetime objects
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__str__'):
            return str(obj)
        return super(CustomJSONEncoder, self).default(obj)

# Initialize extensions
mail = Mail()
jwt = JWTManager()
mongo_client = None
db = None

def create_app():
    app = Flask(__name__)
    
    # Configure app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # Set custom JSON encoder
    app.json_encoder = CustomJSONEncoder
    
    # JWT Configuration
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False # FOREVER
    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    app.config['JWT_HEADER_NAME'] = 'Authorization'
    app.config['JWT_HEADER_TYPE'] = 'Bearer'
    
    # Mail Configuration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'dounecompany@gmail.com'
    app.config['MAIL_PASSWORD'] = 'zasa vbpy arko snov'
    app.config['MAIL_DEFAULT_SENDER'] = 'dounecompany@gmail.com'
    
    # MongoDB Configuration
    app.config['MONGO_URI'] = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
    
    # Initialize extensions with app
    mail.init_app(app)
    jwt.init_app(app)
    
    # Configure CORS with specific options
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "allow_headers": ["Content-Type", "Authorization"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "expose_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Initialize MongoDB connection
    global mongo_client, db
    mongo_client = MongoClient(app.config['MONGO_URI'])
    db = mongo_client['CloudStorageApp']
    
    # Ensure Users collection exists
    if 'Users' not in db.list_collection_names():
        db.create_collection('Users')
    
    # Create indexes for email uniqueness - always ensure this index exists
    db.Users.create_index('email', unique=True)
    
    # Create API with Swagger documentation
    authorizations = {
        'Bearer Auth': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': "Type in the *'Value'* input box below: **'Bearer &lt;JWT&gt;'**, where JWT is the token"
        },
    }
    
    api = Api(app, version='1.0', title='Authentication API',
              description='A simple authentication API with Flask-RestX',
              authorizations=authorizations, security='Bearer Auth')
    
    # Configure Flask-RestX to use our custom JSON encoder
    @api.representation('application/json')
    def output_json(data, code, headers=None):
        resp = app.response_class(
            response=json.dumps(data, cls=CustomJSONEncoder),
            status=code,
            mimetype='application/json'
        )
        if headers:
            for header, value in headers.items():
                resp.headers[header] = value
        return resp
    
    # Import and register blueprints/routes
    from Authenticator.routes.auth_routes import api as auth_ns
    api.add_namespace(auth_ns, path='/api/auth')
    
    # Import and register file controller routes
    from FileController import api as file_ns
    api.add_namespace(file_ns, path='/api/files')

    # Import and register collection controller routes
    from CollectionController import api as collection_ns
    api.add_namespace(collection_ns, path='/api/collections')
    
    # Import and register restore controller routes using blueprint
    from RestoreController import restore_bp
    app.register_blueprint(restore_bp)
    
    # Register trash routes
    from RestoreController.routes.restore_routes import api as trash_ns
    api.add_namespace(trash_ns, path='/api/trash')
    
    return app

