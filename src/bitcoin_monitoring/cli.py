"""Command-line interface for synthetic data generation and validation."""

from __future__ import annotations

import argparse
from pathlib import Path

from .generator import SCENARIOS, SyntheticGenerator
from .ingestion import read_records, write_records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="btc-synth")
    sub = parser.add_subparsers(dest="command", required=True)
    gen = sub.add_parser("generate", help="generate synthetic transactions")
    gen.add_argument("--count", type=int, required=True); gen.add_argument("--seed", type=int, default=0)
    gen.add_argument("--scenario", choices=SCENARIOS, default="mixed"); gen.add_argument("--format", choices=("csv", "json", "xml"), required=True); gen.add_argument("--output", type=Path, required=True)
    val = sub.add_parser("validate", help="ingest and validate a document"); val.add_argument("path", type=Path); val.add_argument("--format", choices=("csv", "json", "xml"))
    args = parser.parse_args(argv)
    if args.command == "generate": write_records(SyntheticGenerator(args.seed).generate(args.count, args.scenario), args.output, args.format); print(f"wrote {args.count} records to {args.output}")
    else: print(f"validated {len(read_records(args.path, args.format))} records from {args.path}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
