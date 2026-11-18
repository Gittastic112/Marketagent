class SourceAdapterError(ValueError):
    """A safe public failure; never holds raw provider responses or credentials."""

    def __init__(self, code: str, message: str, status_code: int = 422, *, retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.retryable = retryable
