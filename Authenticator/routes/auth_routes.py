from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from Authenticator.models.user import User
from Authenticator.utils.email_utils import (
    generate_verification_token, generate_reset_token, 
    verify_token, send_verification_email, send_password_reset_email
)
from Authenticator import db
import re
from pymongo.errors import DuplicateKeyError

api = Namespace('auth', description='Authentication operations')

# Models for request/response documentation
register_model = api.model('Register', {
    'email': fields.String(required=True, description='User email'),
    'password': fields.String(required=True, description='User password')
})

login_model = api.model('Login', {
    'email': fields.String(required=True, description='User email'),
    'password': fields.String(required=True, description='User password')
})

forgot_password_model = api.model('ForgotPassword', {
    'email': fields.String(required=True, description='User email')
})

reset_password_model = api.model('ResetPassword', {
    'token': fields.String(required=True, description='Reset token'),
    'new_password': fields.String(required=True, description='New password')
})

token_model = api.model('Token', {
    'token': fields.String(required=True, description='Verification token')
})

# Helper function to validate email
def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

# Helper function to validate password
def is_valid_password(password):
    # At least 8 characters, containing letters and numbers
    return len(password) >= 8 and any(c.isalpha() for c in password) and any(c.isdigit() for c in password)

@api.route('/register')
class Register(Resource):
    @api.expect(register_model)
    @api.doc(responses={
        201: 'User registered successfully',
        400: 'Invalid input',
        409: 'Email already exists'
    })
    def post(self):
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        # Validate input
        if not email or not password:
            return {'message': 'Email and password are required'}, 400
        
        if not is_valid_email(email):
            return {'message': 'Invalid email format'}, 400
        
        if not is_valid_password(password):
            return {'message': 'Password must be at least 8 characters and contain both letters and numbers'}, 400
        
        try:
            # Create new user
            user = User.create_user(db, email, password)
            
            # Generate verification token and send email
            token = generate_verification_token(user['_id'])
            send_verification_email(user['email'], token)
            
            return {'message': 'User registered successfully. Please check your email to verify your account.'}, 201
        except DuplicateKeyError:
            return {'message': 'Email already registered'}, 409

@api.route('/verify-email')
class VerifyEmail(Resource):
    @api.expect(token_model)
    @api.doc(responses={
        200: 'Email verified successfully',
        400: 'Invalid or expired token'
    })
    def post(self):
        data = request.json
        token = data.get('token')
        
        if not token:
            return {'message': 'Token is required'}, 400
        
        user_id = verify_token(token, 'email_verification')
        
        if not user_id:
            return {'message': 'Invalid or expired token'}, 400
        
        user = User.find_by_id(db, user_id)
        
        if not user:
            return {'message': 'User not found'}, 404
        
        User.activate_user(db, user_id)
        
        return {'message': 'Email verified successfully'}, 200

@api.route('/login')
class Login(Resource):
    @api.expect(login_model)
    @api.doc(responses={
        200: 'Login successful',
        400: 'Invalid input',
        401: 'Invalid credentials or account not verified'
    })
    def post(self):
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return {'message': 'Email and password are required'}, 400
        
        user = User.find_by_email(db, email)
        
        if not user or not User.check_password(user, password):
            return {'message': 'Invalid email or password'}, 401
        
        if not user.get('is_active', False):
            return {'message': 'Please verify your email before logging in'}, 401
        
        access_token = create_access_token(identity=str(user['_id']))
        
        return {
            'message': 'Login successful',
            'access_token': access_token,
            'user': User.to_dict(user)
        }, 200

@api.route('/forgot-password')
class ForgotPassword(Resource):
    @api.expect(forgot_password_model)
    @api.doc(responses={
        200: 'Password reset email sent',
        400: 'Invalid input',
        404: 'User not found'
    })
    def post(self):
        data = request.json
        email = data.get('email')
        
        if not email:
            return {'message': 'Email is required'}, 400
        
        user = User.find_by_email(db, email)
        
        if not user:
            # For security reasons, don't reveal that the user doesn't exist
            return {'message': 'If your email is registered, you will receive a password reset link'}, 200
        
        token = generate_reset_token(user['_id'])
        send_password_reset_email(user['email'], token)
        
        return {'message': 'Password reset email sent'}, 200

@api.route('/reset-password')
class ResetPassword(Resource):
    @api.expect(reset_password_model)
    @api.doc(responses={
        200: 'Password reset successful',
        400: 'Invalid input or token',
        404: 'User not found'
    })
    def post(self):
        data = request.json
        token = data.get('token')
        new_password = data.get('new_password')
        
        if not token or not new_password:
            return {'message': 'Token and new password are required'}, 400
        
        if not is_valid_password(new_password):
            return {'message': 'Password must be at least 8 characters and contain both letters and numbers'}, 400
        
        user_id = verify_token(token, 'password_reset')
        
        if not user_id:
            return {'message': 'Invalid or expired token'}, 400
        
        user = User.find_by_id(db, user_id)
        
        if not user:
            return {'message': 'User not found'}, 404
        
        User.update_password(db, user_id, new_password)
        
        return {'message': 'Password reset successful'}, 200

@api.route('/user')
class UserInfo(Resource):
    @jwt_required()
    @api.doc(responses={
        200: 'User information retrieved successfully',
        404: 'User not found'
    })
    def get(self):
        """Get current user information"""
        user_id = get_jwt_identity()
        user = User.find_by_id(db, user_id)
        
        if not user:
            return {'message': 'User not found'}, 404
        
        return {'user': User.to_dict(user)}, 200


# Add this new route
@api.route('/verify-email-link')
class VerifyEmailLink(Resource):
    @api.doc(params={'token': 'Verification token'})
    def get(self):
        """Verify email through a direct link"""
        token = request.args.get('token')
        
        if not token:
            return {'message': 'Token is required'}, 400
        
        user_id = verify_token(token, 'email_verification')
        
        if not user_id:
            return {'message': 'Invalid or expired token'}, 400
        
        user = User.find_by_id(db, user_id)
        
        if not user:
            return {'message': 'User not found'}, 404
        
        User.activate_user(db, user_id)
        
        # You can return a success page or redirect to a frontend page
        return {'message': 'Email verified successfully. You can now log in.'}, 200