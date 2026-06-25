#!/usr/bin/env python3
"""
Test Result ETL Ingestion — Composite Biomaterial for Wind Energy.

Registers mechanical test results in the universal registry (objects table)
and inserts corresponding records in test_results with full constraint
validation at the application layer.

Usage:
    from src.03-data-management.etl.ingest_test_results import ingest_test_result

    obj = ingest_test_result(
        specimen_id="<specimen-uuid>",
        test_standard="ASTM D638",
        test_type="tensile",
        property_measured="tensile_strength",
        value=12.5,
        unit="MPa",
        uncertainty=1.2,
        uncertainty_type="standard_deviation",
        num_replicates=5,
        test_date="2026-06-05",
        testing_machine="Instron 5967",
    )
"""
import json
import sys
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.common.database import database, DatabaseError
from src.common.registry import create_object, object_exists, ValidationError


class TestResultIngestionError(ValueError):
    """Raised on invalid test result data."""
    pass


VALID_TEST_TYPES = {"tensile", "flexural", "compressive", "hardness", "fatigue", "impact"}
VALID_UNCERTAINTY_TYPES = {"standard_deviation", "confidence_interval", "instrument_error"}
VALID_VALIDATION_STATUSES = {"PENDING", "PASS", "FAIL"}


def _validate_test_result_data(data: Dict[str, Any]) -> None:
    """Validate test result data against application-layer constraints."""
    errors = []

    required = ["specimen_id", "test_standard", "test_type", "property_measured",
                "value", "unit", "uncertainty", "uncertainty_type",
                "num_replicates", "test_date", "testing_machine"]
    for field in required:
        if field not in data or data[field] is None:
            errors.append(f"Missing required field: {field}")

    if errors:
        raise TestResultIngestionError("; ".join(errors))

    # Specimen must exist
    if not object_exists(data["specimen_id"]):
        raise TestResultIngestionError(
            f"specimen_id '{data['specimen_id']}' does not exist"
        )

    if data["test_type"] not in VALID_TEST_TYPES:
        raise TestResultIngestionError(
            f"Invalid test_type '{data['test_type']}'. Must be one of: {sorted(VALID_TEST_TYPES)}"
        )

    if data["uncertainty_type"] not in VALID_UNCERTAINTY_TYPES:
        raise TestResultIngestionError(
            f"Invalid uncertainty_type '{data['uncertainty_type']}'"
        )

    if data["value"] <= 0:
        errors.append(f"value must be > 0, got {data['value']}")

    if not (0 <= data["uncertainty"] < data["value"]):
        errors.append(
            f"uncertainty ({data['uncertainty']}) must be >= 0 and < value ({data['value']})"
        )

    if data["num_replicates"] < 1:
        errors.append(f"num_replicates must be >= 1, got {data['num_replicates']}")

    # Humidity validation
    h = data.get("humidity_pct")
    if h is not None and not (0 <= h <= 100):
        errors.append(f"humidity_pct must be between 0 and 100, got {h}")

    # Temperature validation
    t = data.get("temperature_c")
    if t is not None and not (-100 < t < 200):
        errors.append(f"temperature_c must be between -100 and 200, got {t}")

    # Validation status
    vs = data.get("validation_status", "PENDING")
    if vs not in VALID_VALIDATION_STATUSES:
        errors.append(f"validation_status must be one of {VALID_VALIDATION_STATUSES}")

    if errors:
        raise TestResultIngestionError("; ".join(errors))


def ingest_test_result(
    specimen_id: str,
    test_standard: str,
    test_type: str,
    property_measured: str,
    value: float,
    unit: str,
    uncertainty: float,
    uncertainty_type: str,
    num_replicates: int,
    test_date: str,
    testing_machine: str,
    operator: Optional[str] = None,
    temperature_c: Optional[float] = None,
    humidity_pct: Optional[float] = None,
    failure_mode: Optional[str] = None,
    notes: Optional[str] = None,
    raw_data_file: Optional[str] = None,
    validation_status: str = "PENDING",
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Register a test result in the universal registry and entity table.

    Args:
        specimen_id: UUID of the tested specimen.
        test_standard: e.g. 'ASTM D638', 'ASTM D790'.
        test_type: One of: tensile, flexural, compressive, hardness, fatigue, impact.
        property_measured: e.g. 'tensile_strength', 'elastic_modulus'.
        value: Measured value (> 0).
        unit: e.g. 'MPa', 'GPa', 'Shore D'.
        uncertainty: Measurement uncertainty (>= 0 and < value).
        uncertainty_type: One of: standard_deviation, confidence_interval, instrument_error.
        num_replicates: Number of replicate tests (>= 1).
        test_date: ISO 8601 date.
        testing_machine: Equipment identifier.
        operator: Optional operator name/ID.
        temperature_c: Optional test ambient temperature.
        humidity_pct: Optional ambient humidity (0-100).
        failure_mode: Optional failure mode description.
        notes: Optional free-text notes.
        raw_data_file: Optional path to raw data file.
        validation_status: One of PENDING, PASS, FAIL.
        tags: Optional list of search tags.
        metadata: Optional JSON-serializable metadata dict.

    Returns:
        Dict with 'object_id', 'test_type', and 'status'.

    Raises:
        TestResultIngestionError: On validation failure.
    """
    data = {k: v for k, v in locals().items() if k not in ("tags", "metadata")}
    _validate_test_result_data(data)

    # Register in universal registry
    object_id = create_object(
        object_type="test_result",
        tags=tags,
        metadata=metadata,
    )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with database() as db:
        db.execute(
            """INSERT INTO test_results
               (id, specimen_id, test_standard, test_type, property_measured,
                value, unit, uncertainty, uncertainty_type, num_replicates,
                test_date, testing_machine, operator, temperature_c,
                humidity_pct, failure_mode, notes, raw_data_file,
                validation_status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                object_id, specimen_id, test_standard, test_type, property_measured,
                value, unit, uncertainty, uncertainty_type, num_replicates,
                test_date, testing_machine, operator, temperature_c,
                humidity_pct, failure_mode, notes, raw_data_file,
                validation_status,
            ),
        )
        db.commit()

    return {
        "object_id": object_id,
        "test_type": test_type,
        "status": "registered",
    }


def list_test_results(
    test_type: Optional[str] = None,
    specimen_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List registered test results.

    Args:
        test_type: Optional filter.
        specimen_id: Optional filter.

    Returns:
        List of test result dicts joined with objects.
    """
    conditions = ["tr.id = o.id"]
    params = []
    if test_type:
        conditions.append("tr.test_type = ?")
        params.append(test_type)
    if specimen_id:
        conditions.append("tr.specimen_id = ?")
        params.append(specimen_id)

    where = " AND ".join(conditions)
    with database() as db:
        rows = db.execute(
            f"""SELECT o.*, tr.test_type, tr.test_standard, tr.property_measured,
                       tr.value, tr.unit, tr.uncertainty, tr.specimen_id,
                       tr.validation_status as test_validation_status
                FROM test_results tr
                JOIN objects o ON {where}
                ORDER BY o.created_at DESC""",
            params,
        ).fetchall()
    return [dict(r) for r in rows]


def main() -> None:
    """CLI entry point for test result ingestion."""
    import argparse

    parser = argparse.ArgumentParser(description="Ingest test result")
    parser.add_argument("--specimen-id", required=True)
    parser.add_argument("--test-standard", required=True)
    parser.add_argument("--test-type", required=True, choices=sorted(VALID_TEST_TYPES))
    parser.add_argument("--property", required=True)
    parser.add_argument("--value", type=float, required=True)
    parser.add_argument("--unit", required=True)
    parser.add_argument("--uncertainty", type=float, required=True)
    parser.add_argument("--uncertainty-type", required=True)
    parser.add_argument("--num-replicates", type=int, required=True)
    parser.add_argument("--test-date", required=True)
    parser.add_argument("--testing-machine", required=True)
    parser.add_argument("--operator")
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--humidity", type=float)
    parser.add_argument("--failure-mode")
    parser.add_argument("--notes")
    parser.add_argument("--list", action="store_true", help="List test results")

    args = parser.parse_args()

    if args.list:
        results = list_test_results()
        if results:
            print(f"Test results ({len(results)}):")
            for r in results:
                print(f"  {r['id'][:8]}... [{r['test_type']}] {r['property_measured']}={r['value']} {r['unit']}")
        else:
            print("No test results registered.")
        return

    result = ingest_test_result(
        specimen_id=args.specimen_id,
        test_standard=args.test_standard,
        test_type=args.test_type,
        property_measured=args.property,
        value=args.value,
        unit=args.unit,
        uncertainty=args.uncertainty,
        uncertainty_type=args.uncertainty_type,
        num_replicates=args.num_replicates,
        test_date=args.test_date,
        testing_machine=args.testing_machine,
        operator=args.operator,
        temperature_c=args.temperature,
        humidity_pct=args.humidity,
        failure_mode=args.failure_mode,
        notes=args.notes,
    )
    print(f"Test result registered: {result['object_id']}")
    print(f"  Type: {result['test_type']}")


if __name__ == "__main__":
    main()
