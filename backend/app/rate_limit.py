"""Rate limiter — shared instance for all route modules."""

import sys

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60/minute"],
    enabled="pytest" not in sys.modules,
)
