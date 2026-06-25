import pytest, tempfile, os
from modules.knowledge_base import KnowledgeBase
def test_kb_init():
    with tempfile.TemporaryDirectory() as td:
        kb = KnowledgeBase(db_path=os.path.join(td, 'kb'))
        assert kb is not None
def test_kb_methods():
    with tempfile.TemporaryDirectory() as td:
        kb = KnowledgeBase(db_path=os.path.join(td, 'kb'))
        for attr in ('get', 'query', 'register', 'sources', 'summary'):
            assert hasattr(kb, attr)
