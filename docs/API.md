# Make My Resume API Documentation

This document describes the backend endpoints used by the mobile application and the expected request/response shapes.

## Authentication
All profile-related routes require a bearer token from Supabase auth.

Headers:
- Authorization: Bearer <access_token>

## Base URL
- Local: http://localhost:8000
- Render: https://<your-render-app>.onrender.com

## Health
### GET /
Returns a simple liveness response.

Response:
```json
{"status": "the service is running"}
```

### GET /health
Returns a simple health response.

Response:
```json
{"status": "ok"}
```

## Auth
### POST /auth/register
Creates a new Supabase auth user.

Request body:
```json
{
  "username": "string",
  "email": "user@example.com",
  "password": "string"
}
```

Success response:
```json
{
  "user_uuid": "uuid",
  "username": "string",
  "email": "user@example.com"
}
```

Errors:
- 400: registration failed or Supabase rejected the request
- 401: invalid credentials (for login)

### POST /auth/login
Logs in and returns an access token.

Request body:
```json
{
  "email": "user@example.com",
  "password": "string"
}
```

Success response:
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "user": {
    "user_uuid": "uuid",
    "username": "string",
    "email": "user@example.com"
  }
}
```

## Profile Endpoints
### GET /user-details/
Returns the authenticated user's profile summary.

Success response:
```json
{}
```

### POST /user-details/upsert
Creates or updates the profile record for the authenticated user.

Request body:
```json
{
  "name": "string",
  "mobile_number": "string",
  "email_id": "string",
  "github_url": "string",
  "linkedin_url": "string",
  "portfolio_link": "string",
  "location": "string",
  "profession_summary": "string"
}
```

Success response:
```json
{
  "message": "user details saved successfully",
  "data": []
}
```

Errors:
- 400: Supabase returned an error

## Project Endpoints
### GET /projects/
Returns all projects for the authenticated user.

Response:
```json
{
  "projects": []
}
```

### POST /projects/add-project
Adds a new project.

Request body:
```json
{
  "name": "string",
  "description": "string",
  "tech_stack": "string",
  "github_url": "string",
  "live_link": "string"
}
```

## Skills Endpoints
### GET /skills/
Returns all skills for the authenticated user.

## Education Endpoints
### GET /education/
Returns all education records for the authenticated user.

## Internship Endpoints
### GET /internship/
Returns all internship records for the authenticated user.

## Certificate Endpoints
### GET /certificates/
Returns all certificates for the authenticated user.

## Achievement Endpoints
### GET /achievement/
Returns all achievements for the authenticated user.

## AI Endpoint
### POST /ai/ask
Answers questions about the authenticated user's profile.

Request body:
```json
{
  "question": "What projects has this user built?"
}
```

Success response:
```json
{
  "answer": "string",
  "sources": [
    {
      "source_table": "projects",
      "source_id": 1
    }
  ]
}
```

Errors:
- 404: no profile data was found for the current user
- 500: missing GROQ_API_KEY
- 502: the AI service failed to respond

## AI History
### GET /ai/history
Returns the authenticated user's recent AI question/answer pairs, most recent first.

Query params:
- limit: number of items to return (default 20, max 100)
- offset: number of items to skip (default 0)

Success response:
```json
{
  "items": [
    {
      "id": 1,
      "question": "What projects has this user built?",
      "answer": "The user built a portfolio app.",
      "sources": [
        {
          "source_table": "projects",
          "source_id": 1
        }
      ],
      "created_at": "2026-07-30T00:00:00Z"
    }
  ],
  "limit": 20,
  "offset": 0
}
```

Errors:
- 401: invalid or missing bearer token

## Resume Endpoint
### POST /resume/generate
Starts resume generation for a job description.

Request body:
```json
{
  "job_description": "Senior Python backend engineer"
}
```

Success response:
```json
{
  "job_id": "uuid",
  "status": "queued",
  "message": "Resume generation completed"
}
```

### GET /resume/generate/{job_id}
Checks the resume generation status.

Success response:
```json
{
  "job_id": "uuid",
  "status": "completed",
  "download_url": "/resume/generate/uuid/download",
  "error": null
}
```

### POST /resume/generate/{job_id}/download
Downloads the generated DOCX resume.

Errors:
- 404: job not found
- 409: resume generation is not complete yet

## Resume History
### GET /resume/history
Returns the authenticated user's recent resume generation jobs, most recent first.

Query params:
- limit: number of items to return (default 20, max 100)
- offset: number of items to skip (default 0)

Success response:
```json
{
  "items": [
    {
      "id": 1,
      "job_id": "uuid",
      "status": "completed",
      "job_description": "Senior Python backend engineer",
      "created_at": "2026-07-30T00:00:00Z",
      "download_url": "/resume/generate/uuid/download"
    }
  ],
  "limit": 20,
  "offset": 0
}
```

Errors:
- 401: invalid or missing bearer token

## Document Embeddings
### POST /document-embeddings/
Stores a document embedding chunk for the current user.

Request body:
```json
{
  "source_table": "projects",
  "source_id": 1,
  "content": "text chunk",
  "embedding": [0.1, 0.2]
}
```

Success response:
```json
{
  "id": 1,
  "user_uuid": "uuid",
  "source_table": "projects",
  "source_id": 1,
  "content": "text chunk",
  "embedding": []
}
```
