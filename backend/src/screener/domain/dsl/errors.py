class DslError(Exception):
    """A query failed to parse — always carries the character position of
    the problem so the API/UI can point at exactly where it went wrong."""

    def __init__(self, message: str, position: int):
        super().__init__(message)
        self.message = message
        self.position = position
