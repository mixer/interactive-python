class DiscoveryError(Exception):
    """Raised if some error occurs during service discovery
    that we didn't anticipate.
    """
    pass


class NoServersAvailableError(Exception):
    """Raised if Beam reports that no servers are available."""
    pass
