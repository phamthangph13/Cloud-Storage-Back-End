# Cloud Storage API Documentation

## Base URL
```
http://localhost:5000
```

## Authentication API Endpoints

### Authentication Base URL
```
http://localhost:5000/api/auth
```

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/register` | POST | Register new user with email verification |
| `/login` | POST | Authenticate user and get JWT token |
| `/forgot-password` | POST | Initiate password reset process |
| `/reset-password` | POST | Complete password reset |
| `/verify-email-link` | GET | Verify email through direct link |

**Request/Response Examples:**
```json
// Register Request
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}

// Login Response
{
  "access_token": "jwt_token",
  "user": {
    "email": "user@example.com",
    "storage_used": 0,
    "storage_limit": 24576
  }
}
```

## File Storage API Endpoints

### File Operations Base URL
```
http://localhost:5000/api/files
```

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload` | POST | Upload single file (Max 2GB) |
| `/upload-multiple` | POST | Upload multiple files |
| `/files/{file_id}` | GET | Download file |
| `/files/{file_id}` | DELETE | Delete file |
| `/files` | GET | List all files with metadata |

**File Upload Request:**
```json
{
  "file": "<binary_data>",
  "tags": ["document", "important"],
  "storage_path": "/documents"
}
```

**File Metadata Response:**
```json
{
  "file_id": "5f9d7a2b",
  "filename": "report.pdf",
  "size": 1548921,
  "md5_hash": "a3b9c7d8e1f2g3h4i5j",
  "upload_date": "2024-03-15T09:30:00Z",
  "storage_location": "mongodb://..."
}
```

## Error Codes

| Code | Meaning | Typical Fix |
|------|---------|-------------|
| 400 | Invalid request format | Check request body |
| 401 | Missing/invalid JWT | Add Authorization header |
| 404 | Resource not found | Verify resource ID |
| 413 | Payload too large | Reduce file size |
| 500 | Server error | Retry with exponential backoff |

## Storage Implementation Details
- **MongoDB GridFS** for large file storage
- Automatic MD5 hash generation
- File versioning support
- Storage quota enforcement
- Background cleanup processes

## Rate Limits
- 100 requests/minute per IP
- 10 concurrent uploads/user
- 2GB max file size