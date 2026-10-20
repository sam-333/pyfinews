"""Package version and default HTTP User-Agent."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pyfinews")
except PackageNotFoundError:
    __version__ = "0+unknown"

DEFAULT_USER_AGENT = f"pyfinews/{__version__}"