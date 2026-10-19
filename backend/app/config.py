"""
Application configuration loaded from environment variables with validation.

Uses a Pydantic-free settings class to avoid extra dependencies while still
providing startup validation. All validation happens at import time so
misconfiguration fails fast.
"""
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _normalize_database_url(url: str) -> str:
    """Normalize a database URL for SQLAlchemy async drivers.

    Render provides postgresql:// URLs, but SQLAlchemy's asyncpg dialect
    requires postgresql+asyncpg://. This normalizes postgres:// and
    postgresql:// to postgresql+asyncpg:// without double-prefixing or
    corrupting URLs that are already correct. SQLite and other dialects
    pass through unchanged. Database credentials are not logged.

    Supabase connection strings often include query parameters such as
    ?sslmode=require or ?options=... . This function preserves any existing
    query string rather than blindly appending parameters, which could
    otherwise produce malformed URLs.
    """
    if not url:
        return url
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://"):]
    if url.startswith("postgresql://") and not url.startswith("postgresql+"):
        return "postgresql+asyncpg://" + url[len("postgresql://"):]
    # postgresql+asyncpg:// and all other dialects pass through unchanged
    return url


class ConfigError(Exception):
    """Raised when configuration is invalid."""


class Settings:
    # App
    APP_NAME: str = "ATS Resume Score Checker"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"  # development, staging, production
    PORT: int = 8000  # Antideploy injects PORT at runtime

    # Database
    DATABASE_URL: str = ""

    # Security
    JWT_SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = False

    # Email verification / password reset
    EMAIL_VERIFICATION_EXPIRE_MINUTES: int = 30
    PASSWORD_RESET_EXPIRE_MINUTES: int = 60

    # Email delivery (Resend)
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "noreply@yourapp.com"
    FRONTEND_URL: str = "http://localhost:5173"

    # File handling
    UPLOAD_DIR: Path
    MAX_FILE_SIZE_MB: int = 10

    # CORS
    ALLOWED_ORIGINS: list[str] = []

    # NLP
    SENTENCE_TRANSFORMER_MODEL: str = "all-MiniLM-L6-v2"
    SPACY_MODEL: str = "en_core_web_sm"

    # Scoring weights
    SCORING_WEIGHTS: dict[str, float] = {}

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: int = 60  # requests per window per client
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_AUTH: int = 10  # stricter for auth endpoints
    RATE_LIMIT_ANALYSIS: int = 20  # stricter for expensive analysis

    # Logging
    LOG_LEVEL: str = "INFO"

    # Report
    REPORT_DIR: Path

    def __init__(self):
        self._load()
        self._validate()

    def _load(self):
        self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "production").lower()
        self.PORT = int(os.getenv("PORT", "8000"))

        self.DATABASE_URL = _normalize_database_url(os.getenv("DATABASE_URL", ""))
        if not self.DATABASE_URL:
            # Safe dev fallback only — production must set DATABASE_URL explicitly
            if self.ENVIRONMENT == "production":
                raise ConfigError(
                    "DATABASE_URL must be set in production. "
                    "Refusing to start with a default database URL."
                )
            self.DATABASE_URL = "sqlite+aiosqlite:///./ats_resume_checker.db"

        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
        self.PASSWORD_MIN_LENGTH = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
        self.PASSWORD_REQUIRE_UPPERCASE = os.getenv("PASSWORD_REQUIRE_UPPERCASE", "true").lower() == "true"
        self.PASSWORD_REQUIRE_LOWERCASE = os.getenv("PASSWORD_REQUIRE_LOWERCASE", "true").lower() == "true"
        self.PASSWORD_REQUIRE_DIGIT = os.getenv("PASSWORD_REQUIRE_DIGIT", "true").lower() == "true"
        self.PASSWORD_REQUIRE_SPECIAL = os.getenv("PASSWORD_REQUIRE_SPECIAL", "false").lower() == "true"

        self.EMAIL_VERIFICATION_EXPIRE_MINUTES = int(os.getenv("EMAIL_VERIFICATION_EXPIRE_MINUTES", "30"))
        self.PASSWORD_RESET_EXPIRE_MINUTES = int(os.getenv("PASSWORD_RESET_EXPIRE_MINUTES", "60"))

        self.RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
        self.EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@yourapp.com")
        self.FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

        self.UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads")))
        self.MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))

        origins = os.getenv("ALLOWED_ORIGINS", "")
        self.ALLOWED_ORIGINS = [o.strip() for o in origins.split(",") if o.strip()]
        if not self.ALLOWED_ORIGINS:
            if self.ENVIRONMENT == "production":
                raise ConfigError(
                    "ALLOWED_ORIGINS must be set in production. "
                    "Refusing to start with permissive CORS."
                )
            self.ALLOWED_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]

        self.SENTENCE_TRANSFORMER_MODEL = os.getenv(
            "SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2"
        )
        self.SPACY_MODEL = os.getenv("SPACY_MODEL", "en_core_web_sm")

        self.RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        self.RATE_LIMIT_DEFAULT = int(os.getenv("RATE_LIMIT_DEFAULT", "60"))
        self.RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
        self.RATE_LIMIT_AUTH = int(os.getenv("RATE_LIMIT_AUTH", "10"))
        self.RATE_LIMIT_ANALYSIS = int(os.getenv("RATE_LIMIT_ANALYSIS", "20"))

        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
        self.REPORT_DIR = Path(os.getenv("REPORT_DIR", str(BASE_DIR / "reports")))

        # Load scoring weights from env
        self.SCORING_WEIGHTS = {
            "keyword_match": float(os.getenv("WEIGHT_KEYWORD_MATCH", "30")),
            "technical_skill": float(os.getenv("WEIGHT_TECHNICAL_SKILL", "25")),
            "experience_relevance": float(os.getenv("WEIGHT_EXPERIENCE", "20")),
            "structure": float(os.getenv("WEIGHT_STRUCTURE", "10")),
            "education": float(os.getenv("WEIGHT_EDUCATION", "5")),
            "formatting": float(os.getenv("WEIGHT_FORMATTING", "10")),
        }

    def _validate(self):
        # Reject insecure default JWT secret in production
        if self.ENVIRONMENT == "production":
            if not self.JWT_SECRET_KEY or self.JWT_SECRET_KEY in (
                "change-me-in-production",
                "your-secret-key-change-in-production",
                "change-me-to-a-long-random-string",
                "dev-secret-key-change-in-production-abc123xyz",
            ):
                raise ConfigError(
                    "JWT_SECRET_KEY must be set to a strong, unique value in production. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
                )
            if len(self.JWT_SECRET_KEY) < 32:
                raise ConfigError(
                    "JWT_SECRET_KEY must be at least 32 characters long in production."
                )

        if self.ACCESS_TOKEN_EXPIRE_MINUTES < 1:
            raise ConfigError("ACCESS_TOKEN_EXPIRE_MINUTES must be at least 1.")

        if self.MAX_FILE_SIZE_MB < 1 or self.MAX_FILE_SIZE_MB > 100:
            raise ConfigError("MAX_FILE_SIZE_MB must be between 1 and 100.")

        if self.PASSWORD_MIN_LENGTH < 6:
            raise ConfigError("PASSWORD_MIN_LENGTH must be at least 6.")

        # Validate scoring weights sum to 100
        weight_sum = sum(self.SCORING_WEIGHTS.values())
        if abs(weight_sum - 100.0) > 0.01:
            raise ConfigError(
                f"Scoring weights must sum to 100. Current sum: {weight_sum}. "
                f"Weights: {self.SCORING_WEIGHTS}"
            )
        for name, value in self.SCORING_WEIGHTS.items():
            if value < 0:
                raise ConfigError(f"Scoring weight '{name}' cannot be negative: {value}")

        if self.RATE_LIMIT_WINDOW_SECONDS < 1:
            raise ConfigError("RATE_LIMIT_WINDOW_SECONDS must be at least 1.")

        if self.LOG_LEVEL not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            raise ConfigError(f"Invalid LOG_LEVEL: {self.LOG_LEVEL}")

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def max_file_size_mb_display(self) -> int:
        return self.MAX_FILE_SIZE_MB


settings = Settings()
