"""Custom exceptions for the ingest layer."""

from __future__ import annotations


class DataValidationError(ValueError):
    """Raised when an ingested DataFrame fails schema or value validation."""
