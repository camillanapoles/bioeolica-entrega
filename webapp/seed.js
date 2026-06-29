// seed.js — Orçamento FINEP AgriFam-ICT 2026 v2.0 (R$7.000.000 / 36 m)
// SOURCE OF TRUTH: docs/projetos/orcamento-versionado-finep-agrifam.md
// "tipo" classifica a natureza do item p/ validação de categoria (ver edital-rules.js).

window.ORCAMENTO_SEED = {
  meta: {
    projeto: "Bioeólica (PM-15G + Savonius) — Linha 2",
    edital: "FINEP AgriFam-ICT 2026",
    versao: "v2.0 RETIFICADA",
    data_base: "2026-06-29",
    duracao_meses: 36,
    faixa_min: 1000000,
    faixa_max: 7000000
  },
  rubricas: [
    {
      id: "pessoal",
      nome: "Pessoal",
      item_edital: "6.5.5",
      teto_pct: 0.30,
      itens: [
        { id: "p1", descricao: "Coordenadora P&D integrado (DT3, 10h/sem, 1560h)", valor: 341500, tipo: "mao-de-obra" },
        { id: "p2", descricao: "Pesq. Materiais sênior Parte 1 (DT2, 16h/sem, 2496h)", valor: 447800, tipo: "mao-de-obra" },
        { id: "p3", descricao: "Pesq. Eletromecânica sênior Parte 2 (DT2, 16h/sem, 2496h)", valor: 447800, tipo: "mao-de-obra" },
        { id: "p4", descricao: "2× Apoio Técnico bancada (AT2, 20h/sem×2, 3120h×2)", valor: 373776, tipo: "mao-de-obra" },
        { id: "p5", descricao: "Reserva banco de horas / reajuste", valor: 189124, tipo: "mao-de-obra" }
      ]
    },
    {
      id: "bolsas",
      nome: "Bolsas",
      item_edital: "6.5.7",
      teto_pct: 0.30,
      itens: [
        { id: "b1", descricao: "2× Doutorado (SET D, 3250/mês, 36m×2)", valor: 234000, tipo: "mao-de-obra" },
        { id: "b2", descricao: "3× Mestrado (SET F, 2200/mês, 36m×3)", valor: 237600, tipo: "mao-de-obra" },
        { id: "b3", descricao: "3× Desenv. industrial DTI B (3900/mês, 24m×3)", valor: 280800, tipo: "mao-de-obra" },
        { id: "b4", descricao: "1× Especialista eólica/PMG EXP A (5200/mês, 18m)", valor: 93600, tipo: "mao-de-obra" },
        { id: "b5", descricao: "4× Iniciação científica SET H (1560/mês, 36m×4)", valor: 224640, tipo: "mao-de-obra" },
        { id: "b6", descricao: "1× Pós-doc júnior SET E (2600/mês, 24m)", valor: 62400, tipo: "mao-de-obra" },
        { id: "b7", descricao: "2× DTI apoio simulação/dados DTI C (1430/mês, 24m×2)", valor: 68640, tipo: "mao-de-obra" },
        { id: "b8", descricao: "Reserva renewal/cobertura de vagas", valor: 398320, tipo: "mao-de-obra" }
      ]
    },
    {
      id: "tp_pj",
      nome: "Serviços de TP PJ",
      item_edital: "6.5.2",
      teto_pct: null, // livre
      itens: [
        { id: "t1", descricao: "Ensaios mecânicos iterativos D638/D790/D256/D7774 + fluência E139 (5 ciclos)", valor: 180000, tipo: "servico" },
        { id: "t2", descricao: "Microestrutura iterativa MEV+EDS/TGA E1131/DSC D3418/FTIR E1252 (5 ciclos)", valor: 90000, tipo: "servico" },
        { id: "t3", descricao: "END iterativo ultrassom phased-array ISO 16811 + termografia E2582 (4 ciclos)", valor: 55000, tipo: "servico" },
        { id: "t4", descricao: "Envelhecimento longo UV G154/umidade D2247/salt-spray B117/ciclagem D6944 (3 ciclos)", valor: 95000, tipo: "servico" },
        { id: "t5", descricao: "PI nacional+internacional: INPI+PCT+fases US/EU/CN+procurador+anuidades", valor: 220000, tipo: "servico" },
        { id: "t6", descricao: "Ensaios Parte 2: túnel de vento + banco de carga + concretagem + bobinagem PMG", valor: 95000, tipo: "servico" },
        { id: "t7", descricao: "HPC/cloud computing FEM CalculiX/CFD OpenFOAM sob demanda (36m)", valor: 45000, tipo: "servico" },
        { id: "t8", descricao: "Logística de campo (hospedagem/fretes/capacitação) M12–M30", valor: 70000, tipo: "servico" }
      ]
    },
    {
      id: "material",
      nome: "Material de consumo",
      item_edital: "6.5.1",
      teto_pct: null, // livre
      itens: [
        { id: "m1", descricao: "Insumos PM-15G (papel reciclado/PVA/grafite mesh 325/água/EPI) — 2000 kg", valor: 42000, tipo: "insumo" },
        { id: "m2", descricao: "Bancada Parte 1 (balança/misturador/triturador/moldes ASTM/durômetro)", valor: 52000, tipo: "equipamento-menor" },
        { id: "m3", descricao: "Bancada Parte 2 (banco baterias 150Ah×30 + eletrônica NR-10 + instrumentação)", valor: 74000, tipo: "equipamento-menor" },
        { id: "m4", descricao: "Ferramental + reposição de moldes (5 ciclos)", valor: 38000, tipo: "insumo" },
        { id: "m5", descricao: "Reagentes + corpos-de-prova 36m (~1500 CP)", valor: 85000, tipo: "insumo" },
        { id: "m6", descricao: "Mantimentos de campo + capacitação comunitária (5 comunidades)", valor: 120000, tipo: "insumo" },
        { id: "m7", descricao: "Reserva robustez 36m (reposição/inflação/quebras)", valor: 339000, tipo: "insumo" }
      ]
    },
    {
      id: "equip",
      nome: "Equipamento permanente",
      item_edital: "6.6.1/6.6.2/2.1.24",
      teto_pct: null,
      itens: [
        { id: "e1", descricao: "Prensa hidráulica moldagem 50 t (≥R$50K) [6.6.1]", valor: 95000, tipo: "equipamento-maior" },
        { id: "e2", descricao: "Estufa secagem/cura 500 L (≥R$50K) [6.6.1]", valor: 62000, tipo: "equipamento-maior" },
        { id: "e3", descricao: "Máquina universal de ensaios 50 kN (≥R$50K) [6.6.1]", valor: 130000, tipo: "equipamento-maior" },
        { id: "e4", descricao: "Servidor/workstation HPC FEM/CFD (≥R$50K) [6.6.1]", valor: 90000, tipo: "equipamento-maior" },
        { id: "e5", descricao: "Bancada de testes PMG/eletrônica (≥R$50K) [6.6.1]", valor: 100000, tipo: "equipamento-maior" },
        { id: "e6", descricao: "Gerador Savonius ×6 (sistema composto: rotor+PMG+torre+eletrônica) [2.1.24]", valor: 75000, tipo: "equipamento-maior" },
        { id: "e7", descricao: "6× sistema de irrigação (<R$50K, lista permitida) [6.6.2]", valor: 100000, tipo: "equipamento-menor" },
        { id: "e8", descricao: "Nobreak + chiller + AC + casa de vegetação (<R$50K) [6.6.2]", valor: 98000, tipo: "equipamento-menor" }
      ]
    },
    {
      id: "obras",
      nome: "Obras",
      item_edital: "6.6.3",
      teto_pct: 0.10,
      teto_ambiente: 392952.63,
      itens: [
        { id: "o1", descricao: "Ambiente 1 — Lab Materiais (piso químico/elétrica 220V/exaustão NR-8/23 NBR 14725)", valor: 200000, tipo: "obra" },
        { id: "o2", descricao: "Ambiente 2 — Lab Eletromecânico (piso técnico/bancada mec.+eletrotéc. NR-10/18)", valor: 200000, tipo: "obra" },
        { id: "o3", descricao: "Sistema tratamento de efluentes (caixa separadora + filtração PVA CONAMA 430/2011)", valor: 50000, tipo: "obra" },
        { id: "o4", descricao: "Fundações das 6 unidades (concreto/fixação torre treliça 10m)", valor: 50000, tipo: "obra" }
      ]
    },
    {
      id: "operacional",
      nome: "Despesas operacionais",
      item_edital: "6.5.3",
      teto_pct: 0.05,
      teto_exacto: true, // =5% exato
      itens: [
        { id: "op1", descricao: "Energia + materiais escritório + comunicação + seguros + software", valor: 350000, tipo: "operacional" }
      ]
    },
    {
      id: "diarias",
      nome: "Diárias",
      item_edital: "6.5.6",
      teto_pct: 0.05,
      itens: [
        { id: "d1", descricao: "Campo 5 comunidades (M12–M30) + internac. congressos 2×", valor: 200000, tipo: "diaria" }
      ]
    },
    {
      id: "passagens",
      nome: "Passagens",
      item_edital: "6.5.6",
      teto_pct: 0.05,
      itens: [
        { id: "pa1", descricao: "Nacionais PE/BA/GO + congressos BR + internac. COP-31/32", valor: 200000, tipo: "passagem" }
      ]
    }
  ]
};
