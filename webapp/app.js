// app.js — Orçamento FINEP AgriFam-ICT 2026: CRUD + SQLite (sql.js WASM) + validação ao vivo.
// Persistência: SQLite em memória → exportado binário → localStorage (chave "orc_finep_v2").
// Depende de: seed.js (window.ORCAMENTO_SEED), edital-rules.js (window.* validadores).

(function () {
  "use strict";

  var SQL_JS_URL = "https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.10.3/sql-wasm.js";
  var SQL_JS_WASM = "https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.10.3/sql-wasm.wasm";
  var STORAGE_KEY = "orc_finep_v2";
  var db = null;       // instância sql.js
  var SQL = null;      // construtor sql.js
  var seed = null;     // estado corrente em memória (espelho do SQLite)

  // ---- Bootstrap ---------------------------------------------------------
  document.addEventListener("DOMContentLoaded", function () {
    carregarSqlJs().then(function () {
      return restaurarOuInit();
    }).then(function () {
      vincularUI();
      renderTudo();
    }).catch(function (err) {
      var el = document.getElementById("status");
      if (el) el.textContent = "Erro de init: " + (err && err.message ? err.message : err);
    });
  });

  // Carrega sql.js dinamicamente.
  function carregarSqlJs() {
    if (window.initSqlJs) return Promise.resolve();
    return new Promise(function (resolve, reject) {
      var s = document.createElement("script");
      s.src = SQL_JS_URL;
      s.onload = resolve;
      s.onerror = function () { reject(new Error("falha ao carregar sql.js")); };
      document.head.appendChild(s);
    }).then(function () {
      return window.initSqlJs({ locateFile: function () { return SQL_JS_WASM; } });
    }).then(function (sql) { SQL = sql; });
  }

  // ---- SQLite schema + load ---------------------------------------------
  function initDb() {
    db = new SQL.Database();
    db.run(
      "CREATE TABLE IF NOT EXISTS rubricas (" +
      "  id TEXT PRIMARY KEY, nome TEXT, item_edital TEXT," +
      "  teto_pct REAL, teto_ambiente REAL, teto_exacto INTEGER);"
    );
    db.run(
      "CREATE TABLE IF NOT EXISTS itens (" +
      "  id TEXT PRIMARY KEY, rubrica_id TEXT, descricao TEXT," +
      "  valor REAL, tipo TEXT," +
      "  FOREIGN KEY(rubrica_id) REFERENCES rubricas(id));"
    );
    db.run("CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT);");
  }

  function popularDeSeed(s) {
    db.run("DELETE FROM itens; DELETE FROM rubricas; DELETE FROM meta;");
    var mk = db.prepare("INSERT OR REPLACE INTO meta(k,v) VALUES (?,?);");
    Object.keys(s.meta).forEach(function (k) { mk.run([k, String(s.meta[k])]); }); mk.free();
    var mr = db.prepare(
      "INSERT OR REPLACE INTO rubricas(id,nome,item_edital,teto_pct,teto_ambiente,teto_exacto) VALUES (?,?,?,?,?,?);"
    );
    s.rubricas.forEach(function (r) {
      mr.run([r.id, r.nome, r.item_edital, r.teto_pct == null ? null : r.teto_pct,
              r.teto_ambiente == null ? null : r.teto_ambiente, r.teto_exacto ? 1 : 0]);
    }); mr.free();
    var mi = db.prepare("INSERT OR REPLACE INTO itens(id,rubrica_id,descricao,valor,tipo) VALUES (?,?,?,?,?);");
    s.rubricas.forEach(function (r) {
      r.itens.forEach(function (it) { mi.run([it.id, r.id, it.descricao, it.valor, it.tipo]); });
    }); mi.free();
  }

  // Lê o SQLite corrente e reconstrói o objeto `seed` em memória.
  function lerDbParaSeed() {
    var meta = {};
    db.exec("SELECT k,v FROM meta;")[0].values.forEach(function (row) { meta[row[0]] = row[1]; });
    meta.faixa_min = Number(meta.faixa_min); meta.faixa_max = Number(meta.faixa_max);
    meta.duracao_meses = Number(meta.duracao_meses);
    var rubricas = db.exec("SELECT * FROM rubricas;")[0];
    var itens = db.exec("SELECT * FROM itens;")[0];
    var colsR = rubricas.columns, rowsR = rubricas.values;
    var colsI = itens.columns, rowsI = itens.values;
    var out = { meta: meta, rubricas: [] };
    var byId = {};
    rowsR.forEach(function (row) {
      var r = rowToObj(colsR, row);
      r.teto_pct = r.teto_pct == null ? null : Number(r.teto_pct);
      r.teto_ambiente = r.teto_ambiente == null ? null : Number(r.teto_ambiente);
      r.teto_exacto = !!r.teto_exacto;
      r.itens = [];
      byId[r.id] = r; out.rubricas.push(r);
    });
    rowsI.forEach(function (row) {
      var it = rowToObj(colsI, row); it.valor = Number(it.valor);
      if (byId[it.rubrica_id]) byId[it.rubrica_id].itens.push(it);
    });
    return out;
  }

  function rowToObj(cols, row) {
    var o = {}; cols.forEach(function (c, i) { o[c] = row[i]; }); return o;
  }

  // Persiste binário SQLite no localStorage.
  function persistir() {
    try {
      var data = db.export();           // Uint8Array
      var str = uint8ToBase64(data);
      localStorage.setItem(STORAGE_KEY, str);
      setStatus("Salvo (SQLite em localStorage, " + (data.length / 1024).toFixed(1) + " KB).");
    } catch (e) { setStatus("Falha ao salvar: " + e.message); }
  }

  function restaurarOuInit() {
    initDb();
    var salvo = localStorage.getItem(STORAGE_KEY);
    if (salvo) {
      try {
        var data = base64ToUint8(salvo);
        db = new SQL.Database(data);
        seed = lerDbParaSeed();
        setStatus("Restaurado de localStorage.");
        return Promise.resolve();
      } catch (e) { console.warn("restore falhou, reseed", e); }
    }
    seed = JSON.parse(JSON.stringify(window.ORCAMENTO_SEED));
    popularDeSeed(seed);
    persistir();
    return Promise.resolve();
  }

  // ---- CRUD --------------------------------------------------------------
  function upsertItem(rubricaId, item) {
    var stmt = db.prepare(
      "INSERT OR REPLACE INTO itens(id,rubrica_id,descricao,valor,tipo) VALUES (?,?,?,?,?);"
    );
    stmt.run([item.id, rubricaId, item.descricao, Number(item.valor) || 0, item.tipo]); stmt.free();
  }
  function delItem(id) {
    var s = db.prepare("DELETE FROM itens WHERE id=?;"); s.run([id]); s.free();
  }
  function novoId(prefixo) {
    return prefixo + "_" + Date.now().toString(36) + Math.floor(Math.random() * 1e4).toString(36);
  }

  // ---- UI bind -----------------------------------------------------------
  function vincularUI() {
    document.getElementById("btnReset").onclick = function () {
      if (!confirm("Descartar edições e re-carregar o orçamento v2.0 original?")) return;
      seed = JSON.parse(JSON.stringify(window.ORCAMENTO_SEED));
      popularDeSeed(seed); persistir(); renderTudo();
    };
    document.getElementById("btnExport").onclick = exportarJSON;
    document.getElementById("btnImport").onclick = function () {
      document.getElementById("fileImport").click();
    };
    document.getElementById("fileImport").onchange = importarJSON;
    document.getElementById("btnReport").onclick = toggleReport;
    document.getElementById("btnCatalogo").onclick = toggleCatalogo;
    document.getElementById("btnDownloadSqlite").onclick = baixarSqlite;
  }

  // ---- Render ------------------------------------------------------------
  function renderTudo() { renderMeta(); renderTabela(); renderTotais(); }

  function renderMeta() {
    var m = seed.meta;
    document.getElementById("metaProj").textContent = m.projeto;
    document.getElementById("metaVer").textContent = m.versao;
    document.getElementById("metaData").textContent = m.data_base;
  }

  function renderTabela() {
    var cont = document.getElementById("tabela");
    cont.innerHTML = "";
    seed.rubricas.forEach(function (r) {
      var total = window.somaTotal(seed);
      var rv = window.validarRubrica(r, total);

      var sec = document.createElement("section");
      sec.className = "rubrica" + (rv.ok ? "" : " ruim");

      var head = document.createElement("div");
      head.className = "rubrica-head";
      var capLabel = rv.cap ? (" — teto " + rv.cap.label + " [item " + rv.cap.item + "]") : " — livre";
      var pctTxt = rv.cap && rv.cap.pct !== null
        ? " (" + (rv.pct * 100).toFixed(1) + "%, máx " + window.fmtBRL(total * rv.cap.pct) + ")"
        : " (" + (rv.pct * 100).toFixed(1) + "%)";
      head.innerHTML = "<h3>" + r.nome + capLabel + "</h3>" +
        "<div class=\"rubrica-totais\">Subtotal: <b>" + window.fmtBRL(rv.valor) + "</b>" + pctTxt +
        (rv.ok ? "" : " — <span class=\"tagNAO\">NÃO APROVADO</span>") + "</div>";
      sec.appendChild(head);

      var tbl = document.createElement("table");
      tbl.innerHTML =
        "<thead><tr>" +
        "<th>Item</th><th>Tipo</th><th>Valor</th><th>Status</th><th>Motivo / Valor máximo</th><th></th>" +
        "</tr></thead><tbody></tbody>";
      var body = tbl.querySelector("tbody");

      r.itens.forEach(function (it) {
        var iv = window.validarItem(r, it);
        var tr = document.createElement("tr");
        tr.className = iv.ok ? "" : "linhaRuim";

        var tdDesc = cel(it.descricao, true, it.id, "descricao", r.id);
        var tdTipo = celTipo(it.tipo, it.id, r.id);
        var tdVal = celValor(it.valor, it.id, r.id);

        var tdStatus = document.createElement("td");
        tdStatus.className = "status";
        tdStatus.innerHTML = iv.ok
          ? "<span class=\"tagOK\">APROVADO</span>"
          : "<span class=\"tagNAO\">NÃO APROVADO</span>";

        var tdMot = document.createElement("td");
        tdMot.className = "motivo";
        var txts = [];
        if (!iv.ok) txts = txts.concat(iv.motivos);
        if (!rv.ok && rv.cap && rv.cap.pct !== null && !rv.cap.exacto) {
          txts.push("Teto da rubrica: " + window.fmtBRL(total * rv.cap.pct) + ".");
        }
        if (rv.cap && rv.cap.teto_ambiente) txts.push("Teto/ambiente: R$392.952,63.");
        tdMot.textContent = txts.join(" ");

        var tdAcao = document.createElement("td");
        var btn = document.createElement("button");
        btn.textContent = "✕"; btn.title = "Excluir item";
        btn.onclick = function () {
          if (!confirm("Excluir '" + it.descricao + "'?")) return;
          delItem(it.id); seed = lerDbParaSeed(); persistir(); renderTudo();
        };
        tdAcao.appendChild(btn);

        tr.appendChild(tdDesc); tr.appendChild(tdTipo); tr.appendChild(tdVal);
        tr.appendChild(tdStatus); tr.appendChild(tdMot); tr.appendChild(tdAcao);
        body.appendChild(tr);
      });

      // Linha "adicionar item"
      var trAdd = document.createElement("tr");
      trAdd.className = "linhaAdd";
      trAdd.innerHTML =
        "<td><input type='text' placeholder='Novo item...' data-add='descricao'></td>" +
        "<td><select data-add='tipo'>" + optionsTipo() + "</select></td>" +
        "<td><input type='number' min='0' step='0.01' placeholder='0,00' data-add='valor'></td>" +
        "<td></td><td></td><td><button>＋ Add</button></td>";
      trAdd.querySelector("button").onclick = function () {
        var desc = trAdd.querySelector("[data-add='descricao']").value.trim();
        var tipo = trAdd.querySelector("[data-add='tipo']").value;
        var val = parseFloat(trAdd.querySelector("[data-add='valor']").value) || 0;
        if (!desc) { alert("Descreva o item."); return; }
        var it = { id: novoId(r.id), descricao: desc, valor: val, tipo: tipo };
        upsertItem(r.id, it); seed = lerDbParaSeed(); persistir(); renderTudo();
      };
      body.appendChild(trAdd);

      sec.appendChild(tbl);
      cont.appendChild(sec);
    });
  }

  function optionsTipo(sel) {
    var tipos = ["mao-de-obra", "servico", "insumo", "equipamento-menor", "equipamento-maior",
                 "obra", "operacional", "diaria", "passagem"];
    return tipos.map(function (t) {
      return "<option value='" + t + "'" + (t === sel ? " selected" : "") + ">" + t + "</option>";
    }).join("");
  }

  // célula editável de texto
  function cel(val, editavel, id, campo, rubricaId) {
    var td = document.createElement("td");
    var inp = document.createElement("input");
    inp.type = "text"; inp.value = val;
    inp.onchange = function () {
      var novo = inp.value;
      var s = db.prepare("UPDATE itens SET " + campo + "=? WHERE id=?;");
      s.run([novo, id]); s.free();
      seed = lerDbParaSeed(); persistir(); renderTudo();
    };
    td.appendChild(inp); return td;
  }
  function celValor(val, id, rubricaId) {
    var td = document.createElement("td");
    var inp = document.createElement("input");
    inp.type = "number"; inp.min = "0"; inp.step = "0.01"; inp.value = val;
    inp.onchange = function () {
      var v = parseFloat(inp.value) || 0;
      var s = db.prepare("UPDATE itens SET valor=? WHERE id=?;"); s.run([v, id]); s.free();
      seed = lerDbParaSeed(); persistir(); renderTudo();
    };
    td.appendChild(inp); return td;
  }
  function celTipo(val, id, rubricaId) {
    var td = document.createElement("td");
    var sel = document.createElement("select");
    sel.innerHTML = optionsTipo(val);
    sel.onchange = function () {
      var s = db.prepare("UPDATE itens SET tipo=? WHERE id=?;"); s.run([sel.value, id]); s.free();
      seed = lerDbParaSeed(); persistir(); renderTudo();
    };
    td.appendChild(sel); return td;
  }

  function renderTotais() {
    var v = window.validarProposta(seed);
    var box = document.getElementById("totais");
    var r4 = v.r4_eliminacao
      ? "<span class='tagNAO'>⚠ R4 — VALOR INABILITADO > 30% ⇒ ELIMINAÇÃO [11.2.2]</span>"
      : "<span class='tagOK'>R4 OK — valor inabilitado " + (v.pct_inabilitado * 100).toFixed(1) + "% (≤30%)</span>";
    var faixa = v.faixa_ok
      ? "<span class='tagOK'>Faixa R$1M–R$7M OK</span>"
      : "<span class='tagNAO'>Faixa violada</span>";
    box.innerHTML =
      "<div><b>TOTAL:</b> <span class='big'>" + window.fmtBRL(v.total) + "</span></div>" +
      "<div>" + faixa + " " + r4 + "</div>" +
      "<div class='resumo'>" + resumoRubricas(v) + "</div>" +
      (v.globais.length ? "<div class='globais'>" + v.globais.join("<br>") + "</div>" : "");
  }

  function resumoRubricas(v) {
    return seed.rubricas.map(function (r) {
      var rv = v.rubricas[r.id];
      var cor = rv.ok ? "ok" : "nao";
      var pct = (rv.pct * 100).toFixed(1) + "%";
      return "<span class='pill " + cor + "'>" + r.nome + ": " + window.fmtBRL(rv.valor) + " (" + pct + ")</span>";
    }).join(" ");
  }

  // ---- Catálogo R&D ------------------------------------------------------
  function toggleCatalogo() {
    var box = document.getElementById("catalogoView");
    var report = document.getElementById("report");
    if (report) report.style.display = "none";
    if (box.style.display === "block") { box.style.display = "none"; return; }
    box.style.display = "block";
    box.innerHTML = "";
    box.appendChild(renderCatalogoHead());
    box.appendChild(renderCatalogoTable());
    box.appendChild(renderCatalogoAlertas());
    box.appendChild(renderCatalogoBotoes());
  }

  function renderCatalogoHead() {
    var C = window.CATALOGO;
    var m = C.SEED.meta;
    var total = C.totalGeral(C.SEED.itens);
    var div = document.createElement("div");
    div.style.cssText = "background:#fff;border:1px solid var(--line);border-radius:8px;padding:12px 14px;margin-bottom:12px";
    div.innerHTML =
      "<b>" + m.titulo + "</b> <span class='meta-row'>· base " + m.base + "</span><br>" +
      "<span class='meta-row'>" + m.nota + "</span><br>" +
      "<b>TOTAL CATÁLOGO:</b> <span class='big' style='font-size:18px'>" + window.fmtBRL(total) + "</span>";
    return div;
  }

  function renderCatalogoTable() {
    var C = window.CATALOGO;
    var itens = C.SEED.itens;
    var porGrupo = {};
    itens.forEach(function (it) {
      (porGrupo[it.grupo] = porGrupo[it.grupo] || []).push(it);
    });
    var tbl = document.createElement("table");
    tbl.innerHTML =
      "<thead><tr>" +
      "<th>Item</th><th>Categoria</th><th>Grupo</th><th>Tipo cobrança</th>" +
      "<th>Preço unit.</th><th>Qtd/CP</th><th>Ensaios/Duração</th>" +
      "<th>Custo médio</th><th>Total</th><th>Justificativa</th>" +
      "</tr></thead><tbody></tbody>";
    var body = tbl.querySelector("tbody");
    Object.keys(porGrupo).forEach(function (g) {
      porGrupo[g].forEach(function (it) {
        var total = C.calcularTotal(it);
        var acima = it.custo_medio && parseFloat(it.preco_unitario) > parseFloat(it.custo_medio) && !it.justificativa;
        var tr = document.createElement("tr");
        if (acima) tr.className = "linhaRuim";
        var tcampos = "";
        if (it.tipo_cobranca === "ensaio") tcampos = it.ensaios + " rounds";
        else if (it.tipo_cobranca === "tempo") tcampos = it.duracao + " h";
        else if (it.tipo_cobranca === "mensal") tcampos = it.quantidade + " meses";
        else tcampos = "—";
        tr.innerHTML =
          "<td>" + it.descricao + "</td>" +
          "<td><code>" + it.categoria + "</code></td>" +
          "<td>" + it.grupo + "</td>" +
          "<td><code>" + it.tipo_cobranca + "</code><br><small style='color:var(--muted)'>" + (C.TIPOS_COBRANCA[it.tipo_cobranca] || {}).label + "</small></td>" +
          "<td style='text-align:right'>" + window.fmtBRL(it.preco_unitario) + "</td>" +
          "<td style='text-align:right'>" + (it.quantidade || "—") + " " + (it.unidade || "") + "</td>" +
          "<td style='text-align:right'>" + tcampos + "</td>" +
          "<td style='text-align:right'>" + (it.custo_medio ? window.fmtBRL(it.custo_medio) : "—") + "</td>" +
          "<td style='text-align:right'><b>" + window.fmtBRL(total) + "</b></td>" +
          "<td class='motivo'>" + (it.justificativa || (acima ? "⚠ acima do custo médio sem justificativa" : "")) + "</td>";
        body.appendChild(tr);
      });
    });
    return tbl;
  }

  function renderCatalogoAlertas() {
    var C = window.CATALOGO;
    var div = document.createElement("div");
    div.style.cssText = "margin-top:10px;font-size:12px";
    var alertas = C.itensAcimaCustoMedio(C.SEED.itens);
    var porCat = {};
    C.SEED.itens.forEach(function (it) {
      var t = C.calcularTotal(it);
      porCat[it.categoria] = (porCat[it.categoria] || 0) + t;
    });
    var linhas = ["<b>Resumo por categoria (rubrica):</b>"];
    Object.keys(porCat).forEach(function (c) {
      linhas.push("· <code>" + c + "</code>: " + window.fmtBRL(porCat[c]));
    });
    if (alertas.length) {
      linhas.push("<br><b style='color:var(--nao)'>⚠ " + alertas.length + " item(ns) acima do custo médio sem justificativa:</b>");
      alertas.forEach(function (it) { linhas.push("· " + it.descricao + " (" + window.fmtBRL(it.preco_unitario) + " > " + window.fmtBRL(it.custo_medio) + ")"); });
    } else {
      linhas.push("<br><span class='tagOK'>✓ Todo item acima do custo médio tem justificativa.</span>");
    }
    div.innerHTML = linhas.join("<br>");
    return div;
  }

  function renderCatalogoBotoes() {
    var wrap = document.createElement("div");
    wrap.style.cssText = "margin-top:12px;display:flex;gap:8px";
    var bMd = document.createElement("button");
    bMd.textContent = "📄 Exportar Relatório (Markdown)";
    bMd.onclick = function () {
      var blob = new Blob([gerarRelatorioCatalogo()], { type: "text/markdown" });
      download(blob, "catalogo-rd-bioeolica.md");
    };
    var bJson = document.createElement("button");
    bJson.textContent = "⬇ Exportar JSON";
    bJson.onclick = function () {
      var blob = new Blob([JSON.stringify(window.CATALOGO.SEED, null, 2)], { type: "application/json" });
      download(blob, "catalogo-rd-bioeolica.json");
    };
    wrap.appendChild(bMd); wrap.appendChild(bJson);
    return wrap;
  }

  function gerarRelatorioCatalogo() {
    var C = window.CATALOGO;
    var itens = C.SEED.itens;
    var m = C.SEED.meta;
    var total = C.totalGeral(itens);
    var L = [];
    L.push("# " + m.titulo);
    L.push("_Base " + m.base + " — " + m.nota + "_");
    L.push("");
    L.push("**Total do catálogo:** " + window.fmtBRL(total));
    L.push("");
    L.push("| Item | Categoria | Grupo | Tipo | Preço unit. | Qtd | Ensaios/Duração | Custo médio | Total | Justificativa |");
    L.push("|---|---|---|---|---:|---:|---:|---:|---:|---|");
    itens.forEach(function (it) {
      var t = C.calcularTotal(it);
      var extra = it.tipo_cobranca === "ensaio" ? it.ensaios + " rnd"
        : it.tipo_cobranca === "tempo" ? it.duracao + " h"
        : it.tipo_cobranca === "mensal" ? it.quantidade + " mêses" : "—";
      L.push("| " + it.descricao + " | " + it.categoria + " | " + it.grupo + " | " + it.tipo_cobranca +
        " | " + window.fmtBRL(it.preco_unitario) + " | " + (it.quantidade || "—") + " " + (it.unidade || "") +
        " | " + extra + " | " + (it.custo_medio ? window.fmtBRL(it.custo_medio) : "—") +
        " | " + window.fmtBRL(t) + " | " + (it.justificativa || "") + " |");
    });
    L.push("");
    L.push("## Resumo por rubrica");
    var porCat = {};
    itens.forEach(function (it) { var t = C.calcularTotal(it); porCat[it.categoria] = (porCat[it.categoria] || 0) + t; });
    Object.keys(porCat).forEach(function (c) { L.push("- **" + c + ":** " + window.fmtBRL(porCat[c])); });
    L.push("");
    var alertas = C.itensAcimaCustoMedio(itens);
    if (alertas.length) {
      L.push("## ⚠ Itens acima do custo médio sem justificativa");
      alertas.forEach(function (it) { L.push("- **" + it.descricao + "** (" + window.fmtBRL(it.preco_unitario) + " > " + window.fmtBRL(it.custo_medio) + ")"); });
    } else {
      L.push("_✓ Todo item acima do custo médio tem justificativa técnica._");
    }
    return L.join("\n");
  }


  function toggleReport() {
    var rep = document.getElementById("report");
    if (rep.style.display === "block") { rep.style.display = "none"; return; }
    rep.style.display = "block";
    rep.innerHTML = gerarRelatorio();
  }
  function gerarRelatorio() {
    var v = window.validarProposta(seed);
    var linhas = [];
    linhas.push("# RELATÓRIO DE ORÇAMENTO — " + seed.meta.projeto);
    linhas.push("_Edital " + seed.meta.edital + " · " + seed.meta.versao + " · base " + seed.meta.data_base + "_");
    linhas.push("");
    linhas.push("**Total:** " + window.fmtBRL(v.total) + " · **Faixa:** " +
      (v.faixa_ok ? "OK (R$1M–R$7M)" : "VIOLADA") + " · **Duração:** " + seed.meta.duracao_meses + " m");
    linhas.push("**Valor inabilitado:** " + window.fmtBRL(v.valor_inabilitado) +
      " (" + (v.pct_inabilitado * 100).toFixed(1) + "%) — " +
      (v.r4_eliminacao ? "⚠ ELIMINAÇÃO [11.2.2]" : "OK (≤30%)"));
    linhas.push("");
    linhas.push("| Rubrica | Item edital | Teto | Valor | % | Status |");
    linhas.push("|---|---|---|---:|---:|---|");
    seed.rubricas.forEach(function (r) {
      var rv = v.rubricas[r.id];
      var cap = rv.cap || {};
      linhas.push("| " + r.nome + " | " + (r.item_edital || "") + " | " + (cap.label || "livre") + " | " +
        window.fmtBRL(rv.valor) + " | " + (rv.pct * 100).toFixed(1) + "% | " +
        (rv.ok ? "✅ APROVADO" : "❌ NÃO APROVADO") + " |");
    });
    linhas.push("");
    var naoAprov = [];
    seed.rubricas.forEach(function (r) {
      r.itens.forEach(function (it) {
        var iv = window.validarItem(r, it);
        if (!iv.ok) naoAprov.push("- **" + r.nome + " / " + it.descricao + "** (" + window.fmtBRL(it.valor) +
          "): " + iv.motivos.join(" "));
      });
    });
    if (naoAprov.length) {
      linhas.push("## Itens NÃO APROVADOS");
      linhas.push(naoAprov.join("\n"));
    } else {
      linhas.push("_Nenhum item individual reprovado._");
    }
    return linhas.join("\n");
  }

  // ---- Export / Import ---------------------------------------------------
  function exportarJSON() {
    var blob = new Blob([JSON.stringify(seed, null, 2)], { type: "application/json" });
    download(blob, "orcamento-finep-agrifam-v2.json");
  }
  function importarJSON(ev) {
    var f = ev.target.files[0]; if (!f) return;
    var reader = new FileReader();
    reader.onload = function () {
      try {
        var obj = JSON.parse(reader.result);
        if (!obj.rubricas || !obj.meta) throw new Error("JSON inválido");
        seed = obj; popularDeSeed(seed); persistir(); renderTudo();
        setStatus("Importado de JSON.");
      } catch (e) { alert("Importação falhou: " + e.message); }
    };
    reader.readAsText(f);
    ev.target.value = "";
  }
  function baixarSqlite() {
    var data = db.export();
    var blob = new Blob([data], { type: "application/octet-stream" });
    download(blob, "orcamento-finep.sqlite");
  }
  function download(blob, nome) {
    var a = document.createElement("a");
    var url = URL.createObjectURL(blob);
    a.href = url; a.download = nome; a.click();
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }

  // ---- utils base64 ------------------------------------------------------
  function uint8ToBase64(u8) {
    var bin = ""; for (var i = 0; i < u8.length; i++) bin += String.fromCharCode(u8[i]);
    return btoa(bin);
  }
  function base64ToUint8(b64) {
    var bin = atob(b64), len = bin.length, u8 = new Uint8Array(len);
    for (var i = 0; i < len; i++) u8[i] = bin.charCodeAt(i);
    return u8;
  }
  function setStatus(t) {
    var el = document.getElementById("status"); if (el) el.textContent = t;
  }
})();
