# FlyRank BE-03 Auth API

A FastAPI-based authentication system using Supabase for user management. Provides secure signup, login, logout, and protected routes with Bearer token authentication.

## Purpose

This API demonstrates a complete authentication flow with:
- User registration and login
- JWT token-based authentication
- Protected and public endpoints
- Proper error handling and validation
- Swagger UI documentation with authentication

## Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
PORT=8000
```

**Note**: Use `.env.example` as a template. Never commit real credentials to version control.

## Installation & Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your environment variables in `.env`

3. **Important**: For local development, disable email confirmation in your Supabase dashboard:
   - Go to Authentication > Settings
   - Turn off "Confirm email" to allow immediate signup without email verification

## Run Command

Start the development server:

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | `/auth/signup` | No | Register a new user |
| POST | `/auth/login` | No | Login and get access tokens |
| POST | `/auth/logout` | Yes | Logout current user |
| GET | `/public/info` | No | Get public information |
| GET | `/protected/profile` | Yes | Get current user profile |
| GET | `/protected/dashboard` | Yes | Access user dashboard |

### Authentication

Protected endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

## Testing with cURL

### 1. Sign up a new user
```bash
curl -X POST "http://localhost:8000/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

### 2. Login to get access token
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

Save the `access_token` from the response.

### 3. Access protected profile endpoint
```bash
curl -X GET "http://localhost:8000/protected/profile" \
  -H "Authorization: Bearer <your_access_token>"
```

### 4. Test public endpoint (no auth required)
```bash
curl -X GET "http://localhost:8000/public/info"
```

### 5. Logout
```bash
curl -X POST "http://localhost:8000/auth/logout" \
  -H "Authorization: Bearer <your_access_token>"
```

## Swagger UI Testing

1. Navigate to http://localhost:8000/docs
2. Click the "Authorize" button (🔒 padlock icon)
3. Enter `Bearer <your_access_token>` in the value field
4. Click "Authorize" to authenticate
5. Test protected endpoints directly from the UI

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Email and password are required"
}
```

### 401 Unauthorized
```json
{
  "error": "Invalid login credentials"
}
```

```json
{
  "detail": "Access token required"
}
```

```json
{
  "detail": "Invalid or expired token"
}
```

## Development Notes

- **Email Confirmation**: For local development, disable email confirmation in Supabase dashboard to avoid verification requirements
- **Token Validation**: All protected routes validate JWT tokens against Supabase
- **Security**: Uses HTTPBearer for consistent token handling across endpoints
- **Error Handling**: Comprehensive error responses for authentication failures

## Supabase Configuration

Make sure your Supabase project has:
1. Authentication enabled
2. Email confirmation disabled (for local testing)
3. Valid anon key configured in environment variables

## Swagger Documentation Screenshot

*[Placeholder for Swagger UI screenshot showing the authentication interface]*

## Stack

- **Python 3.10+**
- **FastAPI** - Modern web framework for building APIs
- **Supabase** - Backend-as-a-service for authentication
- **Uvicorn** - ASGI server for running FastAPI
- **Pydantic** - Data validation and serialization