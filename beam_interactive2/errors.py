class DiscoveryError(Exception):
    """Raised if some error occurs during service discovery
    that we didn't anticipate.
    """
    pass


class NoServersAvailableError(Exception):
    """Raised if Beam reports that no servers are available."""
    pass


class ShortCodeError(Exception):
    """Base exception raised when some unexpected event occurs in the shortcode
    OAuth flow."""
    pass


class UnknownShortCodeError(ShortCodeError):
    """Exception raised when an unknown error happens while running shortcode
    OAuth.
    """
    pass


class ShortCodeAccessDeniedError(ShortCodeError):
    """Exception raised when the user denies access to the client in shortcode
    OAuth."""
    pass


class ShortCodeTimeoutError(ShortCodeError):
    """Exception raised when the shortcode expires without being accepted."""
    pass
