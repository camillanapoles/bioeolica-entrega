#!/usr/bin/env node
/**
 * Edital conformity gate (Mandato: GARANTIR CONFORMIDADE COM O EDITAL).
 *
 * Headless runner that loads the webapp's OWN orcamento (webapp/seed.js) and the
 * webapp's OWN validation engine (webapp/edital-rules.js → validarProposta) and
 * asserts the proposal conforms to FINEP AgriFam-ICT 2026. This is the SSOT for
 * the rules: the same `validarProposta` the webapp runs live is what CI runs —
 * no duplicated rule logic.
 *
 * Run by .github/workflows/audit-edital.yml on every change to the orcamento and
 * on a schedule. Exits non-zero (→ CI FAIL) on any conformity violation:
 *   - total outside [R$1.000.000, R$7.000.000]
 *   - duração > 36 meses
 *   - any rubrica over its cap (pessoal/bolsas ≤30%, operacional =5%,
 *     diárias ≤5%, passagens ≤5%, obras ≤10% + ≤R$392.952,63/ambiente)
 *   - R4 eliminação: valor inabilitado > 30% do total
 *
 * Usage:
 *   node scripts/audit_edital_conformity.js            # human report, exit 1 on violation
 *   node scripts/audit_edital_conformity.js --json      # machine-readable
 *   node scripts/audit_edital_conformity.js --quiet     # only print on failure
 */
'use strict';

const fs = require('fs');
const vm = require('vm');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const WEBAPP = (...p) => path.join(ROOT, 'webapp', ...p);
const FILES = ['edital-rules.js', 'seed.js'];

const args = process.argv.slice(2);
const WANT_JSON = args.includes('--json');
const QUIET = args.includes('--quiet');

function loadWebapp() {
  // Both files assign to a global `window`. Give them one and eval in a shared
  // context so edital-rules.js' validarProposta can see seed.js' ORCAMENTO_SEED.
  const sandbox = { window: {}, console };
  vm.createContext(sandbox);
  for (const f of FILES) {
    const p = WEBAPP(f);
    if (!fs.existsSync(p)) {
      throw new Error(`webapp file not found: ${p}`);
    }
    vm.runInContext(fs.readFileSync(p, 'utf8'), sandbox, { filename: f });
  }
  return sandbox.window;
}

function fmtBRL(v) {
  return 'R$ ' + Number(v || 0).toLocaleString('pt-BR', {
    minimumFractionDigits: 2, maximumFractionDigits: 2,
  });
}

function main() {
  const win = loadWebapp();
  const seed = win.ORCAMENTO_SEED;
  if (!seed || !seed.rubricas) {
    console.error('❌ ORCAMENTO_SEED não carregado de webapp/seed.js');
    process.exit(2);
  }
  const res = win.validarProposta(seed);

  const rubricaFailures = Object.entries(res.rubricas)
    .filter(([_, r]) => !r.ok);

  const passed =
    res.faixa_ok &&
    res.duracao_ok &&
    rubricaFailures.length === 0 &&
    !res.r4_eliminacao;

  if (WANT_JSON) {
    console.log(JSON.stringify({
      passed,
      total: res.total,
      faixa_ok: res.faixa_ok,
      duracao_ok: res.duracao_ok,
      r4_eliminacao: res.r4_eliminacao,
      valor_inabilitado: res.valor_inabilitado,
      pct_inabilitado: res.pct_inabilitado,
      rubrica_failures: rubricaFailures.map(([id, r]) => ({
        rubrica: id, valor: r.valor, pct: r.pct, motivos: r.motivos,
      })),
      globais: res.globais,
    }, null, 2));
  } else if (!QUIET || !passed) {
    console.log('═'.repeat(64));
    console.log(' AUDITORIA DE CONFORMIDADE — Edital FINEP AgriFam-ICT 2026');
    console.log('═'.repeat(64));
    console.log(` Total da proposta : ${fmtBRL(res.total)}  (faixa ${fmtBRL(win.EDITAL_RULES.faixa_min)} – ${fmtBRL(win.EDITAL_RULES.faixa_max)})`);
    console.log(` Duração           : ${seed.meta.duracao_meses} meses  (máx ${win.EDITAL_RULES.duracao_meses_max})`);
    console.log(` Faixa             : ${res.faixa_ok ? 'OK' : '❌ FORA'}`);
    console.log(` Duração           : ${res.duracao_ok ? 'OK' : '❌ >36m'}`);
    console.log(` R4 eliminação     : ${res.r4_eliminacao ? '❌ SIM (inabilitado >30%)' : 'OK'}  (inabilitado ${fmtBRL(res.valor_inabilitado)} = ${(res.pct_inabilitado * 100).toFixed(2)}%)`);
    console.log('─'.repeat(64));
    console.log(' Rubricas:');
    for (const [id, r] of Object.entries(res.rubricas)) {
      const tag = r.ok ? 'OK ' : '❌';
      const cap = r.cap && r.cap.pct !== null ? ` cap ${(r.cap.pct * 100).toFixed(0)}%` : '';
      console.log(`   ${tag} ${id.padEnd(12)} ${fmtBRL(r.valor).padStart(22)}  ${(r.pct * 100).toFixed(2)}%${cap}`);
      for (const m of (r.motivos || [])) console.log(`        ↳ ${m}`);
    }
    if (res.globais.length) {
      console.log('─'.repeat(64));
      console.log(' Globais:');
      for (const g of res.globais) console.log(`   ❌ ${g}`);
    }
    console.log('═'.repeat(64));
    console.log(passed ? ' ✅ CONFORME — proposta dentro de todas as regras do edital.' : ' ❌ NÃO CONFORME — corrigir antes de submeter.');
    console.log('═'.repeat(64));
  }

  process.exit(passed ? 0 : 1);
}

try {
  main();
} catch (e) {
  console.error(`❌ Falha ao executar auditoria: ${e.message}`);
  process.exit(2);
}
