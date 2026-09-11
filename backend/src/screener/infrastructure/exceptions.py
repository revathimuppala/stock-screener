class ProviderError(Exception):
    """Base for any failure talking to a market data provider."""


class TransientProviderError(ProviderError):
    """Timeouts, connection resets — worth retrying."""


class ProviderDataError(ProviderError):
    """The provider responded but the data was unusable (e.g. unknown
    symbol, malformed payload). Never retried — retrying won't fix bad data."""
