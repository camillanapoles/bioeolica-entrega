// catalogo.js — Catálogo unificado de itens R&D (Parte 1 PM-15G + Parte 2 Savonius).
// Motor de fórmulas por TIPO DE COBRANÇA + custo médio + justificativa + export report.
// Mandato: orçamento REALISTA de lab P&D — ensaios repetidos (lotes×variações×re-análise
// pós-envelhecimento), make-vs-buy (CNC/microscopia/ultrassom só justificam aquisição se
// alta recorrência; esporádicos via Serviços TP PJ), entrega final = IMPLEMENTAÇÃO (obra civil
// + mão-de-obra + infra + equipamentos deixados no local: 5 comunidades + 1 protótipo).
// Depende de: edital-rules.js (window.EDITAL_RULES.rubricaPorId, fmtBRL). Independente do seed.

(function () {
  "use strict";

  // ---- Motor de fórmulas por tipo de cobrança ----------------------------
  // Cada item tem um tipo_cobranca; o total é calculado pela fórmula correspondente.
  var TIPOS_COBRANCA = {
    unitario: {
      label: "Unitário (preço × qtd)",
      // Padrão: componentes/insumos discretos (rotor, PMG, bateria, molde...).
      formula: function (it) { return num(it.preco_unitario) * num(it.quantidade); },
      campos: ["preco_unitario", "quantidade"]
    },
    fixo: {
      label: "Fixo (preço único)",
      // Aquisições/serviços one-shot (prensa, depósito INPI, obra por ambiente).
      formula: function (it) { return num(it.preco_unitario); },
      campos: ["preco_unitario"]
    },
    ensaio: {
      label: "Ensaio (preço × CP × nº ensaios)",
      // ENSAIOS REPETIDOS: lotes × variações × re-análises pós-envelhecimento.
      // quantidade = corpos-de-prova; ensaios = nº de rounds de análise.
      formula: function (it) { return num(it.preco_unitario) * num(it.quantidade) * num(it.ensaios); },
      campos: ["preco_unitario", "quantidade", "ensaios"]
    },
    tempo: {
      label: "Tempo (preço/h × horas)",
      // Serviços por hora: usinagem/fadiga/fluência/túnel via TP, mão-de-obra instalação.
      formula: function (it) { return num(it.preco_unitario) * num(it.duracao); },
      campos: ["preco_unitario", "duracao"]
    },
    mensal: {
      label: "Mensal (preço/mês × meses)",
      // Contratos recorrentes: capacitação comunitária, manutenção, datacenter.
      formula: function (it) { return num(it.preco_unitario) * num(it.quantidade); },
      // aqui "quantidade" = nº de meses (mantém schema uniforme).
      campos: ["preco_unitario", "quantidade"]
    }
  };

  function num(v) { var n = parseFloat(v); return isFinite(n) ? n : 0; }

  // Calcula o total de um item pela fórmula do seu tipo de cobrança.
  function calcularTotal(it) {
    var t = TIPOS_COBRANCA[it.tipo_cobranca] || TIPOS_COBRANCA.unitario;
    return t.formula(it);
  }

  // ---- Seed: catálogo R&D realista ---------------------------------------
  // categoria = id da rubrica do edital (bate com seed.js / edital-rules.js).
  // grupo = agregação lógica (fabricação, mecânica, microestrutura, end, envelhecimento,
  //   savonius-hardware, irrigacao, implementacao, pi, logistica).
  // custo_medio = referência de mercado (opcional); se preco > custo_medio → exige justificativa.
  var CATALOGO_SEED = {
    meta: {
      titulo: "Catálogo R&D — Bioeólica (PM-15G + Savonius)",
      base: "2026-06",
      nota: "Cálculo por TIPO DE COBRANÇA. Ensaios são REPETIDOS (lotes×variações×re-análise). " +
            "Esporádicos via TP PJ; recorrentes (CNC/microscopia/ultrassom) justificam aquisição. " +
            "Entrega final = IMPLEMENTAÇÃO: obra+mão-de-obra+infra+equip ficam no local (6 sistemas)."
    },
    itens: [
      // ============ PARTE 1 — PM-15G ============
      // --- Fabricação (Material de consumo) ---
      { id: "ct01", categoria: "material", grupo: "fabricacao", descricao: "Pasta celulósica (base papel machê)", tipo_cobranca: "unitario", unidade: "kg", preco_unitario: 8.5, quantidade: 120, custo_medio: 8.5, justificativa: "" },
      { id: "ct02", categoria: "material", grupo: "fabricacao", descricao: "PVA (ligante)", tipo_cobranca: "unitario", unidade: "L", preco_unitario: 14, quantidade: 80, custo_medio: 14, justificativa: "" },
      { id: "ct03", categoria: "material", grupo: "fabricacao", descricao: "Pó de grafite (15% vol)", tipo_cobranca: "unitario", unidade: "kg", preco_unitario: 95, quantidade: 40, custo_medio: 95, justificativa: "" },
      { id: "ct04", categoria: "material", grupo: "fabricacao", descricao: "Moldes/usinagem de moldes (recorrência alta → aquisição)", tipo_cobranca: "unitario", unidade: "conjunto", preco_unitario: 3800, quantidade: 4, custo_medio: 3500, justificativa: "Recorrência alta em 36m (lotes sucessivos); aquisição própria mais barata que TP repetido." },

      // --- Equipamento permanente (≥R$50K, recorrente) ---
      { id: "ct05", categoria: "equip", grupo: "fabricacao", descricao: "Prensa moldagem (pressão/temp controlada) — aquisição", tipo_cobranca: "fixo", unidade: "un", preco_unitario: 62000, custo_medio: 60000, justificativa: "Uso intensivo Parte1+2 em 36m; ≥R$50K livre (item 6.6.1). Justifica aquisição vs TP." },
      { id: "ct06", categoria: "equip", grupo: "fabricacao", descricao: "Microscópio óptico + bancada de usinagem/CNC (recorrência alta)", tipo_cobranca: "fixo", unidade: "kit", preco_unitario: 58000, custo_medio: 55000, justificativa: "Deep-tech: CNC e microscopia de uso diário em 36m justificam aquisição própria (mandato)." },

      // --- Ensaios mecânicos REPETIDOS via TP PJ (esporádico/hora-máquina) ---
      { id: "ct07", categoria: "tp_pj", grupo: "mecanica", descricao: "Tração ASTM D638 (CP × rounds)", tipo_cobranca: "ensaio", unidade: "CP", preco_unitario: 45, quantidade: 240, ensaios: 2, custo_medio: 45, justificativa: "240 CP (lotes×variações) × 2 rounds (inicial + pós-envelhecimento). TP PJ sem teto (6.5.2)." },
      { id: "ct08", categoria: "tp_pj", grupo: "mecanica", descricao: "Flexão ASTM D790", tipo_cobranca: "ensaio", unidade: "CP", preco_unitario: 48, quantidade: 180, ensaios: 2, custo_medio: 48, justificativa: "" },
      { id: "ct09", categoria: "tp_pj", grupo: "mecanica", descricao: "Izod ASTM D256", tipo_cobranca: "ensaio", unidade: "CP", preco_unitario: 55, quantidade: 150, ensaios: 2, custo_medio: 55, justificativa: "" },
      { id: "ct10", categoria: "tp_pj", grupo: "mecanica", descricao: "Shore D ASTM D2240", tipo_cobranca: "ensaio", unidade: "CP", preco_unitario: 18, quantidade: 150, ensaios: 2, custo_medio: 18, justificativa: "" },
      { id: "ct11", categoria: "tp_pj", grupo: "mecanica", descricao: "Fadiga ASTM D7774 (esporádico → TP)", tipo_cobranca: "ensaio", unidade: "CP", preco_unitario: 320, quantidade: 30, ensaios: 1, custo_medio: 320, justificativa: "Equip de fadiga caro e esporádico → TP PJ (make-vs-buy)." },
      { id: "ct12", categoria: "tp_pj", grupo: "mecanica", descricao: "Fluência (Norton) — hora-máquina", tipo_cobranca: "tempo", unidade: "h", preco_unitario: 180, duracao: 120, custo_medio: 180, justificativa: "Longa duração/caro → TP por hora." },

      // --- Microestrutura (esporádico → TP PJ) ---
      { id: "ct13", categoria: "tp_pj", grupo: "microestrutura", descricao: "MEV + EDS", tipo_cobranca: "ensaio", unidade: "amostra", preco_unitario: 220, quantidade: 60, ensaios: 2, custo_medio: 220, justificativa: "MEV esporádico → TP PJ." },
      { id: "ct14", categoria: "tp_pj", grupo: "microestrutura", descricao: "TGA", tipo_cobranca: "ensaio", unidade: "amostra", preco_unitario: 150, quantidade: 48, ensaios: 2, custo_medio: 150, justificativa: "" },
      { id: "ct15", categoria: "tp_pj", grupo: "microestrutura", descricao: "DSC", tipo_cobranca: "ensaio", unidade: "amostra", preco_unitario: 140, quantidade: 48, ensaios: 2, custo_medio: 140, justificativa: "" },
      { id: "ct16", categoria: "tp_pj", grupo: "microestrutura", descricao: "FTIR", tipo_cobranca: "ensaio", unidade: "amostra", preco_unitario: 95, quantidade: 48, ensaios: 2, custo_medio: 95, justificativa: "" },

      // --- END (ultrassom importante p/ materiais, mas esporádico → TP) ---
      { id: "ct17", categoria: "tp_pj", grupo: "end", descricao: "Ultrassom phased-array (END)", tipo_cobranca: "ensaio", unidade: "peça", preco_unitario: 280, quantidade: 40, ensaios: 2, custo_medio: 280, justificativa: "Ultrassom importante p/ lab de materiais, mas phased-array esporádico/caro → TP PJ." },
      { id: "ct18", categoria: "tp_pj", grupo: "end", descricao: "Termografia ativa", tipo_cobranca: "ensaio", unidade: "peça", preco_unitario: 160, quantidade: 40, ensaios: 2, custo_medio: 160, justificativa: "" },

      // --- Envelhecimento (tempo/câmara → TP PJ) ---
      { id: "ct19", categoria: "tp_pj", grupo: "envelhecimento", descricao: "UV acelerada (câmara)", tipo_cobranca: "ensaio", unidade: "lote", preco_unitario: 650, quantidade: 12, ensaios: 2, custo_medio: 650, justificativa: "" },
      { id: "ct20", categoria: "tp_pj", grupo: "envelhecimento", descricao: "Ciclagem térmica/umidade", tipo_cobranca: "ensaio", unidade: "lote", preco_unitario: 480, quantidade: 12, ensaios: 2, custo_medio: 480, justificativa: "" },
      { id: "ct21", categoria: "tp_pj", grupo: "envelhecimento", descricao: "Salt-spray", tipo_cobranca: "ensaio", unidade: "lote", preco_unitario: 720, quantidade: 8, ensaios: 2, custo_medio: 720, justificativa: "" },

      // --- PI/TALCX ---
      { id: "ct22", categoria: "tp_pj", grupo: "pi", descricao: "Depósito PI + TALCX (INPI)", tipo_cobranca: "fixo", unidade: "pacote", preco_unitario: 22000, custo_medio: 22000, justificativa: "Parte 1 do projeto: criação + depósito de PI/TALCX do compósito PM-15G." },

      // ============ PARTE 2 — Savonius + irrigação (6 sistemas no local) ============
      // --- Hardware por sistema (×6) ---
      { id: "ct23", categoria: "material", grupo: "savonius-hardware", descricao: "Rotor/pás PM-15G", tipo_cobranca: "unitario", unidade: "un", preco_unitario: 6000, quantidade: 6, custo_medio: 6000, justificativa: "" },
      { id: "ct24", categoria: "material", grupo: "savonius-hardware", descricao: "PMG (NdFeB + cobre)", tipo_cobranca: "unitario", unidade: "un", preco_unitario: 1380, quantidade: 6, custo_medio: 1380, justificativa: "" },
      { id: "ct25", categoria: "material", grupo: "savonius-hardware", descricao: "Torre treliça 10 m", tipo_cobranca: "unitario", unidade: "un", preco_unitario: 6450, quantidade: 6, custo_medio: 6450, justificativa: "" },
      { id: "ct26", categoria: "material", grupo: "savonius-hardware", descricao: "Banco de baterias 150 Ah", tipo_cobranca: "unitario", unidade: "conjunto", preco_unitario: 4100, quantidade: 6, custo_medio: 4100, justificativa: "" },
      { id: "ct27", categoria: "material", grupo: "savonius-hardware", descricao: "Instrumentação Arduino/GSM", tipo_cobranca: "unitario", unidade: "kit", preco_unitario: 2520, quantidade: 6, custo_medio: 2520, justificativa: "" },

      // --- Irrigação (item PERMITIDO <R$50K, 6.6.2) — fica no local ---
      { id: "ct28", categoria: "equip", grupo: "irrigacao", descricao: "Sistema de irrigação (bomba CC 24V + controlador + mangueira + reservatório + cisterna) — cada <R$50K", tipo_cobranca: "unitario", unidade: "sistema", preco_unitario: 15300, quantidade: 6, custo_medio: 15300, justificativa: "Item 6.6.2 permitido <R$50K; 6 sistemas deixados nas comunidades (entrega = implementação)." },

      // --- IMPLEMENTAÇÃO: obra civil + mão-de-obra + infra (×6 ambientes, ficam no local) ---
      { id: "ct29", categoria: "obras", grupo: "implementacao", descricao: "Fundação + obra civil por ambiente (≤R$392.952/ambiente, ≤10%)", tipo_cobranca: "fixo", unidade: "ambiente", preco_unitario: 47000, quantidade: 6, custo_medio: 47000, justificativa: "Entrega=implementação: obra civil por ambiente (Dec.12.807/2025); 6 sistemas no campo." },
      { id: "ct30", categoria: "tp_pj", grupo: "implementacao", descricao: "Mão-de-obra instalação + cabeamento (por sistema)", tipo_cobranca: "tempo", unidade: "h", preco_unitario: 65, duracao: 360, custo_medio: 65, justificativa: "Equipe de campo × 6 sites; mandato: custo de mão-de-obra de instalação." },
      { id: "ct31", categoria: "material", grupo: "implementacao", descricao: "Cabeamento/condutos/acessórios infra", tipo_cobranca: "unitario", unidade: "site", preco_unitario: 3650, quantidade: 6, custo_medio: 3650, justificativa: "" },

      // --- Operação/capacitação + logística ---
      { id: "ct32", categoria: "tp_pj", grupo: "capacitacao", descricao: "Capacitação comunitária + ATER (manutenção)", tipo_cobranca: "mensal", unidade: "mês", preco_unitario: 4200, quantidade: 30, custo_medio: 4200, justificativa: "30 meses de ATER nas 5 comunidades (sustentabilidade pós-entrega)." },
      { id: "ct33", categoria: "tp_pj", grupo: "logistica", descricao: "Túnel de vento + banco de carga (ensaio rotor)", tipo_cobranca: "ensaio", unidade: "ensaio", preco_unitario: 1200, quantidade: 18, ensaios: 1, custo_medio: 1200, justificativa: "Ensaios do rotor em túnel; esporádico → TP PJ." },
      { id: "ct34", categoria: "operacional", grupo: "logistica", descricao: "Fretes/deslocamentos campo", tipo_cobranca: "fixo", unidade: "pacote", preco_unitario: 28000, custo_medio: 28000, justificativa: "" }
    ]
  };

  // ---- Helpers de agregação ---------------------------------------------
  function itensPorCategoria(itens, catId) {
    return itens.filter(function (it) { return it.categoria === catId; });
  }
  function totalCategoria(itens, catId) {
    return itensPorCategoria(itens, catId).reduce(function (s, it) { return s + calcularTotal(it); }, 0);
  }
  function totalGeral(itens) {
    return itens.reduce(function (s, it) { return s + calcularTotal(it); }, 0);
  }
  // Itens cujo preço supera o custo médio de mercado → exigem justificativa.
  function itensAcimaCustoMedio(itens) {
    return itens.filter(function (it) {
      return it.custo_medio && num(it.preco_unitario) > num(it.custo_medio) && !it.justificativa;
    });
  }

  // ---- Export para window -----------------------------------------------
  window.CATALOGO = {
    TIPOS_COBRANCA: TIPOS_COBRANCA,
    SEED: CATALOGO_SEED,
    calcularTotal: calcularTotal,
    itensPorCategoria: itensPorCategoria,
    totalCategoria: totalCategoria,
    totalGeral: totalGeral,
    itensAcimaCustoMedio: itensAcimaCustoMedio
  };
})();
