# AI Resume Optimizer - Backend API

![Code Quality](https://github.com/ehte92/resume-match-api/workflows/Code%20Quality/badge.svg)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688)

A modern, production-ready FastAPI backend for AI-powered resume optimization. This API provides secure user authentication, database management with migrations, and comprehensive test coverage.

## Features

- 🔐 **JWT Authentication** - Secure user registration, login, and token refresh
- 📄 **Resume Management** - Upload, parse, and store PDF/DOCX resumes with R2 integration
- 🔍 **Keyword Analysis** - TF-IDF and spaCy NER for extracting keywords and calculating match scores
- ☁️ **Cloud Storage** - Cloudflare R2 integration for scalable file storage
- 🔗 **Presigned URLs** - Automatic generation of time-limited download links
- 🗄️ **PostgreSQL Database** - Robust data persistence with SQLAlchemy ORM
- 🔄 **Database Migrations** - Version-controlled schema changes with Alembic
- ✅ **Comprehensive Testing** - 91% test coverage with pytest
- 📚 **Auto-generated Documentation** - Interactive API docs with Swagger UI and ReDoc
- 🏥 **Health Checks** - Monitoring endpoints for application and database status
- 🔒 **Secure Password Hashing** - bcrypt with 12 rounds for password storage
- 🎯 **Type Safety** - Full type hints for better IDE support and code quality

## Tech Stack

- **Python 3.13.7** - Modern Python with latest features
- **FastAPI 0.116.1** - High-performance async web framework
- **PostgreSQL 14+** - Reliable relational database
- **SQLAlchemy 2.0.36** - Python SQL toolkit and ORM
- **Alembic** - Database migration tool
- **Pydantic 2.10.6** - Data validation using Python type hints
- **spaCy 3.8.7** - NLP library for named entity recognition
- **scikit-learn 1.7.2** - Machine learning library for TF-IDF vectorization
- **pytest** - Testing framework with fixtures
- **bcrypt** - Secure password hashing
- **python-jose** - JWT token implementation

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.13+** (tested with 3.13.7)
- **PostgreSQL 14+** (tested with 14.19)
- **Git**
- **pip** and **virtualenv**

## Project Structure

```
backend/
├── app/
│   ├── routers/          # API route handlers
│   │   ├── auth.py       # Authentication endpoints
│   │   ├── resume.py     # Resume management endpoints (NEW - Phase 11)
│   │   └── health.py     # Health check endpoints
│   ├── models/           # SQLAlchemy database models
│   │   ├── user.py       # User model
│   │   ├── resume.py     # Resume model (Phase 9)
│   │   └── resume_analysis.py  # Analysis model (Phase 9)
│   ├── schemas/          # Pydantic schemas for validation
│   │   ├── auth.py       # Auth request/response schemas
│   │   ├── user.py       # User schemas
│   │   ├── resume.py     # Resume schemas (Phase 9)
│   │   └── analysis.py   # Analysis schemas (Phase 9)
│   ├── services/         # Business logic layer
│   │   ├── auth_service.py
│   │   ├── resume_service.py    # Resume CRUD operations (NEW - Phase 11)
│   │   ├── resume_parser.py     # PDF/DOCX parsing (Phase 10)
│   │   ├── storage_service.py   # R2 storage operations (NEW - Phase 11)
│   │   └── keyword_analyzer.py  # Keyword extraction and matching (NEW - Phase 12)
│   ├── utils/            # Utility functions
│   │   ├── security.py   # Password hashing, JWT tokens
│   │   └── file_handler.py      # File validation and upload (Phase 10)
│   ├── config.py         # Application settings
│   ├── database.py       # Database connection and session
│   ├── dependencies.py   # FastAPI dependencies (auth)
│   └── main.py           # FastAPI application entry point
├── tests/                # Test suite
│   ├── conftest.py       # Pytest fixtures
│   ├── test_auth.py      # Authentication tests
│   ├── test_health.py    # Health check tests
│   ├── test_resume.py    # Resume management tests (Phase 11)
│   ├── test_keyword_analyzer.py  # Keyword analyzer tests (Phase 12)
│   └── fixtures/         # Test data files
├── alembic/              # Database migrations
│   └── versions/         # Migration scripts
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore rules
├── alembic.ini           # Alembic configuration
├── pytest.ini            # Pytest configuration
├── requirements.txt      # Production dependencies
├── requirements-dev.txt  # Development dependencies
└── README.md             # This file
```

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd backend
```

### 2. Create Virtual Environment

**macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (for testing)
pip install -r requirements-dev.txt
```

## Database Setup

### 1. Create PostgreSQL Database

```bash
# Using PostgreSQL command line
createdb resume_optimizer_dev

# Or using psql
psql -U postgres
CREATE DATABASE resume_optimizer_dev;
\q
```

### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

**Important:** Update the following in your `.env` file:

- `DATABASE_URL` - Your PostgreSQL connection string
- `SECRET_KEY` - Generate a secure random key for production

### 3. Run Database Migrations

```bash
# Apply all migrations
alembic upgrade head

# Verify migration was successful
alembic current
```

## Environment Variables

Configure these variables in your `.env` file:

### Database

- `DATABASE_URL` - PostgreSQL connection string
  - Format: `postgresql://user:password@host:port/database`
  - Example: `postgresql://postgres:postgres@localhost:5432/resume_optimizer_dev`

### Security

- `SECRET_KEY` - Secret key for JWT token signing (change in production!)
- `ALGORITHM` - JWT algorithm (default: `HS256`)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Access token expiration (default: `15`)
- `REFRESH_TOKEN_EXPIRE_DAYS` - Refresh token expiration (default: `7`)

### Application

- `ENVIRONMENT` - Environment name (`development`, `staging`, `production`)
- `DEBUG` - Enable debug mode (default: `true` for development)
- `CORS_ORIGINS` - Allowed CORS origins (JSON array)
  - Example: `["http://localhost:5173","http://localhost:3000"]`

### Server

- `HOST` - Server host (default: `0.0.0.0`)
- `PORT` - Server port (default: `8000`)

### File Storage (Cloudflare R2)

- `STORAGE_BACKEND` - Storage backend to use (`local` or `r2`, default: `local`)
- `R2_ACCOUNT_ID` - Cloudflare R2 account ID
- `R2_ACCESS_KEY_ID` - R2 access key ID
- `R2_SECRET_ACCESS_KEY` - R2 secret access key
- `R2_BUCKET_NAME` - R2 bucket name for resume storage
- `R2_ENDPOINT_URL` - R2 endpoint URL (e.g., `https://<account_id>.r2.cloudflarestorage.com`)
- `MAX_UPLOAD_SIZE_MB` - Maximum file upload size in MB (default: `5`)
- `ALLOWED_UPLOAD_TYPES` - Allowed file MIME types (default: `["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]`)

## Running the Server

### Development Mode (with auto-reload)

```bash
uvicorn app.main:app --reload
```

The server will start at http://localhost:8000

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Access Points

- **API Base URL:** http://localhost:8000
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Running Tests

### Run All Tests

```bash
pytest
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Coverage Report

```bash
# Terminal report
pytest --cov=app

# HTML report
pytest --cov=app --cov-report=html

# View HTML report
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

### Current Test Statistics

- **Total Tests:** 14
- **Test Coverage:** 91%
- **All Tests:** ✅ Passing

**Coverage by Module:**

- `app/schemas/auth.py`: 100%
- `app/schemas/user.py`: 100%
- `app/utils/security.py`: 97%
- `app/main.py`: 96%
- `app/models/user.py`: 94%
- `app/routers/auth.py`: 93%

## API Endpoints

### Health Checks

#### Basic Health Check

```http
GET /health
```

**Response:** `200 OK`

```json
{
  "status": "healthy"
}
```

#### Database Health Check

```http
GET /health/db
```

**Response:** `200 OK`

```json
{
  "status": "healthy",
  "database": "connected"
}
```

### Authentication

#### Register New User

```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"
}
```

**Response:** `201 Created`

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2025-10-14T12:00:00",
  "updated_at": "2025-10-14T12:00:00"
}
```

#### Login

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** `200 OK`

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe"
  }
}
```

#### Refresh Access Token

```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:** `200 OK`

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

#### Get Current User (Protected)

```http
GET /api/auth/me
Authorization: Bearer <access_token>
```

**Response:** `200 OK`

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2025-10-14T12:00:00",
  "updated_at": "2025-10-14T12:00:00"
}
```

### Resume Management

**Note:** All resume endpoints require authentication. Include the access token in the Authorization header.

#### Upload Resume

Upload a PDF or DOCX resume file. The file will be automatically parsed and stored in R2 (if configured).

```http
POST /api/resumes/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file=@resume.pdf
```

**Constraints:**
- File types: PDF (`.pdf`) or DOCX (`.docx`)
- Maximum size: 5MB
- Supported formats: `application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`

**Response:** `201 Created`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "file_name": "john_doe_resume.pdf",
  "file_type": "pdf",
  "file_size": 245780,
  "file_path": "/tmp/resume_uploads/550e8400-e29b-41d4-a716-446655440000.pdf",
  "storage_backend": "r2",
  "download_url": "https://r2.example.com/presigned/resumes/550e8400-e29b-41d4-a716-446655440001/550e8400-e29b-41d4-a716-446655440000.pdf?expires=3600",
  "parsed_text": "JOHN DOE\nSoftware Engineer\n...",
  "parsed_data": {
    "email": "john@example.com",
    "phone": "+1-555-0123",
    "linkedin": "linkedin.com/in/johndoe",
    "sections": {
      "experience": ["Senior Software Engineer at ABC Corp..."],
      "education": ["BS Computer Science, University of XYZ"],
      "skills": ["Python", "JavaScript", "AWS"]
    }
  },
  "created_at": "2025-10-15T10:30:00",
  "updated_at": null
}
```

**Error Responses:**

- `400 Bad Request` - Invalid file type or size exceeded
- `401 Unauthorized` - Missing or invalid token
- `500 Internal Server Error` - Upload or parsing failed

#### List User's Resumes

Get a paginated list of all resumes uploaded by the current user.

```http
GET /api/resumes/?page=1&page_size=10
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page` (optional) - Page number, 1-indexed (default: 1)
- `page_size` (optional) - Items per page, max 100 (default: 10)

**Response:** `200 OK`

```json
{
  "resumes": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "user_id": "550e8400-e29b-41d4-a716-446655440001",
      "file_name": "john_doe_resume.pdf",
      "file_type": "pdf",
      "file_size": 245780,
      "file_path": "/tmp/resume_uploads/550e8400-e29b-41d4-a716-446655440000.pdf",
      "storage_backend": "r2",
      "download_url": "https://r2.example.com/presigned/resumes/...",
      "parsed_text": "JOHN DOE\n...",
      "parsed_data": { "email": "john@example.com", ... },
      "created_at": "2025-10-15T10:30:00",
      "updated_at": null
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 10
}
```

#### Get Specific Resume

Retrieve details of a specific resume by ID.

```http
GET /api/resumes/{resume_id}
Authorization: Bearer <access_token>
```

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "file_name": "john_doe_resume.pdf",
  "file_type": "pdf",
  "file_size": 245780,
  "file_path": "/tmp/resume_uploads/550e8400-e29b-41d4-a716-446655440000.pdf",
  "storage_backend": "r2",
  "download_url": "https://r2.example.com/presigned/resumes/...",
  "parsed_text": "JOHN DOE\nSoftware Engineer\n...",
  "parsed_data": {
    "email": "john@example.com",
    "phone": "+1-555-0123",
    "linkedin": "linkedin.com/in/johndoe",
    "sections": {
      "experience": ["Senior Software Engineer at ABC Corp..."],
      "education": ["BS Computer Science, University of XYZ"],
      "skills": ["Python", "JavaScript", "AWS"]
    }
  },
  "created_at": "2025-10-15T10:30:00",
  "updated_at": null
}
```

**Error Responses:**

- `404 Not Found` - Resume not found
- `403 Forbidden` - User doesn't own this resume

#### Delete Resume

Delete a resume and all associated data. This also deletes related analyses and removes the file from R2.

```http
DELETE /api/resumes/{resume_id}
Authorization: Bearer <access_token>
```

**Response:** `204 No Content`

**Error Responses:**

- `404 Not Found` - Resume not found
- `403 Forbidden` - User doesn't own this resume
- `500 Internal Server Error` - Deletion failed

#### Generate Download URL

Generate a presigned URL for downloading a resume file from R2 storage (1-hour expiration).

```http
GET /api/resumes/{resume_id}/download
Authorization: Bearer <access_token>
```

**Response:** `200 OK`

```json
{
  "url": "https://r2.example.com/presigned/resumes/550e8400-e29b-41d4-a716-446655440001/550e8400-e29b-41d4-a716-446655440000.pdf?expires=3600",
  "expires_in": 3600,
  "filename": "john_doe_resume.pdf"
}
```

**Error Responses:**

- `400 Bad Request` - Resume not stored in R2 (local storage doesn't support download URLs)
- `404 Not Found` - Resume not found
- `403 Forbidden` - User doesn't own this resume

**Note:** For R2-stored resumes, the `download_url` is automatically included in resume responses (GET endpoints) with 1-hour expiration. This endpoint is for explicitly generating new URLs.

## Database Migrations

### Check Current Migration Version

```bash
alembic current
```

### View Migration History

```bash
alembic history --verbose
```

### Create New Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations

```bash
# Upgrade to latest version
alembic upgrade head

# Upgrade to specific version
alembic upgrade <revision>
```

### Rollback Migrations

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision>
```

## Code Quality

This project uses GitHub Actions for automated code quality checks.

### Automated Checks

The Code Quality workflow runs on every push and pull request to main, master, and develop branches:

- **Black Formatting:** Ensures code follows PEP 8 style guidelines
- **Flake8 Linting:** Checks code style and quality issues
- **Bandit Security:** Scans for common security vulnerabilities
- **Secret Detection:** Basic checks for hardcoded passwords and secrets

### Running Checks Locally

Before pushing code, run these checks locally:

```bash
# Check code formatting
black --check app/ tests/

# Auto-format code
black app/ tests/

# Run linter
flake8 app/ tests/

# Run security checks
bandit -r app/ -ll
```

### Configuration Files

- `.github/workflows/code-quality.yml` - Automated code quality checks
- `pyproject.toml` - Tool configurations (black, pytest, coverage)
- `.flake8` - Flake8 configuration

## Development

### Code Formatting

Format code with black:

```bash
black app/ tests/
```

### Code Quality

Check code style (if flake8 is configured):

```bash
flake8 app/ tests/
```

Type checking (if mypy is configured):

```bash
mypy app/
```

### Development Workflow

1. Create a new branch for your feature
2. Make your changes
3. Format code with black
4. Run tests: `pytest`
5. Ensure coverage stays above 80%
6. Create a pull request

## Project Status

### Completed Phases ✅

- **Phase 1:** Directory Structure
- **Phase 2:** Configuration Files
- **Phase 3:** Core Application Files
- **Phase 4:** Security & Authentication
- **Phase 5:** Database Migrations
- **Phase 6:** Testing Setup (91% coverage)
- **Phase 7:** Documentation
- **Phase 8:** Bcrypt Bug Fix (password truncation to 72 bytes)
- **Phase 9:** Resume & Analysis Database Models (NO subscription/payment features)
- **Phase 10:** Resume Parser Service (PDF/DOCX parsing with 81.62% test coverage)
- **Phase 11:** Resume Upload & Management API with R2 integration
- **Phase 12:** Keyword Analyzer Service (TF-IDF + spaCy NER with 23 passing tests)

### Current State

- ✅ Production-ready backend API
- ✅ Secure JWT authentication
- ✅ Database migrations configured
- ✅ Comprehensive test suite
- ✅ Auto-generated API documentation
- ✅ Health monitoring endpoints
- ✅ Resume and Analysis database models
- ✅ Resume parser for PDF/DOCX files
- ✅ Resume upload and management API (5 endpoints)
- ✅ Cloudflare R2 storage integration
- ✅ Presigned URL generation for secure downloads
- ✅ Keyword analysis service (TF-IDF + spaCy NER)
- ✅ Match score calculation (resume vs job description)
- ✅ 3 database tables: users, resumes, resume_analyses

### Next Steps

- **Phase 13:** ATS Checker Service - Check resume for ATS compatibility
- **Phase 14:** OpenAI Integration - Generate AI-powered suggestions
- **Phase 15:** Resume Analysis Endpoints - Complete analysis workflow

## Troubleshooting

### Database Connection Issues

If you see `connection refused` errors:

1. Ensure PostgreSQL is running: `pg_isready`
2. Check your `DATABASE_URL` in `.env`
3. Verify database exists: `psql -l`

### Migration Issues

If migrations fail:

1. Check current version: `alembic current`
2. View migration history: `alembic history`
3. Reset if needed: `alembic downgrade base` (⚠️ drops all data)

### Test Failures

If tests fail:

1. Ensure database is running
2. Check test database is clean
3. Run with verbose output: `pytest -v`
4. Check for leftover test data

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]

## Contact

[Your Contact Information Here]
