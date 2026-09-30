"""Serialization and ingestion for canonical records."""

from __future__ import annotations

import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable

from .schema import TransactionRecord, ValidationError

FORMATS = {"csv", "json", "xml"}


def _format(path: str | Path, format: str | None) -> str:
    fmt = (format or Path(path).suffix.lstrip(".")).lower()
    if fmt not in FORMATS:
        raise ValueError("format must be csv, json, or xml")
    return fmt


def write_records(records: Iterable[TransactionRecord], path: str | Path, format: str | None = None) -> None:
    records = list(records)
    fmt = _format(path, format)
    if fmt == "json":
        Path(path).write_text(json.dumps([r.to_dict() for r in records], indent=2), encoding="utf-8")
    elif fmt == "csv":
        fields = ["txid", "timestamp", "block_height", "input_value_sats", "output_value_sats", "fee_sats", "scenario", "labels", "inputs", "outputs", "input_addresses", "output_addresses", "input_amounts", "output_amounts", "src_ip", "dst_ip", "src_port", "dst_port", "geo_country", "asn", "script_type", "metadata"]
        with Path(path).open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields); writer.writeheader()
            for record in records:
                row = record.to_dict(); row.update({key: json.dumps(row[key], separators=(",", ":")) for key in ("labels", "inputs", "outputs", "input_addresses", "output_addresses", "input_amounts", "output_amounts", "metadata")}); writer.writerow(row)
    else:
        root = ET.Element("transactions")
        for record in records:
            node = ET.SubElement(root, "transaction")
            for key, value in record.to_dict().items():
                child = ET.SubElement(node, key); child.text = json.dumps(value, separators=(",", ":")) if isinstance(value, (list, dict)) else str(value)
        ET.indent(root, space="  "); Path(path).write_text(ET.tostring(root, encoding="unicode"), encoding="utf-8")


def read_records(path: str | Path, format: str | None = None) -> list[TransactionRecord]:
    fmt = _format(path, format); text = Path(path).read_text(encoding="utf-8")
    if fmt == "json":
        raw = json.loads(text)
    elif fmt == "csv":
        raw = []
        for row in csv.DictReader(text.splitlines()):
            for key in ("labels", "inputs", "outputs", "input_addresses", "output_addresses", "input_amounts", "output_amounts", "metadata"):
                if key in row and row[key]: row[key] = json.loads(row[key])
            raw.append(row)
    else:
        root = ET.fromstring(text); raw = []
        for node in root.findall("transaction"):
            row = {child.tag: child.text or "" for child in node}
            for key in ("labels", "inputs", "outputs", "metadata"):
                if key in row: row[key] = json.loads(row[key])
            raw.append(row)
    if not isinstance(raw, list): raise ValidationError("input document must contain an array of records")
    return [TransactionRecord.from_dict(item) for item in raw]
