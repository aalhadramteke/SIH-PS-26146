"""Synthetic Bitcoin transaction data generation and ingestion."""

from .generator import SCENARIOS, SyntheticGenerator
from .ingestion import read_records, write_records
from .schema import Address, TransactionRecord, ValidationError

__all__ = ["Address", "SCENARIOS", "SyntheticGenerator", "TransactionRecord", "ValidationError", "read_records", "write_records"]
