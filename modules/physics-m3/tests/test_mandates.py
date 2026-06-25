#!/usr/bin/env python3
"""Tests for M4 (Mapa Unico), M5 (WAL Logging), M6 (Knowledge Base)."""
import sys
import os
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "modules"))

from src.common.mapa_unico import MapaUnico
from src.common.registry import update_validation_status
from src.common import database
from src.common.database import deploy_schema
from logging_wal import WALogger
from knowledge_base import KnowledgeBase


class TestM4MapaUnico:
    def setup_method(self):
        self.tmp_db = tempfile.mktemp(suffix=".db")
        database.DB_PATH = self.tmp_db
        deploy_schema(create_db_if_missing=True, db_path=self.tmp_db)
        self.mapa = MapaUnico(project="TEST")

    def teardown_method(self):
        os.unlink(self.tmp_db)

    def test_register_entry(self):
        eid = self.mapa.register("materiais", "paper_mache", {"E1": 3.5})
        assert eid.startswith("MAP-")

    def test_query_by_domain(self):
        self.mapa.register("materiais", "mat1", {"E": 3})
        self.mapa.register("fluidos", "fl1", {"Re": 1e5})
        results = self.mapa.query(domain="materiais")
        assert len(results) == 1

    def test_validation_status(self):
        eid = self.mapa.register("mecanica", "beam", {"M": 100})
        update_validation_status(eid, "PASS")
        entry = self.mapa.get(eid)
        assert entry["validation_status"] == "PASS"

    def test_summary(self):
        self.mapa.register("a", "x", {})
        s = self.mapa.summary()
        assert s["total_entries"] > 0
        assert "a" in s["domains"]


class TestM5WALogger:
    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        self.log = WALogger(log_dir=self.tmp)

    def test_record_log(self):
        lid = self.log.record(
            what="BEM analysis", why="design optimization", who="agent",
            where="fluid_dynamics.py:bem_theory",
            how={"method": "BEM theory", "tool": "Python/NumPy"},
            domain="fluidos", scale="meso",
        )
        assert lid.startswith("LOG-")

    def test_query_logs(self):
        self.log.record("t1", "test", "agent", "f.py", {"method": "x"}, domain="a")
        results = self.log.query(domain="a")
        assert len(results) >= 1

    def test_log_persisted(self):
        self.log.record("t2", "test", "agent", "f.py", {"method": "y"})
        log_files = [f for f in os.listdir(self.tmp) if f.endswith(".jsonl")]
        assert len(log_files) > 0


class TestM6KnowledgeBase:
    def setup_method(self):
        self.kb = KnowledgeBase()

    def test_has_material_sources(self):
        assert len(self.kb.sources) >= 3

    def test_query_by_domain(self):
        results = self.kb.query(domain="materiais")
        assert len(results) > 0

    def test_query_by_min_score(self):
        results = self.kb.query(min_score=8)
        for r in results:
            assert r.quality_score >= 8

    def test_register_new_source(self):
        sid = self.kb.register(
            title="Test paper", source_type="article",
            authors=["Test, A."], year=2025, doi="10.1234/test",
            quality_score=9, domains=["materiais"],
        )
        assert sid.startswith("SRC-")

    def test_validate_source(self):
        sid = self.kb.register("New", quality_score=6)
        self.kb.validate(sid, "VERIFIED")
        assert self.kb.get(sid).validation_status == "VERIFIED"

    def test_summary(self):
        s = self.kb.summary()
        assert s["total_sources"] > 0
        assert s["avg_quality"] > 0
