import json

import pytest

from bitcoin_monitoring import SyntheticGenerator, TransactionRecord, read_records, write_records


def test_generation_is_reproducible_and_balanced():
    left = SyntheticGenerator(42).generate(8, "mixed")
    right = SyntheticGenerator(42).generate(8, "mixed")
    assert [x.to_dict() for x in left] == [x.to_dict() for x in right]
    assert all(r.input_value_sats == r.output_value_sats + r.fee_sats for r in left)


@pytest.mark.parametrize("fmt", ["csv", "json", "xml"])
def test_round_trip(tmp_path, fmt):
    path = tmp_path / f"records.{fmt}"
    records = SyntheticGenerator(3).generate(3, "peeling-chain")
    write_records(records, path)
    assert [r.to_dict() for r in read_records(path)] == [r.to_dict() for r in records]


def test_labels_and_invalid_record():
    record = SyntheticGenerator(1).generate(1, "mixing-like")[0]
    assert {"mixing_like", "many_inputs", "many_outputs"}.issubset(record.labels)
    raw = record.to_dict(); raw["fee_sats"] = 0
    with pytest.raises(ValueError): TransactionRecord.from_dict(raw)
