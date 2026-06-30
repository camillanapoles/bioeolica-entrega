// app.js — Orçamento FINEP AgriFam-ICT 2026: CRUD + SQLite (sql.js WASM) + validação ao vivo.
// MESMA DB: orçamento + catálogo R&D compartilham uma única instância sql.js (orc_finep_v2).
// Persistência: SQLite em memória → exportado binário → localStorage (chave "orc_finep_v2").
// Depende de: seed.js (window.ORCAMENTO_SEED), catalogo.js (window.CATALOGO — helpers + SEED),
// edital-rules.js (window.* validadores, fmtBRL).

(function () {
  "use strict";

  var SQL_JS_URL = "https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.10.3/sql-wasm.js";
  var SQL_JS_WASM = "https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.10.3/sql-wasm.wasm";
  var STORAGE_KEY = "orc_finep_v2";
  var db = null;       // instância sql.js
  var SQL = null;      // construtor sql.js
  var seed = null;     // estado corrente em memória (espelho do SQLite: orçamento + catálogo)
  var aba = "orcamento"; // aba ativa: 'orcamento' | 'catalogo' | 'relatorio'

  var CAT_COLS = "id,categoria,grupo,descricao,tipo_cobranca,unidade,preco_unitario,quantidade,duracao,ensaios,custo_medio,justificativa,fonte";
  var CAT_TIPOS = ["unitario", "fixo", "ensaio", "tempo", "mensal"];

  // ---- Bootstrap ---------------------------------------------------------
  document.addEventListener("DOMContentLoaded", function () {
    mostrarSkeleton(true);
    carregarSqlJs().then(function () {
      return restaurarOuInit();
    }).then(function () {
      vincularUI();
      lerAbaDaUrl();
      renderTudo();
      mostrarSkeleton(false);
      // P$1: espelha cronograma/roadmap da SSOT (constants.json → CI/CD → DB).
      // Não bloqueia o render inicial; re-renderiza quando o manifest chegar.
      return carregarProjetoDoSSOT().then(function () { renderTudo(); });
    }).catch(function (err) {
      mostrarSkeleton(false);
      toast("Erro de init: " + (err && err.message ? err.message : err), "erro");
    });
  });

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
    // MESMA DB: catálogo R&D na mesma instância (schema rico, separado de `itens`).
    db.run(
      "CREATE TABLE IF NOT EXISTS catalogo (" +
      "  id TEXT PRIMARY KEY, categoria TEXT, grupo TEXT, descricao TEXT," +
      "  tipo_cobranca TEXT, unidade TEXT," +
      "  preco_unitario REAL, quantidade REAL, duracao REAL, ensaios REAL," +
      "  custo_medio REAL, justificativa TEXT, fonte TEXT);"
    );
    // MESMA DB: cronograma (M1–M6) + roadmap de implementação. P$1 ZERO HARDCODED —
    // estes dados vêm da SSOT constants.json via CI/CD sync → _seed_from_ssot.json,
    // nunca de literais JS. entregas armazenado como array JSON (TEXT).
    db.run(
      "CREATE TABLE IF NOT EXISTS cronograma (" +
      "  id TEXT PRIMARY KEY, titulo TEXT, mes_ini INTEGER, mes_fim INTEGER," +
      "  cor TEXT, entregas TEXT);"
    );
    db.run(
      "CREATE TABLE IF NOT EXISTS roadmap (" +
      "  fase TEXT PRIMARY KEY, quando TEXT, cor TEXT," +
      "  oque TEXT, depende TEXT, saida TEXT);"
    );
  }

  function popularDeSeed(s) {
    db.run("DELETE FROM itens; DELETE FROM rubricas; DELETE FROM meta; DELETE FROM catalogo; DELETE FROM cronograma; DELETE FROM roadmap;");
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
    // Catálogo: se o seed trouxer, popula; senão seed-on-first-run após chamada externa.
    if (s.catalogo && s.catalogo.length) popularCatalogo(s.catalogo);
  }

  function popularCatalogo(itens) {
    var mc = db.prepare(
      "INSERT OR REPLACE INTO catalogo(" + CAT_COLS + ") VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?);"
    );
    itens.forEach(function (it) {
      mc.run([it.id, it.categoria, it.grupo, it.descricao, it.tipo_cobranca, it.unidade,
              num(it.preco_unitario), num(it.quantidade), it.duracao == null ? null : num(it.duracao),
              it.ensaios == null ? null : num(it.ensaios),
              it.custo_medio == null ? null : num(it.custo_medio),
              it.justificativa || "", it.fonte || ""]);
    }); mc.free();
  }

  // Seed-on-first-run do catálogo (idempotente via count).
  function seedCatalogoSeVazio() {
    var res = db.exec("SELECT count(*) AS n FROM catalogo;");
    var n = res.length ? res[0].values[0][0] : 0;
    if (n === 0 && window.CATALOGO && window.CATALOGO.SEED) {
      popularCatalogo(window.CATALOGO.SEED.itens);
    }
  }

  // ---- Projeto (cronograma + roadmap) — P$1 SSOT via CI/CD ----------------
  // A página NÃO contém dados de cronograma/roadmap. Eles vêm da única fonte de
  // verdade (constants.json) projetada em webapp/_seed_from_ssot.json pelo
  // workflow sync-ssot.yml. Aqui apenas (a) carregamos o manifest e (b)
  // espelhamos para as tabelas relacionais (mesma DB orc_finep_v2).
  function popularProjetoDoSSOT(seedSsot) {
    if (!seedSsot || !seedSsot.projeto) return;
    var p = seedSsot.projeto;
    if (p.meta) {
      var mm = db.prepare("INSERT OR REPLACE INTO meta(k,v) VALUES (?,?);");
      Object.keys(p.meta).forEach(function (k) { mm.run(["projeto_" + k, String(p.meta[k])]); });
      mm.free();
    }
    var crono = (p.cronograma && p.cronograma.marcos) ? p.cronograma.marcos : [];
    if (p.cronograma && p.cronograma.duracao_meses != null) {
      db.run("INSERT OR REPLACE INTO meta(k,v) VALUES ('crono_duracao','" +
             Number(p.cronograma.duracao_meses) + "');");
    }
    var mc = db.prepare(
      "INSERT OR REPLACE INTO cronograma(id,titulo,mes_ini,mes_fim,cor,entregas) VALUES (?,?,?,?,?,?);"
    );
    crono.forEach(function (m) {
      mc.run([m.id, m.titulo, Number(m.mes_ini), Number(m.mes_fim), m.cor || "info",
              JSON.stringify(m.entregas || [])]);
    }); mc.free();
    var fases = (p.roadmap && p.roadmap.fases) ? p.roadmap.fases : [];
    var mf = db.prepare(
      "INSERT OR REPLACE INTO roadmap(fase,quando,cor,oque,depende,saida) VALUES (?,?,?,?,?,?);"
    );
    fases.forEach(function (f) {
      mf.run([f.fase, f.quando, f.cor || "info", f.oque, f.depende || "", f.saida || ""]);
    }); mf.free();
  }

  function carregarProjetoDoSSOT() {
    return fetch("./_seed_from_ssot.json", { cache: "no-store" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (seedSsot) {
        if (!seedSsot) return;
        popularProjetoDoSSOT(seedSsot);
        persistir(true);
      })
      .catch(function (e) {
        // file:// local ou offline — DB já persistido de um sync anterior.
        console.warn("SSOT manifest indisponível:", e && e.message);
      });
  }

  function listarCronograma() {
    try {
      var res = db.exec("SELECT id,titulo,mes_ini,mes_fim,cor,entregas FROM cronograma ORDER BY mes_ini;");
      if (!res.length) return [];
      return res[0].values.map(function (r) {
        var e; try { e = JSON.parse(r[5] || "[]"); } catch (_) { e = []; }
        return { id: r[0], titulo: r[1], mes_ini: r[2], mes_fim: r[3], cor: r[4], entregas: e };
      });
    } catch (_) { return []; }
  }

  function cronoDuracao() {
    try {
      var res = db.exec("SELECT v FROM meta WHERE k='crono_duracao';");
      var d = res.length ? Number(res[0].values[0][0]) : 36;
      return d > 0 ? d : 36;
    } catch (_) { return 36; }
  }

  function listarRoadmap() {
    try {
      var res = db.exec("SELECT fase,quando,cor,oque,depende,saida FROM roadmap ORDER BY fase;");
      if (!res.length) return [];
      return res[0].values.map(function (r) {
        return { fase: r[0], quando: r[1], cor: r[2], oque: r[3], depende: r[4], saida: r[5] };
      });
    } catch (_) { return []; }
  }

  function lerDbParaSeed() {
    var meta = {};
    db.exec("SELECT k,v FROM meta;")[0].values.forEach(function (row) { meta[row[0]] = row[1]; });
    meta.faixa_min = Number(meta.faixa_min); meta.faixa_max = Number(meta.faixa_max);
    meta.duracao_meses = Number(meta.duracao_meses);
    var rubricas = db.exec("SELECT * FROM rubricas;")[0];
    var itens = db.exec("SELECT * FROM itens;")[0];
    var colsR = rubricas.columns, rowsR = rubricas.values;
    var colsI = itens.columns, rowsI = itens.values;
    var out = { meta: meta, rubricas: [], catalogo: [] };
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
    // Catálogo (tabela pode não existir em DBs antigos → guard).
    try {
      var cat = db.exec("SELECT " + CAT_COLS + " FROM catalogo;");
      if (cat.length) {
        var cc = cat[0].columns, cr = cat[0].values;
        cr.forEach(function (row) {
          var it = rowToObj(cc, row);
          it.preco_unitario = num(it.preco_unitario);
          it.quantidade = num(it.quantidade);
          it.duracao = it.duracao == null ? null : num(it.duracao);
          it.ensaios = it.ensaios == null ? null : num(it.ensaios);
          it.custo_medio = it.custo_medio == null ? null : num(it.custo_medio);
          out.catalogo.push(it);
        });
      }
    } catch (e) { /* tabela ausente: catálogo vazio */ }
    return out;
  }

  function rowToObj(cols, row) {
    var o = {}; cols.forEach(function (c, i) { o[c] = row[i]; }); return o;
  }
  function num(v) { var n = parseFloat(v); return isFinite(n) ? n : 0; }

  function persistir(silencoso) {
    try {
      var data = db.export();
      var str = uint8ToBase64(data);
      localStorage.setItem(STORAGE_KEY, str);
      if (!silencoso) setStatus("Salvo (" + (data.length / 1024).toFixed(1) + " KB em localStorage).");
    } catch (e) { setStatus("Falha ao salvar: " + e.message); }
  }

  function restaurarOuInit() {
    initDb();
    var salvo = localStorage.getItem(STORAGE_KEY);
    if (salvo) {
      try {
        var data = base64ToUint8(salvo);
        db = new SQL.Database(data);
        // Garante tabela catálogo em DBs antigos + seed se vazio.
        initDb();
        seedCatalogoSeVazio();
        seed = lerDbParaSeed();
        setStatus("Restaurado de localStorage.");
        return Promise.resolve();
      } catch (e) { console.warn("restore falhou, reseed", e); }
    }
    seed = JSON.parse(JSON.stringify(window.ORCAMENTO_SEED));
    seed.catalogo = JSON.parse(JSON.stringify(window.CATALOGO.SEED.itens));
    popularDeSeed(seed);
    persistir(true);
    return Promise.resolve();
  }

  // ---- CRUD orçamento ---------------------------------------------------
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

  // ---- CRUD catálogo (MESMA DB) -----------------------------------------
  function salvarItemCatalogo(it) {
    var s = db.prepare(
      "INSERT OR REPLACE INTO catalogo(" + CAT_COLS + ") VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?);"
    );
    s.run([it.id, it.categoria, it.grupo, it.descricao, it.tipo_cobranca, it.unidade,
           num(it.preco_unitario), num(it.quantidade), it.duracao == null ? null : num(it.duracao),
           it.ensaios == null ? null : num(it.ensaios),
           it.custo_medio == null ? null : num(it.custo_medio),
           it.justificativa || "", it.fonte || ""]);
    s.free();
  }
  function removerItemCatalogo(id) {
    var s = db.prepare("DELETE FROM catalogo WHERE id=?;"); s.run([id]); s.free();
  }

  // ---- UI bind -----------------------------------------------------------
  function vincularUI() {
    document.getElementById("btnReset").onclick = function () {
      if (!confirm("Descartar edições e re-carregar orçamento v2.0 + catálogo original?")) return;
      seed = JSON.parse(JSON.stringify(window.ORCAMENTO_SEED));
      seed.catalogo = JSON.parse(JSON.stringify(window.CATALOGO.SEED.itens));
      popularDeSeed(seed); persistir(); renderTudo();
      toast("Restaurado para v2.0 + catálogo original.", "ok");
    };
    document.getElementById("btnExport").onclick = exportarJSON;
    document.getElementById("btnImport").onclick = function () {
      document.getElementById("fileImport").click();
    };
    document.getElementById("fileImport").onchange = importarJSON;
    document.getElementById("btnDownloadSqlite").onclick = baixarSqlite;
    // Abas
    var tabs = document.querySelectorAll("[data-aba]");
    tabs.forEach(function (btn) {
      btn.addEventListener("click", function () { navegar(btn.getAttribute("data-aba")); });
    });
    // Atalhos de teclado (ux-principles: acessibilidade)
    document.addEventListener("keydown", function (e) {
      var mod = e.ctrlKey || e.metaKey;
      if (mod && e.key.toLowerCase() === "e") { e.preventDefault(); exportarJSON(); }
      else if (mod && e.key.toLowerCase() === "i") { e.preventDefault(); document.getElementById("fileImport").click(); }
      else if (!mod && e.key === "1") { navegar("orcamento"); }
      else if (!mod && e.key === "2") { navegar("catalogo"); }
      else if (!mod && e.key === "3") { navegar("relatorio"); }
      else if (!mod && e.key === "4") { navegar("cronograma"); }
      else if (!mod && e.key === "5") { navegar("roadmap"); }
    });
  }

  function lerAbaDaUrl() {
    var h = (location.hash || "").replace("#", "");
    if (["orcamento", "catalogo", "relatorio"].indexOf(h) >= 0) aba = h;
  }

  function navegar(nova) {
    aba = nova;
    if (history.replaceState) history.replaceState(null, "", "#" + nova);
    renderTudo();
  }

  // ---- Render dispatcher -------------------------------------------------
  function renderTudo() {
    renderMeta();
    renderTabs();
    renderTotais();          // sticky header (sempre visível)
    var o = document.getElementById("tabela");
    var c = document.getElementById("catalogoView");
    var cr = document.getElementById("cronogramaView");
    var rd = document.getElementById("roadmapView");
    var r = document.getElementById("report");
    o.style.display = aba === "orcamento" ? "" : "none";
    c.style.display = aba === "catalogo" ? "block" : "none";
    cr.style.display = aba === "cronograma" ? "block" : "none";
    rd.style.display = aba === "roadmap" ? "block" : "none";
    r.style.display = aba === "relatorio" ? "block" : "none";
    if (aba === "orcamento") renderTabela();
    else o.innerHTML = "";
    if (aba === "catalogo") renderCatalogo();
    else c.innerHTML = "";
    if (aba === "cronograma") { cr.innerHTML = renderCronograma(); }
    else cr.innerHTML = "";
    if (aba === "roadmap") { rd.innerHTML = renderRoadmap(); }
    else rd.innerHTML = "";
    if (aba === "relatorio") { r.innerHTML = gerarRelatorio(); }
    else r.innerHTML = "";
  }

  function renderTabs() {
    var tabs = document.querySelectorAll("[data-aba]");
    tabs.forEach(function (btn) {
      var ativo = btn.getAttribute("data-aba") === aba;
      btn.classList.toggle("ativo", ativo);
      btn.setAttribute("aria-selected", ativo ? "true" : "false");
    });
  }

  function renderMeta() {
    var m = seed.meta;
    document.getElementById("metaProj").textContent = m.projeto;
    document.getElementById("metaVer").textContent = m.versao;
    document.getElementById("metaData").textContent = m.data_base;
  }

  // ---- Render orçamento --------------------------------------------------
  function renderTabela() {
    var cont = document.getElementById("tabela");
    cont.innerHTML = "";
    // Painel anti-R4 (rubricas que excedem teto/valor inabilitado)
    var painel = renderPainelR4();
    if (painel) cont.appendChild(painel);

    seed.rubricas.forEach(function (r) {
      var total = window.somaTotal(seed);
      var rv = window.validarRubrica(r, total);

      var sec = document.createElement("section");
      sec.className = "rubrica" + (rv.ok ? "" : " rim");
      sec.setAttribute("aria-label", r.nome);

      var head = document.createElement("div");
      head.className = "rubrica-head";
      var capLabel = rv.cap ? (" — teto " + rv.cap.label + " [item " + rv.cap.item + "]") : " — livre";
      var pctTxt = rv.cap && rv.cap.pct !== null
        ? " (máx " + window.fmtBRL(total * rv.cap.pct) + ")"
        : "";
      head.innerHTML = "<h3>" + r.nome + capLabel + "</h3>" +
        "<div class=\"rubrica-totais\">Subtotal: <b>" + window.fmtBRL(rv.valor) + "</b>" +
        " <span class='pill " + (rv.ok ? "ok" : "nao") + "'>" + (rv.pct * 100).toFixed(1) + "%</span>" +
        pctTxt + (rv.ok ? "" : " — <span class=\"tagNAO\">NÃO APROVADO</span>") + "</div>";
      sec.appendChild(head);

      var tbl = document.createElement("table");
      tbl.innerHTML =
        "<thead><tr>" +
        "<th>Item</th><th>Tipo</th><th>Valor</th><th>Status</th><th>Motivo / Valor máximo</th><th aria-label='remover'></th>" +
        "</tr></thead><tbody></tbody>";
      var body = tbl.querySelector("tbody");

      r.itens.forEach(function (it) {
        var iv = window.validarItem(r, it);
        var tr = document.createElement("tr");
        tr.className = iv.ok ? "" : "linhaRuim";

        var tdDesc = cel(it.descricao, "descricao", it.id);
        var tdTipo = celTipo(it.tipo, it.id);
        var tdVal = celValor(it.valor, it.id);

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
        btn.className = "btn-icone"; btn.textContent = "✕"; btn.title = "Excluir item";
        btn.setAttribute("aria-label", "Excluir " + it.descricao);
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
        "<td><input type='text' placeholder='Novo item...' data-add='descricao' aria-label='Novo item'></td>" +
        "<td><select data-add='tipo' aria-label='Tipo'>" + optionsTipo() + "</select></td>" +
        "<td><input type='number' min='0' step='0.01' placeholder='0,00' data-add='valor' aria-label='Valor'></td>" +
        "<td></td><td></td><td><button class='btn btn-sec'>＋ Add</button></td>";
      trAdd.querySelector("button").onclick = function () {
        var desc = trAdd.querySelector("[data-add='descricao']").value.trim();
        var tipo = trAdd.querySelector("[data-add='tipo']").value;
        var val = parseFloat(trAdd.querySelector("[data-add='valor']").value) || 0;
        if (!desc) { toast("Descreva o item.", "erro"); return; }
        var it = { id: novoId(r.id), descricao: desc, valor: val, tipo: tipo };
        upsertItem(r.id, it); seed = lerDbParaSeed(); persistir(); renderTudo();
      };
      body.appendChild(trAdd);

      sec.appendChild(tbl);
      cont.appendChild(sec);
    });
  }

  function renderPainelR4() {
    var v = window.validarProposta(seed);
    var problemas = [];
    seed.rubricas.forEach(function (r) {
      var rv = v.rubricas[r.id];
      if (!rv.ok) {
        var total = v.total;
        var max = rv.cap && rv.cap.pct !== null ? window.fmtBRL(total * rv.cap.pct) : null;
        problemas.push({ nome: r.nome, valor: rv.valor, max: max, item: rv.cap && rv.cap.item });
      }
    });
    if (v.r4_eliminacao) {
      problemas.unshift({ nome: "R4 — VALOR INABILITADO > 30%", valor: v.valor_inabilitado, max: window.fmtBRL(v.total * 0.30), item: "11.2.2", r4: true });
    }
    if (!problemas.length) return null;
    var div = document.createElement("div");
    div.className = "painel-r4";
    div.setAttribute("role", "alert");
    div.innerHTML = "<h3>⚠ Pendências de validação</h3>";
    problemas.forEach(function (p) {
      var linha = document.createElement("div");
      linha.className = "painel-r4-linha" + (p.r4 ? " crit" : "");
      linha.innerHTML = "<b>" + p.nome + "</b> — atual " + window.fmtBRL(p.valor) +
        (p.max ? " · máximo permitido <b>" + p.max + "</b>" : "") +
        (p.item ? " <small>[item " + p.item + "]</small>" : "");
      div.appendChild(linha);
    });
    return div;
  }

  function optionsTipo(sel) {
    var tipos = ["mao-de-obra", "servico", "insumo", "equipamento-menor", "equipamento-maior",
                 "obra", "operacional", "diaria", "passagem"];
    return tipos.map(function (t) {
      return "<option value='" + t + "'" + (t === sel ? " selected" : "") + ">" + t + "</option>";
    }).join("");
  }

  function cel(val, campo, id) {
    var td = document.createElement("td");
    var inp = document.createElement("input");
    inp.type = "text"; inp.value = val; inp.setAttribute("aria-label", campo);
    inp.onchange = function () {
      var s = db.prepare("UPDATE itens SET " + campo + "=? WHERE id=?;");
      s.run([inp.value, id]); s.free();
      seed = lerDbParaSeed(); persistir(); renderTudo();
    };
    td.appendChild(inp); return td;
  }
  function celValor(val, id) {
    var td = document.createElement("td");
    var inp = document.createElement("input");
    inp.type = "number"; inp.min = "0"; inp.step = "0.01"; inp.value = val;
    inp.setAttribute("aria-label", "valor");
    inp.onchange = function () {
      var v = parseFloat(inp.value) || 0;
      var s = db.prepare("UPDATE itens SET valor=? WHERE id=?;"); s.run([v, id]); s.free();
      seed = lerDbParaSeed(); persistir(); renderTudo();
    };
    td.appendChild(inp); return td;
  }
  function celTipo(val, id) {
    var td = document.createElement("td");
    var sel = document.createElement("select");
    sel.innerHTML = optionsTipo(val); sel.setAttribute("aria-label", "tipo");
    sel.onchange = function () {
      var s = db.prepare("UPDATE itens SET tipo=? WHERE id=?;"); s.run([sel.value, id]); s.free();
      seed = lerDbParaSeed(); persistir(); renderTudo();
    };
    td.appendChild(sel); return td;
  }

  // ---- Totais (sticky header) -------------------------------------------
  function renderTotais() {
    var v = window.validarProposta(seed);
    var box = document.getElementById("totais");
    var r4 = v.r4_eliminacao
      ? "<span class='tagNAO'>⚠ R4 — VALOR INABILITADO > 30% ⇒ ELIMINAÇÃO [11.2.2]</span>"
      : "<span class='tagOK'>R4 OK — inabilitado " + (v.pct_inabilitado * 100).toFixed(1) + "% (≤30%)</span>";
    var faixa = v.faixa_ok
      ? "<span class='tagOK'>Faixa R$1M–R$7M OK</span>"
      : "<span class='tagNAO'>Faixa violada</span>";
    var totalCat = window.CATALOGO.totalGeral(seed.catalogo);
    box.innerHTML =
      "<div class='totais-linha'><div><b>TOTAL ORÇAMENTO:</b> <span class='big' aria-live='polite'>" + window.fmtBRL(v.total) + "</span></div>" +
      "<div class='totais-badges'>" + faixa + " " + r4 + "</div></div>" +
      "<div class='resumo' aria-live='polite'>" + resumoRubricas(v) + "</div>" +
      (v.globais.length ? "<div class='globais'>" + v.globais.join("<br>") + "</div>" : "") +
      "<div class='meta-row'>Catálogo R&D (hard costs): <b>" + window.fmtBRL(totalCat) + "</b> · " +
      seed.catalogo.length + " itens</div>";
  }

  function resumoRubricas(v) {
    return seed.rubricas.map(function (r) {
      var rv = v.rubricas[r.id];
      var cor = rv.ok ? "ok" : "nao";
      var pct = (rv.pct * 100).toFixed(1) + "%";
      return "<span class='pill " + cor + "'>" + r.nome + ": " + window.fmtBRL(rv.valor) + " (" + pct + ")</span>";
    }).join(" ");
  }

  // ---- Catálogo R&D (lê da MESMA DB: seed.catalogo) ----------------------
  function renderCatalogo() {
    var box = document.getElementById("catalogoView");
    box.innerHTML = "";
    var C = window.CATALOGO;
    var itens = seed.catalogo;
    var total = C.totalGeral(itens);
    var alertas = C.itensAcimaCustoMedio(itens);

    // Head
    var head = document.createElement("div");
    head.className = "catalogo-head";
    head.innerHTML =
      "<div><b>" + C.SEED.meta.titulo + "</b> <span class='meta-row'>· base " + C.SEED.meta.base + "</span>" +
      "<br><span class='meta-row'>" + C.SEED.meta.nota + "</span></div>" +
      "<div class='catalogo-total'><b>TOTAL CATÁLOGO</b><span class='big' aria-live='polite'>" + window.fmtBRL(total) + "</span>" +
      "<br><span class='" + (alertas.length ? "tagNAO" : "tagOK") + "'>" +
      (alertas.length ? "⚠ " + alertas.length + " sem justificativa" : "✓ todos justificados") + "</span></div>";
    box.appendChild(head);

    // Toolbar do catálogo
    box.appendChild(renderCatalogoToolbar());

    // Agrupamento collapsible por grupo
    var porGrupo = {};
    itens.forEach(function (it) { (porGrupo[it.grupo] = porGrupo[it.grupo] || []).push(it); });
    Object.keys(porGrupo).forEach(function (g) {
      var det = document.createElement("details");
      det.className = "grupo-cat"; det.open = true;
      var sub = porGrupo[g].reduce(function (s, it) { return s + C.calcularTotal(it); }, 0);
      var sum = document.createElement("summary");
      sum.innerHTML = "<b>" + g + "</b> <span class='meta-row'>· " + porGrupo[g].length + " itens · " + window.fmtBRL(sub) + "</span>";
      det.appendChild(sum);

      var tbl = document.createElement("table");
      tbl.innerHTML =
        "<thead><tr>" +
        "<th>Item</th><th>Categoria</th><th>Tipo cobrança</th>" +
        "<th>Preço unit.</th><th>Qtd</th><th>Ensaios/Duração</th>" +
        "<th>Custo médio</th><th>% s/ médio</th><th>Total</th><th>Fonte</th><th>Justificativa</th><th aria-label='remover'></th>" +
        "</tr></thead><tbody></tbody>";
      var body = tbl.querySelector("tbody");
      porGrupo[g].forEach(function (it) {
        body.appendChild(renderLinhaCatalogo(it, C));
      });
      // Linha adicionar
      var trAdd = document.createElement("tr");
      trAdd.className = "linhaAdd";
      trAdd.innerHTML = "<td colspan='12'><button class='btn btn-sec'>＋ Novo item em '" + g + "'</button></td>";
      trAdd.querySelector("button").onclick = function () {
        var it = { id: novoId("ct"), categoria: "tp_pj", grupo: g, descricao: "Novo item", tipo_cobranca: "unitario",
                   unidade: "un", preco_unitario: 0, quantidade: 1, duracao: null, ensaios: null, custo_medio: null, justificativa: "", fonte: "" };
        salvarItemCatalogo(it); seed = lerDbParaSeed(); persistir(); renderTudo();
      };
      body.appendChild(trAdd);

      det.appendChild(tbl);
      box.appendChild(det);
    });
  }

  function renderLinhaCatalogo(it, C) {
    var total = C.calcularTotal(it);
    var acima = it.custo_medio && num(it.preco_unitario) > num(it.custo_medio) && !it.justificativa;
    var pctMed = it.custo_medio ? ((num(it.preco_unitario) / num(it.custo_medio) - 1) * 100) : null;
    var tr = document.createElement("tr");
    if (acima) tr.className = "linhaRuim";

    var tcampos = "";
    if (it.tipo_cobranca === "ensaio") tcampos = (it.ensaios || 0) + " rnd";
    else if (it.tipo_cobranca === "tempo") tcampos = (it.duracao || 0) + " h";
    else if (it.tipo_cobranca === "mensal") tcampos = (it.quantidade || 0) + " meses";
    else tcampos = "—";

    tr.innerHTML =
      "<td></td><td><code>" + it.categoria + "</code></td><td></td>" +
      "<td></td><td></td><td class='num'>" + tcampos + "</td>" +
      "<td></td><td class='num'></td><td class='num'><b>" + window.fmtBRL(total) + "</b></td>" +
      "<td></td><td class='motivo'></td><td></td>";

    // Descrição (editável)
    var tdDesc = tr.children[0];
    tdDesc.appendChild(catInput(it, "descricao", "text"));

    // Tipo cobrança (select)
    var tdTipo = tr.children[2];
    tdTipo.appendChild(catTipo(it));

    // Preço unitário
    tr.children[3].appendChild(catInput(it, "preco_unitario", "number"));

    // Qtd
    tr.children[4].appendChild(catInput(it, "quantidade", "number"));

    // Custo médio
    tr.children[6].appendChild(catInput(it, "custo_medio", "number"));

    // % sobre custo médio
    var tdPct = tr.children[7];
    if (pctMed !== null) {
      var s = document.createElement("span");
      s.className = pctMed > 0 ? "tagNAO" : "tagOK";
      s.textContent = (pctMed >= 0 ? "+" : "") + pctMed.toFixed(0) + "%";
      tdPct.appendChild(s);
    } else tdPct.textContent = "—";

    // Fonte/referência
    tr.children[9].appendChild(catInput(it, "fonte", "text"));

    // Justificativa
    var tdJust = tr.children[10];
    tdJust.appendChild(catInput(it, "justificativa", "text"));
    if (acima) {
      var warn = document.createElement("div");
      warn.className = "meta-row"; warn.style.color = "var(--nao)";
      warn.textContent = "⚠ acima do custo médio sem justificativa";
      tdJust.appendChild(warn);
    }

    // Remover
    var tdAcao = tr.children[11];
    var btn = document.createElement("button");
    btn.className = "btn-icone"; btn.textContent = "✕"; btn.title = "Excluir do catálogo";
    btn.setAttribute("aria-label", "Excluir " + it.descricao);
    btn.onclick = function () {
      if (!confirm("Excluir '" + it.descricao + "' do catálogo?")) return;
      removerItemCatalogo(it.id); seed = lerDbParaSeed(); persistir(); renderTudo();
    };
    tdAcao.appendChild(btn);

    return tr;
  }

  function catInput(it, campo, tipo) {
    var inp = document.createElement("input");
    inp.type = tipo;
    inp.value = it[campo] == null ? "" : it[campo];
    if (tipo === "number") { inp.min = "0"; inp.step = "0.01"; inp.className = "inp-num"; }
    inp.setAttribute("aria-label", campo);
    inp.onchange = function () {
      var v = tipo === "number" ? (inp.value === "" ? null : parseFloat(inp.value)) : inp.value;
      it[campo] = v; salvarItemCatalogo(it);
      seed = lerDbParaSeed(); persistir(); renderTudo();
    };
    return inp;
  }
  function catTipo(it) {
    var sel = document.createElement("select");
    sel.setAttribute("aria-label", "tipo_cobranca");
    sel.innerHTML = CAT_TIPOS.map(function (t) {
      return "<option value='" + t + "'" + (t === it.tipo_cobranca ? " selected" : "") + ">" + t + "</option>";
    }).join("");
    sel.onchange = function () {
      it.tipo_cobranca = sel.value; salvarItemCatalogo(it);
      seed = lerDbParaSeed(); persistir(); renderTudo();
    };
    return sel;
  }

  function renderCatalogoToolbar() {
    var wrap = document.createElement("div");
    wrap.className = "toolbar-cat";
    var bMd = document.createElement("button");
    bMd.className = "btn btn-sec"; bMd.textContent = "📄 Relatório (Markdown)";
    bMd.onclick = function () {
      var blob = new Blob([gerarRelatorioCatalogo()], { type: "text/markdown" });
      download(blob, "catalogo-rd-bioeolica.md"); toast("Relatório MD gerado.", "ok");
    };
    var bJson = document.createElement("button");
    bJson.className = "btn btn-sec"; bJson.textContent = "⬇ Catálogo (JSON)";
    bJson.onclick = function () {
      var payload = { meta: window.CATALOGO.SEED.meta, itens: seed.catalogo };
      var blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
      download(blob, "catalogo-rd-bioeolica.json"); toast("JSON do catálogo gerado.", "ok");
    };
    wrap.appendChild(bMd); wrap.appendChild(bJson);
    return wrap;
  }

  function gerarRelatorioCatalogo() {
    var C = window.CATALOGO;
    var itens = seed.catalogo;
    var m = C.SEED.meta;
    var total = C.totalGeral(itens);
    var L = [];
    L.push("# " + m.titulo);
    L.push("_Base " + m.base + " — " + m.nota + "_");
    L.push("");
    L.push("**Total do catálogo:** " + window.fmtBRL(total));
    L.push("");
    L.push("| Item | Categoria | Grupo | Tipo | Preço unit. | Qtd | Ensaios/Duração | Custo médio | % s/ médio | Total | Fonte | Justificativa |");
    L.push("|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|");
    itens.forEach(function (it) {
      var t = C.calcularTotal(it);
      var extra = it.tipo_cobranca === "ensaio" ? (it.ensaios || 0) + " rnd"
        : it.tipo_cobranca === "tempo" ? (it.duracao || 0) + " h"
        : it.tipo_cobranca === "mensal" ? (it.quantidade || 0) + " mêses" : "—";
      var pct = it.custo_medio ? ((num(it.preco_unitario) / num(it.custo_medio) - 1) * 100).toFixed(0) + "%" : "—";
      L.push("| " + it.descricao + " | " + it.categoria + " | " + it.grupo + " | " + it.tipo_cobranca +
        " | " + window.fmtBRL(it.preco_unitario) + " | " + (it.quantidade || "—") + " " + (it.unidade || "") +
        " | " + extra + " | " + (it.custo_medio ? window.fmtBRL(it.custo_medio) : "—") +
        " | " + pct + " | " + window.fmtBRL(t) + " | " + (it.fonte || "—") + " | " + (it.justificativa || "") + " |");
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

  // ---- Relatório (orçamento) --------------------------------------------
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
    linhas.push("## Catálogo R&D — " + window.fmtBRL(window.CATALOGO.totalGeral(seed.catalogo)) + " (" + seed.catalogo.length + " itens)");
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

  // ---- Cronograma (M1–M6) — DB-backed da SSOT (P$1 ZERO HARDCODED) --------
  // Render lê das tabelas `cronograma`/`roadmap` (mesma DB orc_finep_v2),
  // populadas pelo manifest _seed_from_ssot.json (projeção de constants.json
  // via CI/CD sync-ssot.yml). Sem literais JS.
  function renderCronograma() {
    var marcos = listarCronograma();
    var dur = cronoDuracao();
    var html = "";
    html += '<div class="catalogo-head"><div><h3>Cronograma Físico — ' + dur + ' meses</h3>' +
            '<div class="meta-row" style="margin:0">Fonte: <code>constants.json → projeto.cronograma</code> ' +
            '(SSOT, via CI/CD). Duração máx. edital item 9.1.</div></div>' +
            '<div class="catalogo-total"><span class="big">' + dur + '</span><small>mêses</small></div></div>';

    if (!marcos.length) {
      html += '<div class="rubrica"><div style="padding:var(--sp-4)" class="meta-row">' +
              'Aguardando manifest SSOT (<code>_seed_from_ssot.json</code>). ' +
              'Em produção (GitHub Pages) é gerado pelo workflow <code>sync-ssot.yml</code>.</div></div>';
      return html;
    }

    html += '<div class="rubrica"><div style="overflow-x:auto"><table>' +
            '<thead><tr><th style="min-width:140px">Marco</th><th>Janela</th>';
    for (var m = 1; m <= dur; m++) {
      html += '<th class="num" title="Mês ' + m + '">' + (m % 3 === 0 ? m : "·") + '</th>';
    }
    html += '</tr></thead><tbody>';
    marcos.forEach(function (mc) {
      html += '<tr><td><b>' + esc(mc.id) + '</b> ' + esc(mc.titulo) + '</td>' +
              '<td class="num">M' + mc.mes_ini + '–M' + mc.mes_fim + '</td>';
      for (var k = 1; k <= dur; k++) {
        var ativo = k >= mc.mes_ini && k <= mc.mes_fim;
        html += '<td class="num"' + (ativo ? ' style="background:var(--' + mc.cor + '-bg);' +
                'box-shadow:inset 0 0 0 1px var(--' + mc.cor + '-line)"' : '') + '></td>';
      }
      html += '</tr>';
    });
    html += '</tbody></table></div></div>';

    // Entregas por marco
    html += '<div class="rubrica"><div class="rubrica-head"><h3>Entregas por marco</h3></div>';
    html += '<table><thead><tr><th>Marco</th><th>Entregas</th></tr></thead><tbody>';
    marcos.forEach(function (mc) {
      html += '<tr><td style="vertical-align:top"><span class="pill ' + mc.cor + '">' + esc(mc.id) + '</span> ' +
              esc(mc.titulo) + '<br><small class="meta-row" style="margin:0">M' + mc.mes_ini + '–M' + mc.mes_fim + '</small></td>';
      html += '<td><ul style="margin:0;padding-left:18px">';
      mc.entregas.forEach(function (e) { html += '<li>' + esc(e) + '</li>'; });
      html += '</ul></td></tr>';
    });
    html += '</tbody></table></div>';

    // Risco temporal R1
    html += '<div class="painel-r4"><h3>⚠ Risco temporal R1 (bloqueador externo)</h3>' +
            '<div class="painel-r4-linha crit">Cadastro Finep: prazo 26/06/2026 17h (verificar status — hoje ' +
            new Date().toLocaleDateString("pt-BR") + ').</div>' +
            '<div class="painel-r4-linha">Proposta: 03/07/2026 17h. A escrita/código seguem independentes, ' +
            'mas a submissão real depende do cadastro aprovado.</div></div>';
    return html;
  }

  // ---- Roadmap de implementação — DB-backed da SSOT -----------------------
  function renderRoadmap() {
    var fases = listarRoadmap();
    var html = "";
    html += '<div class="catalogo-head"><div><h3>Roadmap de Implementação</h3>' +
            '<div class="meta-row" style="margin:0">Fonte: <code>constants.json → projeto.roadmap</code> ' +
            '(SSOT, via CI/CD). Entrega final = <b>IMPLEMENTAÇÃO</b>: 6 sistemas (5 comunidades + 1 protótipo) ' +
            'ficam no campo.</div></div></div>';

    if (!fases.length) {
      html += '<div class="rubrica"><div style="padding:var(--sp-4)" class="meta-row">' +
              'Aguardando manifest SSOT (<code>_seed_from_ssot.json</code>) gerado pelo CI/CD.</div></div>';
      return html;
    }

    html += '<div class="rubrica"><div class="rubrica-head"><h3>Fases (topologia DAG)</h3></div>';
    html += '<table><thead><tr><th>Fase</th><th>Janela</th><th>O quê</th><th>Depende de</th><th>Saída</th></tr></thead><tbody>';
    fases.forEach(function (f) {
      html += '<tr><td><span class="pill ' + f.cor + '">' + esc(f.fase) + '</span></td>' +
              '<td class="status">' + esc(f.quando) + '</td>' +
              '<td>' + esc(f.oque) + '</td>' +
              '<td class="motivo">' + esc(f.depende) + '</td>' +
              '<td><b>' + esc(f.saida) + '</b></td></tr>';
    });
    html += '</tbody></table></div>';

    html += '<div class="rubrica"><div class="rubrica-head"><h3>Entrega final — 6 sistemas no campo</h3></div>';
    html += '<div style="padding:var(--sp-3) var(--sp-4)">' +
            '<div class="totais-badges">' +
            '<span class="pill nao">5 comunidades PE/BA</span>' +
            '<span class="pill info">1 protótipo</span>' +
            '<span class="pill ok">6 sistemas comissionados</span>' +
            '</div>' +
            '<p class="meta-row" style="margin-top:var(--sp-3)">Cada sistema: rotor/pás PM-15G · PMG NdFeB · torre 10 m · banco de baterias 150 Ah · ' +
            'instrumentação Arduino/GSM · sistema de irrigação (bomba CC 24V + controlador + cisterna, &lt;R$50K item 6.6.2). ' +
            'Cartas de anuência: trio CNPJ + assinatura digital + validade ≥36 meses (5.6.1.2).</p></div></div>';
    return html;
  }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }


  function exportarJSON() {
    var payload = {
      meta: seed.meta,
      rubricas: seed.rubricas,
      catalogo: seed.catalogo,
      _schema: "orc_finep_v2+catalogo"
    };
    var blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    download(blob, "orcamento-finep-agrifam-v2.json");
    toast("JSON exportado (orçamento + catálogo).", "ok");
  }
  function importarJSON(ev) {
    var f = ev.target.files[0]; if (!f) return;
    var reader = new FileReader();
    reader.onload = function () {
      try {
        var obj = JSON.parse(reader.result);
        if (!obj.rubricas || !obj.meta) throw new Error("JSON inválido (sem rubricas/meta)");
        if (!obj.catalogo && window.CATALOGO) obj.catalogo = JSON.parse(JSON.stringify(window.CATALOGO.SEED.itens));
        seed = obj; popularDeSeed(seed); persistir(); renderTudo();
        toast("Importado de JSON.", "ok");
      } catch (e) { toast("Importação falhou: " + e.message, "erro"); }
    };
    reader.readAsText(f);
    ev.target.value = "";
  }
  function baixarSqlite() {
    var data = db.export();
    var blob = new Blob([data], { type: "application/octet-stream" });
    download(blob, "orcamento-finep.sqlite");
    toast("SQLite (orçamento + catálogo) baixado.", "ok");
  }
  function download(blob, nome) {
    var a = document.createElement("a");
    var url = URL.createObjectURL(blob);
    a.href = url; a.download = nome; a.click();
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }

  // ---- UX: skeleton, toast ----------------------------------------------
  function mostrarSkeleton(on) {
    var sk = document.getElementById("skeleton");
    if (sk) sk.style.display = on ? "flex" : "none";
  }
  function toast(msg, tipo) {
    var box = document.getElementById("toast");
    if (!box) { setStatus(msg); return; }
    var el = document.createElement("div");
    el.className = "toast " + (tipo || "info");
    el.setAttribute("role", "status");
    el.textContent = msg;
    box.appendChild(el);
    setTimeout(function () { el.classList.add("fade"); }, 1500);
    setTimeout(function () { if (el.parentNode) el.parentNode.removeChild(el); }, 2200);
    setStatus(msg);
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
