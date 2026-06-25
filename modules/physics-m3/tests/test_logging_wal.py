from modules.logging_wal import WALogger

def test_walogger_init():
    logger = WALogger()
    assert logger is not None

def test_walogger_record():
    logger = WALogger()
    log_id = logger.record("compute", "verify convergence", "kimi", "fem_solver.py",
                           {"method": "SIMP", "iter": 5}, domain="mecanica")
    assert log_id is not None

def test_walogger_record_query():
    logger = WALogger()
    logger.record("test", "basic", "kimi", "test.py", {"tool": "pytest"},
                  domain="mecanica", scale="micro")
    results = logger.query()
    assert len(results) >= 1
