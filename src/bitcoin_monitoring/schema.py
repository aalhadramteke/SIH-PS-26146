"""Canonical, dependency-free transaction metadata schema."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Mapping


class ValidationError(ValueError):
    """Raised when a record does not satisfy the canonical schema."""


@dataclass(frozen=True)
class Address:
    address: str
    address_type: str = "p2pkh"
    cluster_id: str | None = None

    def __post_init__(self) -> None:
        if not self.address or any(c.isspace() for c in self.address):
            raise ValidationError("address must be a non-empty token")
        if self.address_type not in {"p2pkh", "p2sh", "bech32", "taproot"}:
            raise ValidationError(f"unsupported address_type: {self.address_type}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TransactionRecord:
    txid: str
    timestamp: str
    block_height: int
    inputs: tuple[Address, ...]
    outputs: tuple[Address, ...]
    input_value_sats: int
    output_value_sats: int
    fee_sats: int
    scenario: str
    labels: tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    src_ip: str = "192.0.2.1"
    dst_ip: str = "198.51.100.1"
    src_port: int = 8333
    dst_port: int = 8333
    geo_country: str = "ZZ"
    asn: str = "AS64500"
    script_type: str = "P2WPKH"

    def __post_init__(self) -> None:
        if len(self.txid) != 64 or any(c not in "0123456789abcdef" for c in self.txid):
            raise ValidationError("txid must be a lowercase 64-character hex string")
        try:
            parsed = datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValidationError("timestamp must be ISO-8601") from exc
        if parsed.tzinfo is None:
            raise ValidationError("timestamp must include a timezone")
        if self.block_height < 0 or self.input_value_sats <= 0 or self.output_value_sats <= 0:
            raise ValidationError("height and transaction values must be positive")
        if self.fee_sats < 0 or self.output_value_sats + self.fee_sats != self.input_value_sats:
            raise ValidationError("inputs must equal outputs plus fee")
        if not self.inputs or not self.outputs or not self.scenario:
            raise ValidationError("inputs, outputs, and scenario are required")
        if len(set(self.labels)) != len(self.labels):
            raise ValidationError("labels must be unique")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["inputs"] = [a.to_dict() for a in self.inputs]
        data["outputs"] = [a.to_dict() for a in self.outputs]
        data["labels"] = list(self.labels)
        data["metadata"] = dict(self.metadata)
        data["src_ip"] = self.src_ip
        data["dst_ip"] = self.dst_ip
        data["src_port"] = self.src_port
        data["dst_port"] = self.dst_port
        data["geo_country"] = self.geo_country
        data["asn"] = self.asn
        data["script_type"] = self.script_type
        data["input_addresses"] = [a.address for a in self.inputs]
        data["output_addresses"] = [a.address for a in self.outputs]
        data["input_amounts"] = [self.input_value_sats // len(self.inputs)] * len(self.inputs)
        data["output_amounts"] = self.metadata.get("output_values_sats", [self.output_value_sats // len(self.outputs)] * len(self.outputs))
        return data

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "TransactionRecord":
        required = {"txid", "timestamp", "block_height", "inputs", "outputs", "input_value_sats", "output_value_sats", "fee_sats", "scenario"}
        missing = required - set(raw)
        if missing:
            raise ValidationError(f"missing fields: {sorted(missing)}")

        def addresses(values: Any) -> tuple[Address, ...]:
            if not isinstance(values, list):
                raise ValidationError("addresses must be arrays")
            return tuple(Address(**value) if isinstance(value, dict) else Address(str(value)) for value in values)

        return cls(
            txid=str(raw["txid"]), timestamp=str(raw["timestamp"]), block_height=int(raw["block_height"]),
            inputs=addresses(raw["inputs"]), outputs=addresses(raw["outputs"]),
            input_value_sats=int(raw["input_value_sats"]), output_value_sats=int(raw["output_value_sats"]),
            fee_sats=int(raw["fee_sats"]), scenario=str(raw["scenario"]),
            labels=tuple(str(x) for x in raw.get("labels", [])), metadata=dict(raw.get("metadata", {})),
            src_ip=str(raw.get("src_ip", "192.0.2.1")), dst_ip=str(raw.get("dst_ip", "198.51.100.1")),
            src_port=int(raw.get("src_port", 8333)), dst_port=int(raw.get("dst_port", 8333)),
            geo_country=str(raw.get("geo_country", "ZZ")), asn=str(raw.get("asn", "AS64500")),
            script_type=str(raw.get("script_type", "P2WPKH")),
        )
