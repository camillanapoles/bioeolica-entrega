import pytest
from modules.vvv_protocol import VVVReport, CrossValidation

def test_vvvreport_init():
    r = VVVReport(study_name="test")
    assert r.study_name == "test"

def test_vvvreport_status():
    r = VVVReport(study_name="test")
    assert r.status == "PENDING"

def test_crossval_init():
    cv = CrossValidation()
    assert cv is not None
