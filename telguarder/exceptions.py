"""telguarder exceptions."""


class TelguarderError(Exception):
    """Generic Telguarder exception."""


class TelguarderNotFoundError(TelguarderError):
    """Telguarder not found exception."""


class TelguarderConnectionError(TelguarderError):
    """Telguarder connection exception."""


class TelguarderConnectionTimeoutError(TelguarderConnectionError):
    """Telguarder connection timeout exception."""


class TelguarderRateLimitError(TelguarderConnectionError):
    """Telguarder Rate Limit exception."""


class TelguarderUnauthorizedError(TelguarderError):
    """Telguarder unauthorized exception."""
