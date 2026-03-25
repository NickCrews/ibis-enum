from __future__ import annotations

from importlib import metadata as _importlib_metadata

from ibis_enum._enum import IbisEnum as IbisEnum

try:
    __version__ = _importlib_metadata.version(__name__)
except _importlib_metadata.PackageNotFoundError as e:
    import warnings

    warnings.warn(f"Could not determine version of {__name__}\n{e!s}", stacklevel=2)
    __version__ = "unknown"
