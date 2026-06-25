"""Tests for ExperimentalData — aligned with actual module API."""

import numpy as np
import pytest
import tempfile, json, csv

from modules.experimental_data import ExperimentalData


@pytest.fixture
def ed():
    return ExperimentalData("test")


def test_init(ed):
    assert ed.name == "test"
    assert ed.list_datasets() == []


def test_add_and_get(ed):
    ed.add_dataset("a", [0, 1, 2], [0.5, 0.6, 0.7])
    assert "a" in ed.list_datasets()
    d = ed.get_dataset("a")
    assert "x" in d and "y" in d


def test_get_keyerror(ed):
    with pytest.raises(KeyError):
        ed.get_dataset("x")


def test_summary(ed):
    ed.add_dataset("a", [0, 1], [0.5, 0.6])
    s = ed.summary()
    assert "a" in s
    assert s["a"]["n_points"] == 2


def test_resample(ed):
    ed.add_dataset("lin", [0, 2, 4], [0, 2, 4])
    r = ed.resample("lin", [1, 3])
    assert np.allclose(r, [1, 3], atol=0.01)


def test_validate_clean(ed):
    ed.add_dataset("c", [0, 1], [0.5, 0.6])
    r = ed.validate()
    assert r["valid"]


def test_json_roundtrip(ed):
    ed.add_dataset("t", [0, 1], [0.0, 1.0])
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w+", delete=False) as f:
        ed.to_json(f.name)
        f.seek(0)
        data = json.load(f)
    # to_json wraps in {datasets: [...]}, load via inner arrays
    ed2 = ExperimentalData("loaded")
    ed2.from_dict(data)
    assert "t" in ed2.list_datasets()


def test_from_dict(ed):
    ed.from_dict({"datasets": [{"name": "d", "x": [0, 1], "y": [10, 20]}]})
    assert len(ed.list_datasets()) > 0


def test_csv(ed):
    with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as f:
        w = csv.writer(f)
        w.writerow(["x", "y"]); w.writerow([0, 10]); w.writerow([1, 11])
        fname = f.name
    ed2 = ExperimentalData("csv")
    ed2.from_csv(fname)
    assert len(ed2.list_datasets()) > 0


def test_to_json_file(ed):
    ed.add_dataset("t", [0, 1], [0.0, 1.0])
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        ed.to_json(f.name)
    with open(f.name) as fh:
        data = json.load(fh)
    assert "datasets" in data
