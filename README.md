# AI Resume Optimizer - Backend API

![CI Pipeline](https://github.com/ehte92/resume-match-api/workflows/CI%20Pipeline/badge.svg)
![Code Quality](https://github.com/ehte92/resume-match-api/workflows/Code%20Quality/badge.svg)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688)
![Coverage](https://img.shields.io/badge/coverage-91%25-brightgreen)

A modern, production-ready FastAPI backend for AI-powered resume optimization. This API provides secure user authentication, database management with migrations, and comprehensive test coverage.

## Features

- 🔐 **JWT Authentication** - Secure user registration, login, and token refresh
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
│   │   └── health.py     # Health check endpoints
│   ├── models/           # SQLAlchemy database models
│   │   └── user.py       # User model
│   ├── schemas/          # Pydantic schemas for validation
│   │   ├── auth.py       # Auth request/response schemas
│   │   └── user.py       # User schemas
│   ├── services/         # Business logic layer
│   │   └── auth_service.py
│   ├── utils/            # Utility functions
│   │   └── security.py   # Password hashing, JWT tokens
│   ├── config.py         # Application settings
│   ├── database.py       # Database connection and session
│   ├── dependencies.py   # FastAPI dependencies (auth)
│   └── main.py           # FastAPI application entry point
├── tests/                # Test suite
│   ├── conftest.py       # Pytest fixtures
│   ├── test_auth.py      # Authentication tests
│   └── test_health.py    # Health check tests
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

## CI/CD

This project uses GitHub Actions for continuous integration and deployment.

### Automated Workflows

#### CI Pipeline

- **Triggers:** Push/PR to main, master, develop branches
- **Python Versions:** 3.11, 3.12, 3.13
- **Services:** PostgreSQL 14
- **Steps:**
  1. Checkout code
  2. Set up Python with pip caching
  3. Install dependencies
  4. Run database migrations
  5. Run pytest with coverage
  6. Enforce 80% coverage threshold
  7. Upload coverage to Codecov (optional)

#### Code Quality Checks

- **Black Formatting:** Ensures code follows PEP 8
- **Flake8 Linting:** Checks code style and quality
- **Bandit Security:** Scans for security vulnerabilities
- **Secret Detection:** Basic checks for hardcoded secrets

### Running CI Checks Locally

Before pushing code, run these checks locally:

```bash
# Run tests with coverage
pytest --cov=app --cov-report=term-missing

# Check code formatting
black --check app/ tests/

# Run linter
flake8 app/ tests/

# Run security checks
bandit -r app/ -ll
```

### Configuration Files

- `.github/workflows/ci.yml` - Main CI pipeline
- `.github/workflows/code-quality.yml` - Code quality checks
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

### Current State

- ✅ Production-ready backend API
- ✅ Secure JWT authentication
- ✅ Database migrations configured
- ✅ Comprehensive test suite
- ✅ Auto-generated API documentation
- ✅ Health monitoring endpoints

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
