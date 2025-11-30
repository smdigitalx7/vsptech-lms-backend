import json
import os
from enum import Enum
from typing import Any, Set
from pydantic import SecretStr, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ============================================================================
# Application Constants (non-configurable values)
# ============================================================================
# Time Conversion Constants
SECONDS_PER_MINUTE = 60
MILLISECONDS_PER_SECOND = 1000

# Database Constants
DB_HEALTH_CHECK_QUERY = "SELECT 1"
DB_HEALTH_CHECK_RETRY_ATTEMPTS = 3
DB_HEALTH_CHECK_RETRY_DELAY_SECONDS = 1

# Health Check Constants
HEALTH_CPU_THRESHOLD_PERCENT = 80
HEALTH_MEMORY_THRESHOLD_PERCENT = 80
HEALTH_DISK_THRESHOLD_PERCENT = 80
HEALTH_CPU_INTERVAL_SECONDS = 0.1
BYTES_PER_GB = 1024 ** 3

# Worker Constants
WORKER_MAX_JOBS = 10
WORKER_JOB_TIMEOUT_SECONDS = 300

# Security Constants
ARGON2_HASH_PREFIX = "$argon2id$"
SECRET_KEY_MIN_LENGTH = 32

# String Length Constants
MAX_EMAIL_LENGTH = 255
MAX_PASSWORD_HASH_LENGTH = 255
MAX_FULL_NAME_LENGTH = 255

# API Defaults
DEFAULT_PAGE_SIZE = 100
DEFAULT_PAGE_NUMBER = 1

# Thread Pool Constants
DEFAULT_THREAD_POOL_TOKENS = 100


class EnvironmentOption(Enum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Centralized application settings using modern pydantic-settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @classmethod
    def get_env_file_priority(cls) -> list[str]:
        """Get environment file priority based on current environment."""
        env = os.getenv("ENVIRONMENT", "local").lower()

        if env == "production":
            return [".env.production", ".env"]
        elif env == "staging":
            return [".env.staging", ".env.production", ".env"]
        else:  # local or development
            return [".env.local", ".env.development", ".env"]

    @classmethod
    def create_with_env_file(cls, env_file: str | None = None):
        """Create settings instance with specific environment file."""
        if env_file:
            env_files = [env_file, ".env"]
        else:
            env_files = cls.get_env_file_priority()

        config = SettingsConfigDict(
            env_file=env_files,
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore"
        )

        class SettingsWithEnv(cls):
            model_config = config

        return SettingsWithEnv()  # type: ignore[call-arg]

    # Application Settings
    app_name: str = Field(..., description="Application name")
    app_description: str | None = Field(default=None, description="Application description")
    app_version: str | None = Field(default=None, description="Application version")
    debug: bool = Field(..., description="Debug mode")

    # Security Settings
    secret_key: SecretStr = Field(..., min_length=32, description="Secret key for JWT tokens")
    algorithm: str = Field(..., description="JWT algorithm")
    access_token_expire_minutes: int = Field(..., ge=1, le=1440, description="Access token expiration in minutes")
    refresh_token_expire_days: int = Field(..., ge=1, le=30, description="Refresh token expiration in days")

    # Argon2id Password Hashing Settings
    argon2_time_cost: int = Field(..., ge=1, le=10, description="Argon2id time cost (iterations)")
    argon2_memory_cost: int = Field(..., ge=1024, le=1048576, description="Argon2id memory cost in KB")
    argon2_parallelism: int = Field(..., ge=1, le=16, description="Argon2id parallelism (number of threads)")
    argon2_hash_len: int = Field(..., ge=16, le=64, description="Argon2id hash length in bytes")
    argon2_salt_len: int = Field(..., ge=8, le=32, description="Argon2id salt length in bytes")

    # Database Settings
    database_url: str | None = Field(default=None, description="Database URL")

    # PostgreSQL Settings (fallback if database_url not provided)
    postgres_user: str = Field(..., description="PostgreSQL username")
    postgres_password: str = Field(..., description="PostgreSQL password")
    postgres_server: str = Field(..., description="PostgreSQL server")
    postgres_port: int = Field(..., ge=1, le=65535, description="PostgreSQL port")
    postgres_db: str = Field(..., description="PostgreSQL database name")

    # Redis Settings
    redis_url: str | None = Field(default=None, description="Redis URL")
    redis_cache_host: str = Field(..., description="Redis cache host")
    redis_cache_port: int = Field(..., ge=1, le=65535, description="Redis cache port")
    redis_queue_host: str = Field(..., description="Redis queue host")
    redis_queue_port: int = Field(..., ge=1, le=65535, description="Redis queue port")
    redis_rate_limit_host: str = Field(..., description="Redis rate limit host")
    redis_rate_limit_port: int = Field(..., ge=1, le=65535, description="Redis rate limit port")

    # Cache Settings
    client_cache_max_age: int = Field(..., ge=1, le=86400, description="Client cache max age in seconds")

    # Rate Limiting
    default_rate_limit_limit: int = Field(..., ge=1, le=10000, description="Default rate limit")
    default_rate_limit_period: int = Field(..., ge=1, le=86400, description="Rate limit period in seconds")

    # Database Connection Pool
    db_pool_size: int = Field(..., ge=5, le=100, description="Database connection pool size")
    db_max_overflow: int = Field(..., ge=5, le=100, description="Database max overflow connections")
    db_pool_timeout: int = Field(..., ge=5, le=300, description="Database pool timeout in seconds")
    db_pool_recycle: int = Field(..., ge=300, le=7200, description="Database pool recycle time in seconds")

    # API Configuration
    default_page_size: int = Field(..., ge=1, le=100, description="Default page size for pagination")
    max_page_size: int = Field(..., ge=10, le=1000, description="Maximum page size for pagination")
    default_page: int = Field(..., description="Default page number")

    # Thread Pool Configuration
    thread_pool_tokens: int = Field(..., ge=10, le=1000, description="Number of thread pool tokens")

    # Gunicorn Configuration
    gunicorn_workers: int = Field(..., ge=1, le=32, description="Number of Gunicorn worker processes")
    gunicorn_threads: int = Field(..., ge=1, le=8, description="Number of threads per worker")
    gunicorn_timeout: int = Field(..., ge=30, le=300, description="Worker timeout in seconds")
    gunicorn_graceful_timeout: int = Field(..., ge=10, le=120, description="Graceful shutdown timeout in seconds")
    gunicorn_keep_alive: int = Field(..., ge=2, le=30, description="Keep-alive connections timeout in seconds")
    gunicorn_max_requests: int = Field(..., ge=100, le=10000, description="Max requests before worker restart")
    gunicorn_max_requests_jitter: int = Field(..., ge=0, le=100, description="Jitter for max requests to prevent thundering herd")

    # Logging Configuration
    log_level: str = Field(..., description="Logging level")
    log_format: str = Field(..., description="Log format (json, text)")
    log_file_max_size: int = Field(..., ge=1048576, le=104857600, description="Maximum log file size in bytes")
    log_file_backup_count: int = Field(..., ge=1, le=20, description="Number of backup log files")
    log_retention_days: int = Field(..., ge=1, le=365, description="Log retention period in days")

    # CORS Settings
    cors_origins: str = Field(
        ...,
        description="Comma-separated list of allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(..., description="Allow credentials in CORS")
    cors_max_age: int = Field(..., ge=0, le=86400, description="CORS preflight cache max age in seconds")
    cors_allow_headers: str = Field(
        ...,
        description="Comma-separated list of allowed CORS headers"
    )
    cors_expose_headers: str = Field(
        ...,
        description="Comma-separated list of exposed CORS headers"
    )
    cors_allow_methods: str = Field(
        ...,
        description="Comma-separated list of allowed CORS methods"
    )

    # Environment
    environment: EnvironmentOption = Field(..., description="Environment")

    # File Upload Settings
    max_file_size: int = Field(..., ge=1024, le=104857600, description="Maximum file upload size in bytes")
    allowed_file_types: str = Field(
        ...,
        description="Comma-separated list of allowed file types"
    )

    # Security Headers Settings
    security_headers_enabled: bool = Field(..., description="Enable security headers")
    content_security_policy: str = Field(
        ...,
        description="Content-Security-Policy header value"
    )
    x_frame_options: str = Field(..., description="X-Frame-Options header value")
    x_content_type_options: str = Field(..., description="X-Content-Type-Options header value")
    referrer_policy: str = Field(
        ...,
        description="Referrer-Policy header value"
    )

    # Core Threshold
    core_threshold: int = Field(..., ge=0, description="Core threshold value")

    # Authentication paths (can be JSON string or comma-separated string)
    skip_auth_paths: Set[str] = Field(
        default={"/health", "/docs", "/redoc", "/openapi.json", "/api/v1/public/auth/login", "/api/v1/public/auth/refresh", "/api/v1/public/auth/register", "/api/v1/public/auth/forgot-password", "/api/v1/public/auth/reset-password", "/api/v1/public/auth/verify-otp", "/api/v1/public/auth/resend-otp"},
        description="Paths that skip authentication (can be JSON array string or comma-separated)"
    )
    refresh_paths: Set[str] = Field(
        default={"/api/v1/public/auth/refresh"},
        description="Paths that require refresh token (can be JSON array string or comma-separated)"
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == EnvironmentOption.PRODUCTION

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == EnvironmentOption.LOCAL

    @property
    def postgres_url(self) -> str:
        """Get PostgreSQL URL."""
        if self.database_url:
            return self.database_url

        from urllib.parse import quote_plus
        encoded_password = quote_plus(self.postgres_password)

        return f"postgresql+asyncpg://{self.postgres_user}:{encoded_password}@{self.postgres_server}:{self.postgres_port}/{self.postgres_db}"

    @property
    def redis_cache_url(self) -> str:
        """Get Redis cache URL."""
        if self.redis_url:
            return self.redis_url
        return f"redis://{self.redis_cache_host}:{self.redis_cache_port}"

    @property
    def redis_queue_url(self) -> str:
        """Get Redis queue URL."""
        return f"redis://{self.redis_queue_host}:{self.redis_queue_port}"

    @property
    def redis_rate_limit_url(self) -> str:
        """Get Redis rate limit URL."""
        return f"redis://{self.redis_rate_limit_host}:{self.redis_rate_limit_port}"

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        if self.is_production:
            return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        else:
            return ["*"]

    @property
    def cors_allow_headers_list(self) -> list[str]:
        """Get CORS allow headers as a list."""
        return [header.strip() for header in self.cors_allow_headers.split(",") if header.strip()]

    @property
    def cors_expose_headers_list(self) -> list[str]:
        """Get CORS expose headers as a list."""
        return [header.strip() for header in self.cors_expose_headers.split(",") if header.strip()]

    @property
    def cors_allow_methods_list(self) -> list[str]:
        """Get CORS allow methods as a list."""
        return [method.strip() for method in self.cors_allow_methods.split(",") if method.strip()]

    @property
    def allowed_file_types_list(self) -> list[str]:
        """Get allowed file types as a list."""
        return [file_type.strip().lower() for file_type in self.allowed_file_types.split(",") if file_type.strip()]

    @field_validator("skip_auth_paths", mode="before")
    @classmethod
    def parse_skip_auth_paths(cls, v: Any) -> Set[str]:
        """Parse skip_auth_paths from JSON string, comma-separated string, or set/list."""
        if isinstance(v, set):
            return {str(item) for item in v}  # type: ignore[arg-type]
        if isinstance(v, list):
            return {str(item) for item in v}  # type: ignore[arg-type]
        if isinstance(v, str):
            # Try to parse as JSON first
            try:
                parsed: Any = json.loads(v)
                if isinstance(parsed, list):
                    return {str(item) for item in parsed}  # type: ignore[arg-type]
            except (json.JSONDecodeError, ValueError):
                pass
            # Fall back to comma-separated string
            return {path.strip() for path in v.split(",") if path.strip()}
        return set()

    @field_validator("refresh_paths", mode="before")
    @classmethod
    def parse_refresh_paths(cls, v: Any) -> Set[str]:
        """Parse refresh_paths from JSON string, comma-separated string, or set/list."""
        if isinstance(v, set):
            return {str(item) for item in v}  # type: ignore[arg-type]
        if isinstance(v, list):
            return {str(item) for item in v}  # type: ignore[arg-type]
        if isinstance(v, str):
            # Try to parse as JSON first
            try:
                parsed: Any = json.loads(v)
                if isinstance(parsed, list):
                    return {str(item) for item in parsed}  # type: ignore[arg-type]
            except (json.JSONDecodeError, ValueError):
                pass
            # Fall back to comma-separated string
            return {path.strip() for path in v.split(",") if path.strip()}
        return set()

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: SecretStr) -> SecretStr:
        """Validate secret key strength."""
        if len(v.get_secret_value()) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> EnvironmentOption:
        """Validate environment value."""
        if not isinstance(v, EnvironmentOption):
            try:
                return EnvironmentOption(v.lower())
            except ValueError:
                raise ValueError(f"Invalid environment: {v}. Must be one of: {[e.value for e in EnvironmentOption]}")
        return v


# Create settings instance with dynamic environment file loading
settings = Settings.create_with_env_file()

