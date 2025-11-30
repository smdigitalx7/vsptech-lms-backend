from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, HashingError
from app.core.config import settings, ARGON2_HASH_PREFIX
from app.core.logger import get_app_logger
from app.schemas.auth import AccessTokenDetails, RefreshTokenDetails

logger = get_app_logger(__name__)


def _get_argon2_hasher() -> PasswordHasher:
    """Get Argon2id password hasher with configuration from settings.

    Returns
    -------
    PasswordHasher
        Configured Argon2id password hasher instance.
    """
    return PasswordHasher(
        time_cost=settings.argon2_time_cost,
        memory_cost=settings.argon2_memory_cost,
        parallelism=settings.argon2_parallelism,
        hash_len=settings.argon2_hash_len,
        salt_len=settings.argon2_salt_len
    )


def _get_argon2_verifier() -> PasswordHasher:
    """Get Argon2id password verifier (can verify hashes with any parameters).
    
    Note: Argon2 verify() reads parameters from the hash itself, so we can use
    a default PasswordHasher for verification even if the hash was created with
    different parameters. Using default parameters ensures maximum compatibility.
    
    Returns
    -------
    PasswordHasher
        PasswordHasher instance for verification (parameters don't matter for verify).
    """
    # For verification, parameters don't matter - Argon2 reads them from the hash
    # Using default PasswordHasher() ensures it can verify hashes created with
    # any valid Argon2 parameters
    return PasswordHasher()


# Initialize Argon2id password hasher with configuration from settings
_argon2_hasher = _get_argon2_hasher()
_argon2_verifier = _get_argon2_verifier()


def _is_argon2id_hash(hashed_password: str) -> bool:
    """Check if the hash is an Argon2id hash."""
    if not hashed_password:
        return False
    return hashed_password.strip().startswith(ARGON2_HASH_PREFIX)


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its Argon2id hash.

    Parameters
    ----------
    plain_password : str
        The plain text password to verify.
    hashed_password : str
        The Argon2id hashed password to compare against.

    Returns
    -------
    bool
        True if password matches, False otherwise.
    """
    if not plain_password or not hashed_password:
        logger.warning("Password verification failed: empty password or hash")
        return False

    # Strip whitespace from hash (in case of database storage issues)
    hashed_password = hashed_password.strip()

    # Check if it's an Argon2id hash
    if not _is_argon2id_hash(hashed_password):
        logger.warning(
            f"Password hash format not recognized. "
            f"Expected Argon2id hash starting with '{ARGON2_HASH_PREFIX}'"
        )
        return False

    try:
        # Verify Argon2id hash (synchronous call, but function is async for consistency)
        # Note: verify() reads parameters from the hash itself, so it works with hashes
        # created with different parameters than the current settings
        _argon2_verifier.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        # Password doesn't match - this is expected for wrong passwords
        return False
    except Exception as e:
        # Log unexpected errors for debugging
        logger.error(f"Password verification error: {type(e).__name__}: {e}", exc_info=True)
        return False


async def hash_password(password: str) -> str:
    """Hash a password using Argon2id.

    Parameters
    ----------
    password : str
        The plain text password to hash.

    Returns
    -------
    str
        The Argon2id hashed password.
    """
    if not password:
        raise ValueError("Password cannot be empty")

    try:
        return _argon2_hasher.hash(password)
    except HashingError as e:
        raise ValueError(f"Password hashing failed: {e}") from e


async def create_access_token(data: AccessTokenDetails, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with custom claims."""
    to_encode = data.model_dump()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire, "token_type": "access"})
    secret_key: str = settings.secret_key.get_secret_value()
    return jwt.encode(to_encode, secret_key, algorithm=settings.algorithm)  # type: ignore[arg-type]


async def create_refresh_token(data: RefreshTokenDetails, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token with custom claims."""
    to_encode = data.model_dump()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=settings.refresh_token_expire_days))
    to_encode.update({"exp": expire, "token_type": "refresh"})
    secret_key: str = settings.secret_key.get_secret_value()
    return jwt.encode(to_encode, secret_key, algorithm=settings.algorithm)  # type: ignore[arg-type]


def decode_token(token: str) -> dict[str, Any]:
    """Decode a JWT token.

    Parameters
    ----------
    token : str
        The JWT token to decode.

    Returns
    -------
    dict
        The decoded token payload.

    Raises
    ------
    jwt.InvalidTokenError
        If the token is invalid or expired.
    """
    secret_key: str = settings.secret_key.get_secret_value()
    return jwt.decode(token, secret_key, algorithms=[settings.algorithm])  # type: ignore[arg-type]

