// edital-rules.js — Regras do edital FINEP AgriFam-ICT 2026 para validação ao vivo.
// Fonte: memory/finep-edital-regras.md + @edital/extracao/latest/EDITAL_RET.

window.EDITAL_RULES = {
  faixa_min: 1000000,
  faixa_max: 7000000,
  duracao_meses_max: 36,

  // Tetos por rubrica (% sobre o valor total da proposta).
  caps: {
    pessoal:    { pct: 0.30, item: "6.5.5", label: "≤30%" },
    bolsas:     { pct: 0.30, item: "6.5.7", label: "≤30%" },
    operacional:{ pct: 0.05, item: "6.5.3", label: "=5% (exato)", exacto: true },
    diarias:    { pct: 0.05, item: "6.5.6", label: "≤5%" },
    passagens:  { pct: 0.05, item: "6.5.6", label: "≤5%" },
    obras:      { pct: 0.10, item: "6.6.3", label: "≤10% e ≤R$392.952,63/ambiente", teto_ambiente: 392952.63 },
    tp_pj:      { pct: null, item: "6.5.2", label: "livre" },
    material:   { pct: null, item: "6.5.1", label: "livre" },
    equip:      { pct: null, item: "6.6.1/6.6.2", label: "≥R$50K livre; <R$50K só lista" }
  },

  // Regra de TIPO por RUBRICA: quais tipos são PROIBIDOS em cada rubrica.
  // Ex.: "Material de consumo" NÃO pode conter mão-de-obra (deve ir p/ Pessoal/Bolsas/TP PJ).
  tipo_por_rubrica: {
    material: {
      proibe: ["mao-de-obra", "diaria", "passagem", "obra", "operacional"],
      motivo: "Material de consumo [6.5.1] é insumo/consumível — mão-de-obra vai p/ Pessoal/Bolsas/TP PJ."
    },
    tp_pj: {
      proibe: ["diaria", "passagem"],
      motivo: "Serviços TP PJ [6.5.2] é serviço de terceiro — diárias/passagens têm rubrica própria [6.5.6]."
    },
    equip: {
      proibe: ["mao-de-obra", "diaria", "passagem", "operacional", "insumo"],
      motivo: "Equipamento permanente [6.6] é bem capital — não admite mão-de-obra nem insumo."
    },
    obras: {
      proibe: ["mao-de-obra-direta", "diaria", "passagem", "insumo-pesquisa"],
      motivo: "Obras [6.6.3] é construção civil — mão-de-obra própria da obra é parte do custo de obra."
    },
    pessoal: {
      proibe: ["insumo", "equipamento-menor", "equipamento-maior", "obra", "diaria", "passagem", "servico"],
      motivo: "Pessoal [6.5.5] é mão-de-obra própria — bens/serviços vão p/ rubrica própria."
    },
    bolsas: {
      proibe: ["insumo", "equipamento-menor", "equipamento-maior", "obra", "diaria", "passagem", "servico"],
      motivo: "Bolsas [6.5.7] é mão-de-obra via bolsa — bens/serviços vão p/ rubrica própria."
    },
    diarias: {
      proibe: ["mao-de-obra", "insumo", "equipamento-menor", "equipamento-maior", "obra", "servico"],
      motivo: "Diárias [6.5.6] é auxílio financeiro p/ despesas de alimentação/hospedagem — não é bem/serviço."
    },
    passagens: {
      proibe: ["mao-de-obra", "insumo", "equipamento-menor", "equipamento-maior", "obra", "servico"],
      motivo: "Passagens [6.5.6] é tarifa de transporte — não é bem/serviço."
    },
    operacional: {
      proibe: ["mao-de-obra", "equipamento-maior", "obra"],
      motivo: "Desp. operac. [6.5.3] é custo de administração (=5%) — não é capital nem mão-de-obra de P&D."
    }
  },

  // Lista de equipamentos <R$50K permitidos (item 6.6.2).
  equip_menor_permitido: [
    "nobreak", "chiller", "ar-condicionado", "ac", "casa de vegetação",
    "sistema de irrigação", "irrigação", "no-break"
  ],

  // Sistema composto (item 2.1.24): palavra-gatilho para alertar empacotamento.
  composto_gatilhos: ["gerador", "savonius", "rotor", "pmg", "torre"]
};

// ---- Motor de validação -------------------------------------------------

// Formata R$ no padrão brasileiro.
window.fmtBRL = function (v) {
  return "R$ " + Number(v || 0).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

// Soma uma rubrica.
window.somaRubrica = function (rubrica) {
  return rubrica.itens.reduce(function (acc, it) { return acc + (Number(it.valor) || 0); }, 0);
};

// Soma total da proposta.
window.somaTotal = function (seed) {
  return seed.rubricas.reduce(function (acc, r) { return acc + window.somaRubrica(r); }, 0);
};

// Valida o TIPO de um item dentro de sua rubrica (regra de categoria).
window.validarTipoItem = function (rubricaId, tipo) {
  var regra = window.EDITAL_RULES.tipo_por_rubrica[rubricaId];
  if (!regra) return { ok: true };
  if (regra.proibe.indexOf(tipo) >= 0) {
    return { ok: false, motivo: "Tipo '" + tipo + "' proibido nesta rubrica. " + regra.motivo };
  }
  return { ok: true };
};

// Valida um item isoladamente (tipo + equipamento-menor permitido + composto).
window.validarItem = function (rubrica, item) {
  var achados = [];

  // 1) Regra de categoria/tipo.
  var tv = window.validarTipoItem(rubrica.id, item.tipo);
  if (!tv.ok) achados.push(tv.motivo);

  // 2) Equipamento <R$50K só da lista permitida [6.6.2].
  if (rubrica.id === "equip" && item.tipo === "equipamento-menor" && Number(item.valor) < 50000) {
    var desc = (item.descricao || "").toLowerCase();
    var permitido = window.EDITAL_RULES.equip_menor_permitido.some(function (k) {
      return desc.indexOf(k) >= 0;
    });
    if (!permitido) {
      achados.push("Equip <R$50K fora da lista permitida [6.6.2] (nobreak/chiller/AC/casa veg./irrigação).");
    }
  }

  // 3) Alerta de sistema composto [2.1.24] se desempacotado.
  if (rubrica.id === "equip") {
    var descUp = (item.descricao || "").toLowerCase();
    var ehComposto = window.EDITAL_RULES.composto_gatilhos.some(function (k) { return descUp.indexOf(k) >= 0; });
    if (ehComposto && item.tipo !== "equipamento-maior") {
      achados.push("Item de sistema composto [2.1.24] deve ser empacotado como item único (≥R$50K).");
    }
  }

  return { ok: achados.length === 0, motivos: achados };
};

// Valida uma rubrica contra o teto percentual e o teto por ambiente.
window.validarRubrica = function (rubrica, total) {
  var cap = window.EDITAL_RULES.caps[rubrica.id];
  var valor = window.somaRubrica(rubrica);
  var res = { ok: true, valor: valor, pct: total > 0 ? valor / total : 0, motivos: [], cap: cap };
  if (!cap) return res;

  // Teto percentual.
  if (cap.pct !== null) {
    res.teto_valor = total * cap.pct;
    if (cap.exacto) {
      // Operacional deve ser exatamente 5% (tolerância de arredondamento R$1).
      if (Math.abs(valor - res.teto_valor) > 1) {
        res.ok = false;
        res.motivos.push("Operacional deve ser EXATAMENTE 5% (=R$ " + res.teto_valor.toLocaleString("pt-BR") + ").");
      }
    } else if (valor > res.teto_valor + 0.01) {
      res.ok = false;
      res.motivos.push("Ultrapassa teto " + cap.label + " (máx " + window.fmtBRL(res.teto_valor) + ").");
    }
  }

  // Teto por ambiente (obras).
  if (cap.teto_ambiente) {
    var ambientes = rubrica.itens.filter(function (it) { return /ambiente/i.test(it.descricao || ""); });
    ambientes.forEach(function (it) {
      if ((Number(it.valor) || 0) > cap.teto_ambiente) {
        res.ok = false;
        res.motivos.push("Ambiente '" + it.descricao + "' > R$392.952,63 (Dec. 12.807/2025).");
      }
    });
  }

  return res;
};

// Validação global da proposta (faixa + duração + todas as rubricas + R4).
window.validarProposta = function (seed) {
  var total = window.somaTotal(seed);
  var out = { total: total, faixa_ok: true, duracao_ok: true, rubricas: {}, globais: [] };

  if (total < window.EDITAL_RULES.faixa_min) {
    out.faixa_ok = false;
    out.globais.push("Total abaixo do piso da faixa (mín " + window.fmtBRL(window.EDITAL_RULES.faixa_min) + ").");
  }
  if (total > window.EDITAL_RULES.faixa_max + 0.01) {
    out.faixa_ok = false;
    out.globais.push("Total acima do teto da faixa (máx " + window.fmtBRL(window.EDITAL_RULES.faixa_max) + ").");
  }

  if (seed.meta.duracao_meses > window.EDITAL_RULES.duracao_meses_max) {
    out.duracao_ok = false;
    out.globais.push("Duração > 36 meses [item 9.1].");
  }

  seed.rubricas.forEach(function (r) {
    out.rubricas[r.id] = window.validarRubrica(r, total);
  });

  // Valor inabilitado: soma dos valores em itens NÃO aprovados (proxy R4).
  var inabilitado = 0;
  seed.rubricas.forEach(function (r) {
    r.itens.forEach(function (it) {
      var iv = window.validarItem(r, it);
      if (!iv.ok) inabilitado += Number(it.valor) || 0;
    });
    var rv = out.rubricas[r.id];
    if (!rv.ok) inabilitado += rv.valor; // rubrica inteira fora do teto conta como inabilitado
  });
  out.valor_inabilitado = inabilitado;
  out.pct_inabilitado = total > 0 ? inabilitado / total : 0;
  out.r4_eliminacao = out.pct_inabilitado > 0.30;

  return out;
};
