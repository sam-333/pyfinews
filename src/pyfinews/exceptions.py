"""Exceptions raised by pyfinews."""


class PyfinewsError(Exception):
    """Base exception for package errors."""


class NewsFetchError(PyfinewsError):
    """Raised when the news provider cannot be reached or returns an error."""


class NewsParseError(PyfinewsError):
    """Raised when a provider response cannot be parsed."""
