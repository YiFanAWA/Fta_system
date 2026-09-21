"""Backward-compatible API import entrypoint.

The implementation lives in :mod:`app.api_server`; this thin module keeps
the existing ``uvicorn api_server:app`` command and local test imports stable.
"""

import sys

from app import api_server as _implementation


sys.modules[__name__] = _implementation
