"""A toolset for connecting OSTRICH with SWMM."""

import datetime as dt

# Add __version__ variable to module namespace
from .version import __version__  # noqa: F401

SWMM_EPOCH_DATETIME = dt.datetime(1899, 12, 30)
"""The epoch for SWMM timestamps as a Python datetime."""
