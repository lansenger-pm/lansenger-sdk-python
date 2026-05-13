"""Exception types for Lansenger SDK."""


class LansengerError(Exception):
    """Base exception for all Lansenger SDK errors."""

    def __init__(self, message: str, err_code: int | None = None, retryable: bool = False):
        super().__init__(message)
        self.err_code = err_code
        self.retryable = retryable


class LansengerAuthError(LansengerError):
    """Authentication/token error."""

    def __init__(self, message: str, err_code: int | None = None):
        super().__init__(message, err_code=err_code, retryable=False)


class LansengerConfigError(LansengerError):
    """Configuration error (missing credentials, etc.)."""

    def __init__(self, message: str):
        super().__init__(message, retryable=False)


class LansengerAPIError(LansengerError):
    """API response error (non-zero errCode from Lansenger)."""

    def __init__(self, message: str, err_code: int | None = None, retryable: bool = True):
        super().__init__(message, err_code=err_code, retryable=retryable)


class LansengerNetworkError(LansengerError):
    """Network/transport error (HTTP failure, timeout, etc.)."""

    def __init__(self, message: str, retryable: bool = True):
        super().__init__(message, retryable=retryable)


class LansengerFileError(LansengerError):
    """File-related error (file not found, upload failed, etc.)."""

    def __init__(self, message: str):
        super().__init__(message, retryable=False)