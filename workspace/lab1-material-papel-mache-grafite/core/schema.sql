-- schema v1 — fundação do laboratório (P$0: SQLite backing JSON SSOT)
PRAGMA user_version = 1;

CREATE TABLE IF NOT EXISTS materials (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo          TEXT    UNIQUE NOT NULL,
    nome            TEXT    NOT NULL,
    categoria       TEXT,              -- matriz | carga | aditivo | composto
    densidade_kg_m3 REAL,
    modulo_young_pa REAL,
    poisson         REAL,
    condutiv_termica_w_mK REAL,
    calor_especifico_j_kgK REAL,
    resistencia_pa  REAL,
    observacoes     TEXT,
    criado_em       TEXT DEFAULT (datetime('now')),
    atualizado_em   TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ensaios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT UNIQUE NOT NULL,
    descricao   TEXT
);

CREATE TABLE IF NOT EXISTS results (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    material_id  INTEGER NOT NULL,
    ensaio       TEXT NOT NULL,
    metrica      TEXT NOT NULL,
    valor        REAL NOT NULL,
    unidade      TEXT,
    configuracao_json TEXT,            -- params do ensaio (rastreabilidade VVV)
    criado_em    TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS simulacoes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nome          TEXT NOT NULL,
    tipo          TEXT NOT NULL,       -- micro|meso|macro|envelhecimento|fabricacao
    config_json   TEXT,
    saida_json    TEXT,
    criado_em     TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_results_material ON results(material_id);
CREATE INDEX IF NOT EXISTS idx_results_ensaio   ON results(ensaio);
