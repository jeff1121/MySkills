"""
Custom error hierarchy for PAN-OS firewall agent.
"""


class PAAgentError(Exception):
    """Base exception class for PA Agent errors."""

    def __init__(self, message: str, error_code: str = "UNKNOWN", remediation: str = ""):
        """
        Initialize PAAgentError.

        Args:
            message: Error message
            error_code: Machine-readable error code
            remediation: Suggested remediation steps
        """
        self.message = message
        self.error_code = error_code
        self.remediation = remediation
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Convert error to dictionary representation."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "remediation": self.remediation,
        }


class AuthenticationError(PAAgentError):
    """Raised when authentication with PAN-OS fails."""

    def __init__(self, message: str = "Authentication failed", remediation: str = None):
        if remediation is None:
            remediation = "Check PANOS_API_KEY or PANOS_USERNAME/PANOS_PASSWORD environment variables."
        super().__init__(message=message, error_code="AUTH_ERROR", remediation=remediation)


class PanosConnectionError(PAAgentError):
    """Raised when unable to connect to PAN-OS device."""

    def __init__(self, message: str = "Connection to PAN-OS failed", remediation: str = None):
        if remediation is None:
            remediation = "Verify PANOS_HOST is reachable and PANOS_VERIFY_TLS setting."
        super().__init__(message=message, error_code="CONN_ERROR", remediation=remediation)


class APIError(PAAgentError):
    """Raised when PAN-OS API call fails."""

    def __init__(self, message: str = "PAN-OS API error", remediation: str = None):
        if remediation is None:
            remediation = "Check PAN-OS API response for details. Verify xpath and element syntax."
        super().__init__(message=message, error_code="API_ERROR", remediation=remediation)


class CommitError(PAAgentError):
    """Raised when configuration commit to PAN-OS fails."""

    def __init__(self, message: str = "Configuration commit failed", remediation: str = None):
        if remediation is None:
            remediation = "Review commit errors in PAN-OS. Consider restoring from backup."
        super().__init__(message=message, error_code="COMMIT_ERROR", remediation=remediation)


class ValidationError(PAAgentError):
    """Raised when input validation fails."""

    def __init__(self, message: str = "Validation failed", remediation: str = None):
        if remediation is None:
            remediation = "Check input parameters and required fields."
        super().__init__(message=message, error_code="VALIDATION_ERROR", remediation=remediation)


class ConfigError(PAAgentError):
    """Raised when configuration is invalid."""

    def __init__(self, message: str = "Configuration error", remediation: str = None):
        if remediation is None:
            remediation = "Verify configuration values and environment variables."
        super().__init__(message=message, error_code="CONFIG_ERROR", remediation=remediation)


class StorageError(PAAgentError):
    """Raised when storage backend operation fails."""

    def __init__(self, message: str = "Storage operation failed", remediation: str = None):
        if remediation is None:
            remediation = "Check storage backend configuration (BACKUP_DIR or S3 settings)."
        super().__init__(message=message, error_code="STORAGE_ERROR", remediation=remediation)


class DryRunAbort(PAAgentError):
    """Raised when operation is aborted during dry-run."""

    def __init__(self, message: str = "Operation aborted in dry-run mode", remediation: str = None):
        if remediation is None:
            remediation = "Re-run with --confirm to execute the operation."
        super().__init__(message=message, error_code="DRY_RUN", remediation=remediation)


class RateLimitError(PAAgentError):
    """Raised when API rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", remediation: str = None):
        if remediation is None:
            remediation = "Reduce request rate or increase PANOS_RATE_LIMIT."
        super().__init__(message=message, error_code="RATE_LIMIT", remediation=remediation)
