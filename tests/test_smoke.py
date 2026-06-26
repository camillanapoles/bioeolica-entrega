"""Smoke test: infraestrutura mínima de GitOps/CI funciona."""
from pathlib import Path


def test_workflows_existem():
    wf = Path(".github/workflows")
    for name in ["ci.yml", "spec-gate.yml", "gitnexus-impact.yml", "vvv-certify.yml"]:
        assert (wf / name).exists(), f"workflow {name} ausente"


def test_specs_validos():
    import yaml
    sp = Path("specs")
    assert any(sp.rglob("*.yaml")), "nenhum spec em specs/"
    for f in sp.rglob("*.yaml"):
        doc = yaml.safe_load(f.read_text())
        for key in ["id", "title", "lab", "status", "owner"]:
            assert key in doc, f"{f} sem campo {key}"


def test_gitops_doc_presente():
    assert Path("GITOPS.md").exists()
    assert Path("specs/README.md").exists()
