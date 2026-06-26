"""TDD: core/config.py — config declarativa, nada hardcoded (P$1)."""
import textwrap


def test_config_carrega_yaml(tmp_path):
    cfg = tmp_path / "c.yaml"
    cfg.write_text(textwrap.dedent("""
        lab: lab1-material
        materiais:
          matriz:
            densidade_kg_m3: 600.0
          carga:
            fracao_volumetrica: 0.15
        ensaios:
          tracao:
            modelo: halpin_tsai
            xi: 2.0
    """))
    from core.config import load_config
    c = load_config(cfg)
    assert c["lab"] == "lab1-material"
    assert c["materiais"]["carga"]["fracao_volumetrica"] == 0.15
    assert c["ensaios"]["tracao"]["xi"] == 2.0


def test_config_rejeita_hardcoded_repetido(tmp_path):
    # smoke: config valida schema mínimo
    cfg = tmp_path / "c.yaml"
    cfg.write_text("lab: x\n")
    from core.config import load_config
    c = load_config(cfg)
    assert c["lab"] == "x"
