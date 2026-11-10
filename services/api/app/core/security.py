from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
import time
from typing import Any, Deque, Dict, Optional, Set
import uuid
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

from app.core.config import settings

# Initialize Argon2 Password Hasher with safe parameters
ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16
)

# In-memory token revocation registry (for logged-out / deleted-account JWTs)
_REVOKED_TOKEN_JTIS: Set[str] = set()

# Sliding-window authentication rate limiter storage: key -> deque of timestamps
_AUTH_ATTEMPT_BUCKETS: Dict[str, Deque[float]] = defaultdict(deque)


def get_password_hash(password: str) -> str:
    """Hashes a plain-text password using Argon2id."""
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against an Argon2id hash."""
    try:
        return ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed JWT access token with a unique JTI for revocation support."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": str(subject),
        "jti": uuid.uuid4().hex,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "iss": "ai-fitness-coach"
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a JWT access token, rejecting expired, tampered, or revoked tokens."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer="ai-fitness-coach"
        )
        jti = payload.get("jti")
        if jti and jti in _REVOKED_TOKEN_JTIS:
            return None
        return payload
    except jwt.PyJWTError:
        return None


def revoke_access_token(token: Optional[str]) -> None:
    """Revokes a JWT token's JTI so subsequent Bearer or cookie requests are rejected."""
    if not token:
        return
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer="ai-fitness-coach",
            options={"verify_exp": False},
        )
        jti = payload.get("jti")
        if jti:
            _REVOKED_TOKEN_JTIS.add(str(jti))
    except jwt.PyJWTError:
        pass


def check_auth_rate_limit(client_key: str) -> bool:
    """Returns True if within rate limit, or False if brute-force threshold is exceeded."""
    now = time.monotonic()
    window = float(settings.AUTH_RATE_LIMIT_WINDOW_SECONDS)
    max_attempts = int(settings.AUTH_RATE_LIMIT_MAX_ATTEMPTS)
    bucket = _AUTH_ATTEMPT_BUCKETS[client_key]

    while bucket and (now - bucket[0]) > window:
        bucket.popleft()

    if len(bucket) >= max_attempts:
        return False

    bucket.append(now)
    return True


def reset_auth_rate_limits() -> None:
    """Clears rate limit buckets (used in test fixtures)."""
    _AUTH_ATTEMPT_BUCKETS.clear()
