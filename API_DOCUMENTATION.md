# Authentication API Documentation

This document provides detailed information about the authentication service endpoints.

## Base URL

```
http://localhost:5000/api/auth
```

## Authentication

Most endpoints require JWT authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### 1. Register User

**Endpoint:** `POST /register`

**Description:** Register a new user account.

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "YourPassword123"
}
```

**Requirements:**
- Email must be in valid format
- Password must be at least 8 characters and contain both letters and numbers

**Response:**
- Success (201):
```json
{
    "message": "User registered successfully. Please check your email to verify your account."
}
```
- Error (400/409):
```json
{
    "message": "Error message"
}
```

### 2. Verify Email

#### Method 1: Via API

**Endpoint:** `POST /verify-email`

**Request Body:**
```json
{
    "token": "verification_token"
}
```

**Response:**
- Success (200):
```json
{
    "message": "Email verified successfully"
}
```

#### Method 2: Via Link

**Endpoint:** `GET /verify-email-link?token=verification_token`

**Response:**
- Success (200):
```json
{
    "message": "Email verified successfully. You can now log in."
}
```

### 3. Login

**Endpoint:** `POST /login`

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "YourPassword123"
}
```

**Response:**
- Success (200):
```json
{
    "message": "Login successful",
    "access_token": "jwt_token",
    "user": {
        "email": "user@example.com",
        "is_active": true
    }
}
```

### 4. Forgot Password

**Endpoint:** `POST /forgot-password`

**Request Body:**
```json
{
    "email": "user@example.com"
}
```

**Response:**
- Success (200):
```json
{
    "message": "If your email is registered, you will receive a password reset link"
}
```

### 5. Reset Password

**Endpoint:** `POST /reset-password`

**Request Body:**
```json
{
    "token": "reset_token",
    "new_password": "NewPassword123"
}
```

**Requirements:**
- New password must be at least 8 characters and contain both letters and numbers

**Response:**
- Success (200):
```json
{
    "message": "Password reset successful"
}
```

### 6. Get User Information

**Endpoint:** `GET /user`

**Authentication Required:** Yes (JWT Token)

**Response:**
- Success (200):
```json
{
    "user": {
        "email": "user@example.com",
        "is_active": true
    }
}
```

## Error Responses

The API uses standard HTTP status codes:

- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 409: Conflict

Error responses follow this format:
```json
{
    "message": "Description of the error"
}
```

## Notes

1. All tokens (verification, reset) have expiration times:
   - Email verification tokens: 24 hours
   - Password reset tokens: 1 hour

2. Users must verify their email before they can log in

3. For security reasons, some endpoints (like forgot-password) don't reveal whether a user exists

4. All passwords must meet minimum security requirements