"""Tests for unified MapaUnico."""
import pytest
from src.common.mapa_unico import MapaUnico
from src.common import database
from src.common.database import deploy_schema
import tempfile
import os

@pytest.fixture(autouse=True)
def db_setup():
    tmp_db = tempfile.mktemp(suffix=".db")
    database.DB_PATH = tmp_db
    deploy_schema(create_db_if_missing=True, db_path=tmp_db)
    yield
    os.unlink(tmp_db)

def test_mapa_init():
    m = MapaUnico(project="TEST")
    assert m.project == "TEST"

def test_mapa_register():
    m = MapaUnico(project="TEST")
    eid = m.register(domain="mecanica", name="test_param", data={"E": 200e9})
    assert isinstance(eid, str)
