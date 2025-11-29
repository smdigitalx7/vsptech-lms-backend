# vsptech-lms-backend

# FastAPI Docker Template

A production-ready FastAPI boilerplate template with Docker support, PostgreSQL, Redis, and comprehensive testing infrastructure.

## Features

- **FastAPI** - Modern, fast web framework for building APIs
- **Docker & Docker Compose** - Containerized development and production environments
- **PostgreSQL** - Async SQLAlchemy with Alembic migrations
- **Redis** - Caching and background job queue (ARQ)
- **JWT Authentication** - Secure token-based authentication with refresh tokens
- **Argon2id Password Hashing** - Industry-standard password security
- **Structured Logging** - JSON-formatted logs with rotation
- **Comprehensive Testing** - Pytest with async support and fixtures
- **Health Checks** - Liveness and readiness probes for Kubernetes/Docker
- **Type Safety** - Full type hints with mypy support
- **Code Quality** - Ruff for linting and formatting

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.13+ (for local development)
- uv package manager (optional, recommended)

### 1. Clone and Setup

```bash
# Copy the template to your project directory
cp -r FastAPI-Docker-Template my-new-project
cd my-new-project

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 2. Start Services

```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f web

# Check service status
docker-compose ps
```

### 3. Run Database Migrations

```bash
# Create initial migration
docker-compose exec web alembic revision --autogenerate -m "Initial migration"

# Apply migrations
docker-compose exec web alembic upgrade head
```

### 4. Access the API

- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health/ready

## Project Structure

```
.
├── src/
│   ├── app/
│   │   ├── api/              # API routes
│   │   │   ├── v1/          # API version 1
│   │   │   │   ├── auth.py  # Authentication endpoints
│   │   │   │   └── users.py # User CRUD endpoints
│   │   │   └── health.py    # Health check endpoints
│   │   ├── core/            # Core application logic
│   │   │   ├── config.py    # Configuration management
│   │   │   ├── database.py  # Database connection
│   │   │   ├── security.py  # Password hashing, JWT
│   │   │   ├── logger.py    # Logging configuration
│   │   │   ├── setup.py     # Application factory
│   │   │   ├── utils/       # Utility modules
│   │   │   └── worker/      # Background job workers
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   ├── middleware/       # Custom middleware
│   │   └── main.py          # Application entry point
│   ├── migrations/           # Alembic migrations
│   └── tests/               # Test suite
├── docker-compose.yml        # Development environment
├── docker-compose.production.yml  # Production environment
├── Dockerfile                # Development Dockerfile
├── Dockerfile.production     # Production Dockerfile
├── pyproject.toml           # Project dependencies
└── alembic.ini              # Alembic configuration
```

## Development Workflow

### Running Locally (without Docker)

```bash
# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run database migrations
alembic upgrade head

# Start development server
uvicorn src.app.main:app --reload
```

### Running Tests

```bash
# Run all tests
docker-compose exec web pytest src/tests/ -v

# Run specific test file
docker-compose exec web pytest src/tests/test_auth.py -v

# Run with coverage
docker-compose exec web pytest src/tests/ --cov=src/app --cov-report=html
```

### Database Migrations

```bash
# Create a new migration
docker-compose exec web alembic revision --autogenerate -m "Description"

# Apply migrations
docker-compose exec web alembic upgrade head

# Rollback one migration
docker-compose exec web alembic downgrade -1

# View migration history
docker-compose exec web alembic history
```

### Background Jobs

The template includes ARQ for background job processing:

```bash
# Start worker (in separate terminal or via docker-compose)
docker-compose up worker

# Or run locally
arq src.app.core.worker.settings.WorkerSettings
```

## API Documentation

### Authentication

#### Register User

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"
}
```

#### Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

#### Refresh Token

```http
POST /api/v1/auth/refresh
Cookie: refreshToken=<refresh_token>
```

#### Logout

```http
POST /api/v1/auth/logout
Cookie: refreshToken=<refresh_token>
```

### Users

#### Create User

```http
POST /api/v1/users
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "email": "newuser@example.com",
  "password": "securepassword123",
  "full_name": "Jane Doe"
}
```

#### List Users

```http
GET /api/v1/users?skip=0&limit=100
Authorization: Bearer <access_token>
```

#### Get User

```http
GET /api/v1/users/{user_id}
Authorization: Bearer <access_token>
```

#### Update User

```http
PUT /api/v1/users/{user_id}
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "full_name": "Updated Name"
}
```

#### Delete User

```http
DELETE /api/v1/users/{user_id}
Authorization: Bearer <access_token>
```

### Health Checks

#### Liveness Probe

```http
GET /api/v1/health/live
```

#### Readiness Probe

```http
GET /api/v1/health/ready
```

#### Comprehensive Health Check

```http
GET /api/v1/health/full
```

## Production Deployment

### Using Docker Compose

```bash
# Build production images
docker-compose -f docker-compose.production.yml build

# Start production services
docker-compose -f docker-compose.production.yml up -d

# View logs
docker-compose -f docker-compose.production.yml logs -f
```

### Environment Variables

For production, create a `.env.production` file with production values:

```bash
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<strong-random-secret-key>
DATABASE_URL=<production-database-url>
REDIS_URL=<production-redis-url>
# ... other production settings
```

### Security Checklist

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Set `DEBUG=false` in production
- [ ] Use strong database passwords
- [ ] Configure CORS origins properly
- [ ] Enable HTTPS/TLS
- [ ] Set up proper firewall rules
- [ ] Configure log rotation and retention
- [ ] Set up monitoring and alerting
- [ ] Review and update dependencies regularly

## Configuration

### Environment Variables

See `.env.example` for all available configuration options. Key settings:

- **Database**: Configure PostgreSQL connection
- **Redis**: Configure Redis for caching and queues
- **Security**: JWT secret key, token expiration times
- **CORS**: Configure allowed origins and methods
- **Logging**: Log level, format, rotation settings

### Application Settings

Settings are managed via Pydantic Settings in `src/app/core/config.py`. The application automatically loads environment variables and supports multiple environment files (`.env.local`, `.env.staging`, `.env.production`).

## Testing

The template includes comprehensive test infrastructure:

- **Pytest** with async support
- **Test fixtures** for database, Redis, and FastAPI app
- **Example tests** for authentication and CRUD operations
- **Coverage reporting** support

Run tests:

```bash
pytest src/tests/ -v
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

This template is provided under the MIT License. See [LICENSE](LICENSE) for details.

## Support

For issues, questions, or contributions, please open an issue on the repository.

## Acknowledgments

This template is based on best practices for FastAPI applications and includes:

- FastAPI framework
- SQLAlchemy async ORM
- Alembic for database migrations
- ARQ for background jobs
- Pydantic for data validation
- Docker for containerization
