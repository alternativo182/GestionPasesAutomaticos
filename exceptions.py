class PasesError(Exception):
    """Base exception for all pases automation errors."""
    pass


class ConfigError(PasesError):
    """Error loading JSON configuration files."""
    pass


class ValidationError(PasesError):
    """Invalid user input."""
    pass


class LoginTimeoutError(PasesError):
    """Timeout waiting for manual login."""
    pass


class OutlookError(PasesError):
    """Fatal error interacting with Outlook Web."""
    pass


class FormsError(PasesError):
    """Non-fatal error completing a Microsoft Forms form."""
    pass
