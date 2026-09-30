"""Deterministic synthetic transaction scenario generator."""

from __future__ import annotations

import hashlib
import random
from datetime import datetime, timedelta, timezone
from typing import Iterator

from .schema import Address, TransactionRecord

SCENARIOS = ("normal", "anomalous", "peeling-chain", "mixing-like", "mixed")


class SyntheticGenerator:
    def __init__(self, seed: int = 0, start: datetime | None = None, block_height: int = 850_000) -> None:
        self.seed = seed
        self.random = random.Random(seed)
        self.start = (start or datetime(2024, 1, 1, tzinfo=timezone.utc)).astimezone(timezone.utc)
        self.block_height = block_height
        self._counter = 0

    def generate(self, count: int, scenario: str = "mixed") -> list[TransactionRecord]:
        if count < 0 or scenario not in SCENARIOS:
            raise ValueError(f"count must be non-negative and scenario one of {SCENARIOS}")
        return list(self.iter_records(count, scenario))

    def iter_records(self, count: int, scenario: str = "mixed") -> Iterator[TransactionRecord]:
        for _ in range(count):
            chosen = self.random.choice(SCENARIOS[:-1]) if scenario == "mixed" else scenario
            yield self._make(chosen)

    def _address(self, role: str, index: int | None = None) -> Address:
        n = self._counter if index is None else index
        token = hashlib.sha256(f"{self.seed}:{role}:{n}".encode()).hexdigest()
        prefixes = (("1", "p2pkh"), ("3", "p2sh"), ("bc1q", "bech32"), ("bc1p", "taproot"))
        prefix, address_type = prefixes[int(token[:2], 16) % len(prefixes)]
        return Address(prefix + token[:33], address_type=address_type, cluster_id=f"cluster-{token[:8]}")

    def _make(self, scenario: str) -> TransactionRecord:
        self._counter += 1
        r = self.random
        if scenario == "normal":
            input_count, output_count, amount, fee, labels = r.randint(1, 2), r.randint(2, 3), r.randint(100_000, 8_000_000), r.randint(500, 8_000), ("normal",)
        elif scenario == "anomalous":
            input_count, output_count, amount, fee, labels = r.randint(3, 8), r.randint(1, 2), r.randint(20_000, 80_000), r.randint(20_000, 100_000), ("anomalous", "high_fee_rate")
        elif scenario == "peeling-chain":
            input_count, output_count, amount, fee, labels = 1, 2, r.randint(2_000_000, 20_000_000), r.randint(1_000, 5_000), ("peeling_chain", "change_output")
        else:
            input_count, output_count, amount, fee, labels = r.randint(5, 12), r.randint(5, 12), r.randint(500_000, 5_000_000), r.randint(2_000, 12_000), ("mixing_like", "many_inputs", "many_outputs")
        input_value = amount + fee
        if scenario == "peeling-chain":
            chain = self._counter // 3
            inputs = (self._address("peel-input", chain),)
            outputs = (self._address("peel-output", chain + 1), self._address("peel-change", chain))
        elif scenario == "mixing-like":
            cluster = self._counter // 4
            inputs = tuple(self._address("mixer-input", cluster * 20 + i) for i in range(input_count))
            outputs = tuple(self._address("mixer-output", cluster * 20 + i) for i in range(output_count))
        else:
            cluster = self._counter // 5
            inputs = tuple(self._address("input", cluster * 10 + i) for i in range(input_count))
            outputs = tuple(self._address("output", cluster * 10 + i) for i in range(output_count))
        # Keep output distribution exact while preserving a useful amount range.
        base, remainder = divmod(amount, output_count)
        metadata = {"generator_seed": self.seed, "generator_index": self._counter, "input_count": input_count, "output_count": output_count}
        timestamp = (self.start + timedelta(minutes=self._counter * 10)).isoformat().replace("+00:00", "Z")
        txid = hashlib.sha256(f"{self.seed}:{self._counter}:{scenario}".encode()).hexdigest()
        countries = ("IN", "US", "DE", "SG", "NL", "GB")
        src_ip = f"192.0.2.{(self._counter % 240) + 1}"
        dst_ip = f"198.51.100.{((self._counter * 7) % 240) + 1}"
        output_values = [base + (1 if i < remainder else 0) for i in range(output_count)]
        return TransactionRecord(
            txid, timestamp, self.block_height + self._counter, inputs, outputs,
            input_value, amount, fee, scenario, labels,
            metadata | {"output_values_sats": output_values},
            src_ip, dst_ip, r.randint(1024, 65535), 8333,
            countries[self._counter % len(countries)], f"AS{64500 + (self._counter % 12)}",
            r.choice(("P2PKH", "P2SH", "P2WPKH", "P2TR")),
        )
