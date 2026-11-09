#!/usr/bin/env python3
"""
Black Earth Commercial Intelligence OS — Database & Seed Module
Implementa o schema completo (Seção 6 da Base de Conhecimento) e popula com os
dados estruturados de Diagnostico.docx, Analise_Mercado.xlsx, PPTX e Knowledge Base.
"""

import json
import os
import sqlite3
from datetime import datetime, timezone

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "black_earth_os.db")


def get_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            family TEXT NOT NULL,
            form TEXT NOT NULL,
            humic_acid_spec TEXT,
            fulvic_acid_spec TEXT,
            cec_meq TEXT,
            solubility TEXT,
            ash_content TEXT DEFAULT '11% (Humalite Sheerness/AB)',
            heavy_metals TEXT DEFAULT 'Cd 0,1 / Pb 3 / As 1 ppm (abaixo IN 61/2020)',
            dose_per_ha REAL NOT NULL,
            unit TEXT NOT NULL,
            unit_price_brl REAL NOT NULL,
            freight_per_ha_brl REAL NOT NULL,
            strategic_role TEXT NOT NULL,
            priority_tier TEXT NOT NULL,
            target_crops TEXT NOT NULL,
            target_markets TEXT NOT NULL,
            recommended_channel TEXT NOT NULL,
            regulatory_gate TEXT NOT NULL,
            regulatory_status TEXT NOT NULL,
            urea_compatibility_note TEXT
        );

        CREATE TABLE IF NOT EXISTS market_parameters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            unit TEXT NOT NULL,
            value REAL NOT NULL,
            base_response_kg_ha REAL DEFAULT 188.0,
            updated_at TEXT NOT NULL,
            source TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS soil_problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem_name TEXT NOT NULL,
            crop TEXT NOT NULL,
            estimated_loss_brl_ha REAL NOT NULL,
            calculation_basis TEXT NOT NULL,
            black_earth_mechanism TEXT NOT NULL,
            recommended_sku TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            brand TEXT,
            cnpj_status TEXT,
            channel_type TEXT NOT NULL,
            uf TEXT NOT NULL,
            region TEXT NOT NULL,
            priority_uf TEXT NOT NULL,
            crops TEXT NOT NULL,
            key_leader_name TEXT,
            key_leader_role TEXT,
            entry_door_role TEXT NOT NULL,
            recommended_skus TEXT NOT NULL,
            fit_score INTEGER NOT NULL,
            volume_score INTEGER NOT NULL,
            access_score INTEGER NOT NULL,
            regulatory_score INTEGER NOT NULL,
            tech_score INTEGER NOT NULL,
            ops_score INTEGER NOT NULL,
            total_score INTEGER NOT NULL,
            pipeline_stage TEXT NOT NULL,
            provenance_status TEXT NOT NULL,
            next_action TEXT NOT NULL,
            notes TEXT,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS competitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_product TEXT UNIQUE NOT NULL,
            origin_tech TEXT NOT NULL,
            formulation TEXT NOT NULL,
            public_dose TEXT NOT NULL,
            dose_profile TEXT NOT NULL,
            public_price_brl TEXT NOT NULL,
            estimated_cost_ha_brl REAL,
            ash_estimate TEXT NOT NULL,
            black_earth_counter_sku TEXT NOT NULL,
            competitive_reading TEXT NOT NULL,
            defense_argument TEXT NOT NULL,
            source TEXT NOT NULL,
            checked_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS market_news_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            impact_level TEXT NOT NULL,
            affected_agent TEXT NOT NULL,
            recommended_action TEXT NOT NULL,
            source_name TEXT NOT NULL,
            source_url TEXT NOT NULL,
            published_at TEXT NOT NULL,
            is_automated INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS campaigns_playbooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            target_channel TEXT NOT NULL,
            target_interlocutor TEXT NOT NULL,
            sku_focus TEXT NOT NULL,
            cadence_step TEXT NOT NULL,
            subject_line TEXT NOT NULL,
            message_body TEXT NOT NULL,
            required_attachments TEXT NOT NULL,
            compliance_gate_status TEXT NOT NULL,
            human_approval_status TEXT DEFAULT 'Pendente Aprovação (AgroRemoto)',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS events_calendar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_name TEXT UNIQUE NOT NULL,
            location TEXT NOT NULL,
            event_date TEXT NOT NULL,
            deadline_alert TEXT NOT NULL,
            priority_level TEXT NOT NULL,
            strategic_goal TEXT NOT NULL,
            target_skus TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS automation_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_code TEXT UNIQUE NOT NULL,
            job_name TEXT NOT NULL,
            agent_owner TEXT NOT NULL,
            cron_expression TEXT NOT NULL,
            frequency_label TEXT NOT NULL,
            description TEXT NOT NULL,
            last_run_at TEXT,
            next_run_at TEXT,
            last_status TEXT DEFAULT 'READY',
            items_processed INTEGER DEFAULT 0,
            enabled INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS automation_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_code TEXT NOT NULL,
            agent_name TEXT NOT NULL,
            started_at TEXT NOT NULL,
            completed_at TEXT NOT NULL,
            status TEXT NOT NULL,
            summary TEXT NOT NULL,
            output_json TEXT NOT NULL,
            report_path TEXT
        );
        """
    )

    # Check if already seeded
    cur.execute("SELECT COUNT(*) as cnt FROM products")
    if cur.fetchone()["cnt"] == 0:
        seed_initial_data(cur)

    conn.commit()
    conn.close()


def seed_initial_data(cur):
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # 1. Products (11 SKUs from Analise_Mercado.xlsx + Diagnostico.docx + Knowledge Base)
    products = [
        (
            "Fuze DS",
            "humiZEN",
            "Pó 100% Solúvel",
            "60% ISO",
            "Incluso em HS",
            "275 meq/100g",
            "100% solúvel (129 g/L = Liquid Carbon)",
            "11% (vs 36-85% leonardita)",
            "Cd 0,1 / Pb 3 / As 1 ppm",
            1.0,
            "kg",
            68.00,
            12.00,
            "Onda 1 — Escala B2B / OEM / Formulação Local",
            "A1",
            "Soja, Milho, Cana, Algodão, Café, HF",
            "Brasil (A1), Argentina, Paraguai, Peru, Chile, Colômbia",
            "Fabricantes de fertilizantes especiais, OEM, Private Label",
            "Gate R1/R2 (Ingrediente B2B / SIPEAGRO)",
            "Prioridade de habilitação B2B",
            "Alta compatibilidade em formulações líquidas; validar pH antes de mistura ácida extrema."
        ),
        (
            "Alpha",
            "humiZEN",
            "Líquido Concentrado",
            "2,0% ISO (3,5% colorim.)",
            "3,5% fúlvico",
            "290 meq/100g",
            "Líquido pronto para sulco/foliar",
            "11% base mineral",
            "Cd 0,1 / Pb 3 / As 1 ppm",
            2.5,
            "L",
            42.00,
            12.00,
            "Onda 1 — Abertura de Mercado e Geração de Demanda",
            "A1",
            "Soja, Milho, Algodão, Café, HF, Tomate, Citros, Cana",
            "Brasil (A1), Peru, Chile, Colômbia, Equador",
            "Distribuidores especializados, Cooperativas e Contas Âncora",
            "Gate R1/R3 (Condicionador/Biofertilizante MAPA)",
            "Em preparação de dossiê e ensaios DBC",
            "Baixa dose (0,58-1,2 L/ha sulco; 1,5-2,5 L/ha foliar). Apresentar teste de jarro proativamente."
        ),
        (
            "Magna",
            "humiZEN",
            "Granular Semi-Solúvel",
            "50% ISO",
            "Incluso em HS",
            "240 meq/100g",
            "~60% solúvel",
            "11% base mineral",
            "Cd 0,1 / Pb 3 / As 1 ppm",
            18.0,
            "kg",
            4.40,
            12.00,
            "Onda 1 — Fertilizer Enhancement / Blend NPK",
            "A1/A2",
            "Soja, Milho, Algodão, Cana",
            "Brasil, Argentina, Paraguai",
            "Misturadores de fertilizantes, Indústrias NPK, Co-desenvolvimento",
            "Gate R1/R2 (Aditivo/Condicionador para blend)",
            "Requer validação analítica dos 60% solúvel e teste industrial",
            "ATENÇÃO: Declarar regras estritas de umidade ao misturar com ureia (premix 5-20%)."
        ),
        (
            "XP100",
            "humaLITE",
            "Pó Microfino (<200 mesh)",
            "55-60% ISO",
            "Incluso em HS",
            "256 meq/100g",
            "Insolúvel (suspensão/recobrimento/processo)",
            "11% (baixa sílica abrasiva)",
            "Cd 0,1 / Pb 3 / As 1 ppm",
            1.0,
            "kg",
            62.00,
            12.00,
            "Onda 1 — Matéria-Prima Industrial / Recobrimento e Extração",
            "A2",
            "Soja, Milho, Cana, Café, Especialidades (via indústria)",
            "Brasil, Argentina",
            "Indústrias químicas/fertilizantes, Organominerais, Formuladores",
            "Gate R0/R2 (Matéria-prima industrial)",
            "Viável para cotação industrial B2B com COA por lote",
            "Ideal para recobrimento de grânulos e reação alcalina industrial."
        ),
        (
            "MP30",
            "humaLITE",
            "Mini-Granular (<1 mm)",
            "55% ISO",
            "Incluso em HS",
            "185 meq/100g",
            "Matriz de liberação gradual / extração",
            "11% base mineral",
            "Cd 0,1 / Pb 3 / As 1 ppm",
            100.0,
            "kg",
            4.60,
            25.00,
            "Onda 1 — Ingrediente para Organominerais e Extração",
            "A2",
            "Cana, Café, Soja/Milho (via organomineral industrial)",
            "Brasil, Argentina, Paraguai",
            "Fabricantes de organominerais e condicionadores de solo",
            "Gate R0/R2 (Ingrediente B2B)",
            "Foco estrito B2B industrial (inviável isolado a lanço em soja)",
            "Sem restrição em compostagem/organomineral peletizado."
        ),
        (
            "Keal",
            "humiZEN",
            "Líquido Fúlvico Premium",
            "0,3% ISO",
            "3,45% fúlvico ISO",
            "325 meq/100g",
            "100% solúvel foliar/fertirrigação",
            "<2% em solução",
            "Cd 0,1 / Pb 3 / As 1 ppm",
            1.0,
            "L",
            95.00,
            18.00,
            "Onda 2 — Especialidades / Café, HF, Citros e Frutas Exportação",
            "B1",
            "Café (ROI 11x-23x), Tomate, HF, Citros, Uva, Frutas Irrigadas",
            "Brasil (MG/SP/BA), Peru, Chile, Colômbia",
            "Cooperativas de café (Cooxupé/Minasul) e Distribuidores Specialty",
            "Gate R1/R3 (Foliar / Condicionador)",
            "Alta atratividade econômica em Café e HF",
            "Excelente compatibilidade em calda foliar e fertirrigação."
        ),
        (
            "Liquid Carbon HC",
            "humaPLUS",
            "Líquido Alta Concentração",
            "24% colorimétrico",
            "Incluso",
            "260 meq/100g",
            "Líquido concentrado (diluição 1:1 = LC)",
            "11% base mineral",
            "Cd 0,1 / Pb 3 / As 1 ppm",
            4.7,
            "L",
            38.00,
            12.00,
            "Onda 1/2 — Cana-de-Açúcar, UAN/Ureia e Grandes Contas",
            "A2",
            "Cana-de-açúcar (soqueira/reforma), Milho, Algodão, Café",
            "Brasil (SP/GO/MT), Argentina, Paraguai",
            "Usinas de cana, Indústria de fertilizantes fluidos",
            "Gate R1/R3",
            "Superior ao LC padrão em logística internacional",
            "Apresentar protocolo de compatibilidade com UAN/ureia líquida."
        ),
        (
            "Liquid Carbon",
            "humaPLUS",
            "Líquido Demonstrador",
            "12% colorimétrico",
            "Incluso",
            "220 meq/100g",
            "Líquido pronto para sulco/irrigação",
            "11% base mineral",
            "Cd 0,1 / Pb 3 / As 1 ppm",
            9.4,
            "L",
            22.00,
            12.00,
            "Onda 1 — Prova Agronômica / Trials (migrar escala para Fuze DS)",
            "A2",
            "Soja, Milho, Cana, Algodão, Café, HF",
            "Brasil (Fundações de pesquisa e áreas piloto)",
            "Fundações de pesquisa (MT, Rio Verde, ABC, Chapadão) e Contas Âncora",
            "Gate R3 (Amostragem/Ensaios experimentais)",
            "Uso focado em validação agronômica; substituir por Fuze DS na escala",
            "Requer teste de jarro em misturas com calda ácida."
        ),
        (
            "GG16",
            "humaLITE",
            "Granular Fino (1–2 mm)",
            "55-60% ISO",
            "Incluso",
            "210 meq/100g",
            "Liberação gradual no sulco",
            "11% base mineral",
            "Cd 0,1 / Pb 3 / As 1 ppm",
            60.0,
            "kg",
            3.60,
            12.00,
            "Onda 2 — Substituição Parcial de MAP (20%) no Sulco",
            "B2",
            "Soja em solos com alta fixação de P, Batata, HF, Café",
            "Brasil (projetos de substituição de MAP)",
            "Cooperativas e Grandes Contas (venda por substituição de adubo)",
            "Gate R1 (Condicionador de solo)",
            "Só ofertar em grãos acoplado à redução de 20% de MAP (ROI 1,35x)",
            "Não misturar diretamente com ureia higroscópica sem condicionante."
        ),
        (
            "AG4",
            "humaLITE",
            "Granular Grosso (2–5 mm)",
            "60% ISO",
            "Incluso",
            "200 meq/100g",
            "Condicionador sólido de longo prazo (pH 3-4)",
            "11% base mineral",
            "Cd 0,1 / Pb 3 / As 1 ppm",
            150.0,
            "kg",
            2.60,
            25.00,
            "Onda 2 — Nichos: Café, Substratos, Horticultura e Turf",
            "C",
            "Café (ROI 3,03x), Substratos, Turf/Gramados, Recuperação ambiental",
            "Brasil (nichos B2B de substratos e café premium)",
            "Fabricantes de substratos (Holambra/SP/RS) e Cafeicultura",
            "Gate R1 (Condicionador de solo / Substrato)",
            "PROIBIDO ofertar isolado a lanço em soja (ROI 0,47x — Semáforo Vermelho)",
            "Aplicação exclusiva em solo/substrato."
        ),
        (
            "Dual Action",
            "humaPLUS",
            "Granular Blend (70% AG4 + 30% Magna)",
            "50% ISO",
            "Incluso",
            "215 meq/100g",
            "25% solúvel imediato + 75% lento",
            "11% base mineral",
            "Cd 0,1 / Pb 3 / As 1 ppm",
            140.0,
            "kg",
            3.20,
            25.00,
            "Onda 2 — Culturas Perenes/Premium Seletivas",
            "C",
            "Café, Citros, Fruticultura de alto valor",
            "Peru, Chile, Nichos Brasil",
            "Projetos especiais de alto valor por hectare",
            "Gate R0 (Documentação complementar pendente)",
            "Aguardando ficha técnica consolidada para registro",
            "Observar compatibilidade física com NPK granulado."
        ),
    ]
    cur.executemany(
        """
        INSERT INTO products (
            sku, family, form, humic_acid_spec, fulvic_acid_spec, cec_meq,
            solubility, ash_content, heavy_metals, dose_per_ha, unit,
            unit_price_brl, freight_per_ha_brl, strategic_role, priority_tier,
            target_crops, target_markets, recommended_channel, regulatory_gate,
            regulatory_status, urea_compatibility_note
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        products,
    )

    # 2. Market Parameters (Bloco 1 de Diagnostico.docx)
    params = [
        ("P_SOJA", "Soja em grão", "Commodity", "R$/kg", 2.083, 188.0, now_iso, "Diagnostico.docx / CEPEA ref"),
        ("P_MILHO", "Milho em grão", "Commodity", "R$/kg", 1.133, 360.0, now_iso, "Diagnostico.docx / CEPEA ref"),
        ("P_ALG", "Algodão pluma", "Commodity", "R$/kg", 9.670, 95.0, now_iso, "Diagnostico.docx / CEPEA ref"),
        ("P_CAFE", "Café arábica beneficiado", "Commodity", "R$/kg", 23.330, 90.0, now_iso, "Diagnostico.docx / Cooxupé ref"),
        ("P_CANA", "Cana-de-açúcar (ATR)", "Commodity", "R$/kg ATR", 0.145, 4200.0, now_iso, "Diagnostico.docx / Consecana ref"),
        ("P_BATATA", "Batata lavada", "Commodity", "R$/kg", 2.200, 1800.0, now_iso, "Diagnostico.docx / HF ref"),
        ("P_TRIGO", "Trigo pão", "Commodity", "R$/kg", 1.250, 240.0, now_iso, "Diagnostico.docx / PR-RS ref"),
        ("P_MAP", "Fertilizante MAP (52% P2O5)", "Insumo", "R$/kg", 3.200, 0.0, now_iso, "Diagnostico.docx Aba Substituição"),
        ("F_GRAN", "Frete granulado a lanço", "Logística", "R$/ha", 25.00, 0.0, now_iso, "Diagnostico.docx"),
        ("F_LIQ", "Frete/aplicação sulco líquido", "Logística", "R$/ha", 12.00, 0.0, now_iso, "Diagnostico.docx"),
        ("F_FOL", "Frete/aplicação foliar", "Logística", "R$/ha", 18.00, 0.0, now_iso, "Diagnostico.docx"),
        ("F_OP", "Custo de oportunidade capital", "Financeiro", "%/mês", 1.10, 0.0, now_iso, "Diagnostico.docx"),
        ("HAIRCUT", "Haircut de resposta (Canadá→Brasil)", "Agronômico", "fator", 0.60, 0.0, now_iso, "Diagnostico.docx"),
        ("HAIRCUT_G", "Haircut granulado a lanço", "Agronômico", "fator", 0.50, 0.0, now_iso, "Diagnostico.docx"),
        ("USD_BRL", "Taxa de Câmbio USD/BRL", "Financeiro", "R$/US$", 5.45, 0.0, now_iso, "Simulador Landed Cost"),
    ]
    cur.executemany(
        """
        INSERT INTO market_parameters (code, name, category, unit, value, base_response_kg_ha, updated_at, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        params,
    )

    # 3. Soil Problems (Bloco 5 de Diagnostico.docx — "Custo do Problema")
    problems = [
        (
            "Al³⁺ > 0,5 cmolc/dm³ em subsuperfície (perda 8% em soja)",
            "Soja / Grãos",
            208.30,
            "3.100 kg/ha × R$ 2,083/kg × 8% perda de produtividade",
            "Complexação orgânica de Al³⁺ tóxico e estímulo radicular em profundidade (acidez total 7,0 mmol/g)",
            "Alpha (2,5 L/ha) ou Fuze DS (1,0 kg/ha) no sulco"
        ),
        (
            "Fósforo (P) fixado em Latossolo (25% de 104 kg P2O5 travado em Fe/Al)",
            "Soja / Milho / Algodão",
            159.90,
            "26 kg P2O5 bloqueados × R$ 6,15/kg equivalente",
            "Bloqueio de sítios de adsorção de Fe/Al por humatos de alta CTC (275 meq/100g), permitindo reduzir 20% do MAP",
            "Magna (18 kg/ha), Fuze DS (1 kg/ha) ou GG16 (60 kg/ha c/ substituição MAP)"
        ),
        (
            "Compactação e baixa agregação física (perda 5% em milho safrinha)",
            "Milho / Sucessão Soja-Milho",
            101.70,
            "9.000 kg/ha × R$ 1,133/kg × 5% perda por restrição hídrica/radicular",
            "Formação de complexos argilo-húmicos e exsudação radicular que aumentam macroporosidade",
            "Liquid Carbon HC (4,7 L/ha) ou Magna (18 kg/ha)"
        ),
        (
            "Replantio de soja por perda de stand / veranico inicial",
            "Soja (MT, GO, MAPITOBA, BA)",
            320.00,
            "Custo operacional + semente adicional + perda de janela ideal da safrinha",
            "Estímulo hormonal auxínico-like das frações fúlvicas/húmicas de baixo peso molecular no arranque",
            "Alpha (1,0 L/ha sulco + 1,5 L/ha foliar)"
        ),
        (
            "Reforma antecipada de canavial por queda de vigor de soqueira",
            "Cana-de-açúcar (SP, GO, MG, MS)",
            900.00,
            "R$ 4.500/ha de reforma amortizados em 5 cortes = R$ 900/ha/ano",
            "Recuperação do sistema radicular de soqueira e complexação de nutrientes junto ao corte de soqueira/vinhaça",
            "Liquid Carbon HC (4,7 L/ha) ou Fuze DS formulado"
        ),
    ]
    cur.executemany(
        """
        INSERT INTO soil_problems (problem_name, crop, estimated_loss_brl_ha, calculation_basis, black_earth_mechanism, recommended_sku)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        problems,
    )

    # 4. Organizations / Target Accounts (from Diagnostico.docx & Knowledge Base)
    orgs = [
        (
            "Vittia S.A.",
            "Vittia Fertilizantes e Biológicos",
            "CNPJ Ativo (B3: VITT3)",
            "OEM / Formulador Industrial",
            "SP",
            "Sudeste / Nacional",
            "P1",
            "Soja, Milho, Cana, Café, Citros",
            "Wilson Fernando Romanini",
            "CEO / Diretoria P&D e Suprimentos",
            "Diretor de P&D / Gerente de Suprimentos Industriais",
            "Fuze DS, XP100, MP30, Magna",
            25, 19, 14, 14, 15, 9, 96,
            "Empresa Qualificada",
            "Confirmado (Documento Diagnóstico Camada 2-C)",
            "Enviar dossiê B2B de custo por kg de HS efetivo (11% cinza + metais pesados abaixo IN 61/2020) e amostra de Fuze DS/XP100",
            "Modelo recomendado para Ano 1: volume imediato, zero custo de estrutura de campo.",
            now_iso
        ),
        (
            "Cooxupé — Cooperativa Regional de Cafeicultores em Guaxupé",
            "Cooxupé",
            "CNPJ Ativo — Maior coop de café do mundo",
            "Cooperativa",
            "MG",
            "Sul/Sudoeste de Minas e Cerrado",
            "P1",
            "Café Arábica (18 mil cooperados)",
            "Carlos Augusto Rodrigues de Melo (Pres.) / Mário Ferraz de Araújo",
            "Gerente do Dep. de Desenvolvimento Técnico (+200 agrônomos)",
            "Gerente de Desenvolvimento Técnico (Mário Ferraz) e Gerente de Insumos",
            "Keal, Alpha, AG4",
            25, 19, 15, 13, 15, 9, 96,
            "Decisor Identificado",
            "Confirmado (Diagnóstico Parte 2 — MG)",
            "Apresentar protocolo DBC em café (break-even de apenas 0,08 sc/ha para Keal 1 L/ha, ROI > 11x)",
            "Café é a cultura com melhor ROI de todo o dossiê Black Earth no Brasil.",
            now_iso
        ),
        (
            "COMIGO — Cooperativa Agroindustrial dos Produtores Rurais do Sudoeste Goiano",
            "Comigo",
            "CNPJ Ativo — Rio Verde/GO",
            "Cooperativa",
            "GO",
            "Centro-Oeste (Sudoeste Goiano)",
            "P1",
            "Soja, Milho, Sorgo, Algodão",
            "Antonio Chavaglia",
            "Presidente / Coordenação Técnica do ITC Comigo",
            "Coordenador Técnico ITC Comigo e Gerente de Insumos (nunca diretoria primeiro)",
            "Fuze DS, Alpha, Magna",
            24, 19, 14, 13, 14, 9, 93,
            "Decisor Identificado",
            "Confirmado (Diagnóstico Parte 2 — GO)",
            "Submeter protocolo de ensaio para Tecnoshow Comigo 2027 (janela fecha em 60 dias) + reunião 40 min",
            "Porta mais eficiente do Centro-Oeste: 1 cooperativa, milhares de cooperados e dia de campo próprio.",
            now_iso
        ),
        (
            "Coamo Agroindustrial Cooperativa",
            "Coamo",
            "CNPJ Ativo — Faturamento R$ 26,8 bi (Forbes Agro100)",
            "Cooperativa",
            "PR",
            "Sul (PR / SC / MS)",
            "P1",
            "Soja, Milho, Trigo, Café",
            "José Aroldo Gallassini",
            "Presidente do Conselho / Gerência Técnica e Fazenda Experimental",
            "Coordenador Técnico da Fazenda Experimental Coamo + Gerente de Insumos",
            "Alpha, Fuze DS, Magna, GG16 (substituição 20% MAP)",
            25, 20, 12, 13, 14, 8, 92,
            "Empresa Qualificada",
            "Confirmado (Diagnóstico Camada 2-B / PR)",
            "Agendar apresentação técnica com foco em bloqueio de fixação de P e redução de 20% MAP",
            "Maior cooperativa do Brasil; exige registro MAPA impecável e ensaio em fundação regional.",
            now_iso
        ),
        (
            "Brandt do Brasil / Atlântica Agrícola / ILSA Brasil (Cluster OEM)",
            "Brandt / Atlântica / ILSA",
            "Indústrias de Fertilizantes Especiais Estabelecidas",
            "OEM / Formulador Industrial",
            "SP",
            "Sudeste / Sul / Centro-Oeste",
            "P1",
            "Soja, Milho, HF, Citros, Café, Algodão",
            "Diretorias Técnicas e Industriais no Brasil",
            "Diretor Industrial / P&D de Formulações",
            "Comprador Técnico Industrial e Químico Responsável",
            "Fuze DS, XP100, MP30, Liquid Carbon HC",
            24, 18, 13, 14, 14, 9, 92,
            "Empresa Qualificada",
            "Confirmado (Diagnóstico Camada 2-C)",
            "Enviar comparativo de solubilidade Fuze DS (129 g/L) vs Leonardita comum e laudo ISO 19822",
            "Foco em fornecimento de ingrediente concentrado para linha private label / co-branded.",
            now_iso
        ),
        (
            "Raízen S.A. / Copersucar / São Martinho (Polo Sucroenergético SP)",
            "Raízen / Copersucar / São Martinho",
            "Líderes globais em Cana-de-Açúcar e Bioenergia",
            "Conta Âncora / Usinas Cana",
            "SP",
            "Sudeste (Interior Paulista)",
            "P1",
            "Cana-de-açúcar (Soqueira e Reforma)",
            "Ricardo Mussa (Raízen) / Tomás Manzano (Copersucar) / Fabio Venturelli (São Martinho)",
            "CEOs / Gerentes Corporativos de Desenvolvimento Agronômico",
            "Gerente Agronômico de Tratos Culturais e Nutrição de Soqueira",
            "Liquid Carbon HC, Fuze DS, Magna, Alpha",
            23, 20, 12, 13, 14, 8, 90,
            "Decisor Identificado",
            "Confirmado (Diagnóstico Parte 2 — SP)",
            "Abordar com tese de Custo do Problema: evitar reforma antecipada de canavial (R$ 900/ha/ano) + ATR",
            "Ticket médio altíssimo; validar compatibilidade com vinhaça e fertilizantes nitrogenados líquidos.",
            now_iso
        ),
        (
            "Fundação MT / Fundação Rio Verde / Fundação ABC / Fundação Chapadão",
            "Rede de Fundações de Pesquisa",
            "Instituições de Validação Oficial de Campo",
            "Parceiro Técnico / Pesquisa",
            "MT",
            "MT / PR / MS / BA",
            "P1",
            "Soja, Milho Safrinha, Algodão",
            "Coordenações de Solos e Nutrição de Plantas",
            "Pesquisador Sênior de Fertilidade do Solo",
            "Coordenador de Pesquisas de Solos (contratação de protocolo DBC)",
            "Alpha, Fuze DS, Magna, Liquid Carbon",
            24, 16, 15, 15, 15, 9, 94,
            "Abordagem Autorizada",
            "Confirmado (Diagnóstico Camada 1 — Regra de Ouro)",
            "Contratar protocolo DBC de 6 locais nas 3 regiões de grãos antes de contratar vendedor",
            "Regra do Diagnóstico: 1 ensaio publicado em fundação regional abre cooperativas e produtores > 5.000 ha.",
            now_iso
        ),
        (
            "UENF (Lab. Prof. Luciano Canellas) & Embrapa Solos",
            "UENF / Embrapa Solos",
            "Referência Mundial em Substâncias Húmicas no Brasil",
            "Parceiro Técnico / Pesquisa",
            "RJ",
            "Nacional (RJ)",
            "P1",
            "Todas as culturas (Mecanismo fisiológico e fracionamento ISO 19822)",
            "Prof. Luciano Canellas (UENF) / Chefia P&D Embrapa Solos",
            "Pesquisador Líder em Ácidos Húmicos e Bactérias Diazotróficas",
            "Contato acadêmico/P&D direto com laudo de espectroscopia e fracionamento ISO 19822",
            "Fuze DS, Alpha, Keal, XP100",
            24, 15, 14, 15, 15, 9, 92,
            "Decisor Identificado",
            "Confirmado (Diagnóstico Camada 1)",
            "Propor convênio de caracterização molecular da Humalite canadense + co-inoculação com bioinsumos",
            "Compra credibilidade científica que nenhum orçamento de marketing substitui.",
            now_iso
        ),
        (
            "C.Vale / Lar Cooperativa / Cocamar (Cluster Cooperativas PR)",
            "C.Vale / Lar / Cocamar",
            "Top 5 Cooperativas Agro Brasil (R$ 24+ bi cada)",
            "Cooperativa",
            "PR",
            "Sul e Mato Grosso do Sul",
            "P1",
            "Soja, Milho, Trigo, Mandioca, Citros",
            "Edio José Schreiner (C.Vale) / Irineo da Costa Rodrigues (Lar) / Luiz Lourenço (Cocamar)",
            "Presidentes / Coordenação de Agronomia e Difusão Técnica",
            "Coordenador Técnico e Gerente de Insumos",
            "Alpha, Fuze DS, Magna",
            23, 19, 12, 13, 14, 8, 89,
            "Empresa Mapeada",
            "Confirmado (Diagnóstico Parte 2 — PR)",
            "Preparar kit Agrônomo de Cooperativa (planilha break-even + matriz de incompatibilidade + laudo)",
            "Priorizar entrada via área demonstrativa em milho safrinha e soja.",
            now_iso
        ),
        (
            "Sinagro / Agrológica / Produtecnica (Distribuidores Regionais Centro-Oeste)",
            "Sinagro / Agrológica / Produtecnica",
            "Líderes de Distribuição Técnica em MT, GO, MS e BA",
            "Distribuidor Técnico",
            "MT",
            "Centro-Oeste e MATOPIBA",
            "P1",
            "Soja, Milho, Algodão",
            "Antonio Botelho (CEO Agrológica) / Diretoria Técnica Sinagro",
            "Diretor Comercial e Gerente de Portfólio de Especialidades",
            "Gerente de Produtos Especialidades / Nutrição de Solo",
            "Alpha, Keal, Fuze DS",
            22, 18, 13, 12, 13, 8, 86,
            "Decisor Identificado",
            "Confirmado (Diagnóstico Parte 2 — GO/MT/BA)",
            "Apresentar argumento de giro por hectare + margem de canal + amarração com crédito RenovAgro/Barter",
            "Foco nos 3 estados prioritários (MT, GO e MG) antes de expandir para 8 estados.",
            now_iso
        ),
        (
            "SLC Agrícola / Grupo Bom Futuro / Amaggi (Contas Âncora Grãos & Algodão)",
            "SLC / Bom Futuro / Amaggi",
            "Mega Grupos Produtivos (>500.000 ha cada)",
            "Conta Âncora",
            "MT",
            "MT / BA / MA / MS",
            "P1",
            "Algodão, Soja, Milho",
            "Aurélio Pavinato (CEO SLC) / Eraí Maggi (Bom Futuro)",
            "Diretoria de Operações Agrícolas e Gerência de Pesquisa Interna",
            "Agrônomo de Fazenda / Coordenador de Pesquisa Agronômica Interna (com Gerente em cópia)",
            "Alpha, Keal, Fuze DS, Liquid Carbon HC",
            23, 20, 11, 12, 14, 8, 88,
            "Decisor Identificado",
            "Confirmado (Diagnóstico Parte 2 — MT/BA)",
            "Propor talhão demonstrativo de 20 ha em área com histórico de Al³⁺ ou fixação de P; foco em algodão e soja",
            "Algodão na BA e MT tem alto valor por ha e absorve perfeitamente Alpha e Keal.",
            now_iso
        ),
    ]
    cur.executemany(
        """
        INSERT INTO organizations (
            name, brand, cnpj_status, channel_type, uf, region, priority_uf,
            crops, key_leader_name, key_leader_role, entry_door_role,
            recommended_skus, fit_score, volume_score, access_score,
            regulatory_score, tech_score, ops_score, total_score,
            pipeline_stage, provenance_status, next_action, notes, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        orgs,
    )

    # 5. Competitors (from Sheet 3 of Analise_Mercado.xlsx)
    competitors = [
        (
            "HGS BioScience — HumiK WSP",
            "Leonardita canadense extraída/ativada",
            "Pó 100% solúvel (~70% AH + 12–15% AF declarados)",
            "1–7 kg/ha",
            "Baixa–média",
            "R$ 158,90/kg (varejo pequena emb.)",
            158.90,
            "25–40% cinza estimada em humato alcalino",
            "Fuze DS (R$ 68/kg | 1 kg/ha = R$ 80/ha entregue)",
            "Concorrente mais direto da Black Earth: origem canadense, estoque no Brasil, pó concentrado e foco B2B em fertilizantes.",
            "Posicionar Fuze DS por custo/ha inferior (R$ 80/ha vs R$ 158+/ha), rastreabilidade ISO 19822 por lote e índice salino menor que humatos de K.",
            "Analise_Mercado.xlsx (Sheet 3)",
            now_iso
        ),
        (
            "HGS BioScience — Granulado Multidispersivo",
            "Leonardita canadense",
            "Granulado solúvel para mistura NPK",
            "1–7 kg/ha",
            "Baixa–média",
            "Sob consulta (B2B)",
            120.00,
            "~30% cinza",
            "Magna (18 kg/ha = R$ 91,20/ha | 60% solúvel)",
            "Já vende a tese 'húmico dentro do fertilizante' para misturadoras no Brasil.",
            "Demonstrar sinergia de Magna em premix 5–20% com CTC de 240 meq/100g e protocolo claro de umidade com ureia.",
            "Analise_Mercado.xlsx (Sheet 3)",
            now_iso
        ),
        (
            "Rigrantec — BioGain Húmico 80",
            "Leonardita (Humato de Potássio)",
            "Pó concentrado solúvel",
            "3–5 kg/ha",
            "Baixa",
            "R$ 118,63/kg (ou 8×1 kg por R$ 454,23 = R$ 56,78/kg)",
            227.00,
            "35–50% cinza / alto K alcalino",
            "Fuze DS (1 kg/ha = R$ 80/ha) e XP100 (R$ 74/ha)",
            "Registrado no MAPA com forte presença digital e transparência de preço.",
            "Na dose recomendada de 3–5 kg/ha, o BioGain custa R$ 170 a R$ 280/ha; Fuze DS resolve com 1 kg/ha (R$ 80/ha) e menor índice salino.",
            "Analise_Mercado.xlsx (Sheet 3)",
            now_iso
        ),
        (
            "Rigrantec — BioGain Húmico Líquido",
            "Leonardita (Humato de K líquido)",
            "Líquido para sulco/foliar",
            "3–5 L/ha sulco; 5 L/ha foliar",
            "Baixa",
            "R$ 43,97/L (1L) ou R$ 28,10/L (em 20L)",
            140.50,
            "Alta carga de potássio alcalino",
            "Alpha (1,0–2,5 L/ha = R$ 54 a R$ 117/ha)",
            "Competidor direto de entrada para líquidos com preço público transparente.",
            "Alpha trabalha com 0,58–1,2 L/ha no sulco (fração fúlvica + húmica de alta atividade CEC 290) reduzindo logística e volume de calda.",
            "Analise_Mercado.xlsx (Sheet 3)",
            now_iso
        ),
        (
            "Rigrantec — BioGain Fúlvico 70",
            "Leonardita (Fulvato/humatos em pó)",
            "Pó solúvel",
            "2–4 kg/ha solo; 1 kg/ha foliar",
            "Muito baixa–baixa",
            "R$ 93,69/kg (ou R$ 60,58/kg no kit 8 kg)",
            180.00,
            "Variável",
            "Keal (1 L/ha = R$ 107–113/ha | CEC 325)",
            "Benchmark importante para produtos fúlvicos concentrados.",
            "Posicionar Keal pela pureza fúlvica (3,45% ISO líquida pronta sem risco de entupimento de bico foliar) e ROI de 11x em café.",
            "Analise_Mercado.xlsx (Sheet 3)",
            now_iso
        ),
        (
            "Healthy BioSolutions — Humic Soil",
            "Leonardita americana purificada",
            "Líquido (10% AH + 10% AF declarados)",
            "2–3 L/ha sulco; 4–5 L/ha soja/algodão",
            "Baixa",
            "Sob consulta (atuação forte em MT, GO, BA, MS, PR, MG)",
            165.00,
            "Variável (método colorimétrico vs ISO)",
            "Alpha (2,5 L/ha) e Liquid Carbon HC (4,7 L/ha)",
            "Atua exatamente nos mesmos estados prioritários de grãos e algodão.",
            "Exigir comparação no mesmo método analítico (ISO 19822 vs colorimétrico, que infla leitura aparente) e apresentar laudo de metais pesados.",
            "Analise_Mercado.xlsx (Sheet 3)",
            now_iso
        ),
        (
            "Liphatech / De Sangosse — Humonia",
            "Humatos e fulvatos de Leonardita",
            "Líquido para solo/fertirrigação",
            "Grãos 2–5 L/ha; Café/Citros 7–15 L/ha; HF 10–20 L/ha",
            "Baixa em grãos; alta em HF/Café",
            "Sob consulta (canal revenda/cooperativa)",
            280.00,
            "Variável",
            "Keal (1 L/ha em Café/HF) e Alpha (2,5 L/ha)",
            "Portfólio muito bem adaptado a café, HF e fertirrigação no Brasil.",
            "Em café e HF, enquanto Humonia exige 7–20 L/ha, Keal e Alpha entregam resposta com 1 a 2,5 L/ha.",
            "Analise_Mercado.xlsx (Sheet 3)",
            now_iso
        ),
        (
            "Coda — Codahumus 20",
            "Extrato húmico de Leonardita",
            "Líquido (~22,8% extrato húmico total)",
            "3–5 L/ha por aplicação",
            "Baixa por aplicação (acumula no ciclo)",
            "R$ 33,75 a R$ 53,00/L (20L a R$ 675–819)",
            195.00,
            "Alto pH alcalino",
            "Keal (1 L/ha) e Alpha (2,5 L/ha)",
            "Concorrente tradicional em HF e specialty crops.",
            "Comparar custo do programa completo por hectare em HF/tomate/café e mostrar vantagem da CEC 325 do Keal.",
            "Analise_Mercado.xlsx (Sheet 3)",
            now_iso
        ),
        (
            "Plantpar — Carbon 9",
            "Leonardita + substâncias húmicas + KNO3",
            "Líquido organomineral",
            "Soja 1 L/ha; Milho 1,2 L/ha; Tomate 3–6 L/ha",
            "Muito baixa em grãos",
            "R$ 68,57/L (loja oficial)",
            80.57,
            "Organomineral diluído",
            "Alpha (0,58–1,2 L/ha sulco)",
            "Prova que o mercado brasileiro já aceita aplicação húmica de ~1 L/ha em soja e milho.",
            "Usar a validação da faixa de 1 L/ha a favor do Alpha, destacando a matéria-prima Humalite canadense pura.",
            "Analise_Mercado.xlsx (Sheet 3)",
            now_iso
        ),
        (
            "Leonardita Australiana / Genérica B2B (Agro Forte, Humytec, Solo Rico)",
            "Leonardita australiana / chinesa / diversas",
            "Pó ou granulado bruto (10–15 kg/ha ou B2B)",
            "2–15 kg/ha",
            "Média–Alta",
            "R$ 2,00/kg (commodity B2B) a R$ 35–85/kg (marketplace)",
            210.00,
            "36% a 85% de cinza inerte + risco de Cd/Pb/As",
            "XP100 / Fuze DS / MP30 (Humalite 11% cinza)",
            "Maior risco de comoditização e ruído de preço ('ácido húmico de R$ 9').",
            "NUNCA disputar preço por tonelada bruta: mostrar na planilha do comprador industrial que 60% de cinza = pagar frete e imposto sobre terra inerte e risco de reprovação na IN 61/2020 (metais pesados).",
            "Analise_Mercado.xlsx & Diagnostico.docx",
            now_iso
        ),
    ]
    cur.executemany(
        """
        INSERT INTO competitors (
            company_product, origin_tech, formulation, public_dose, dose_profile,
            public_price_brl, estimated_cost_ha_brl, ash_estimate,
            black_earth_counter_sku, competitive_reading, defense_argument,
            source, checked_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        competitors,
    )

    # 6. Events Calendar 2027 (Camada 5 de Diagnostico.docx)
    events = [
        (
            "Show Rural Coopavel 2027",
            "Cascavel / PR",
            "Fevereiro / 2027",
            "URGENTE: Inscrição de trabalhos e espaço fecha em até 60 dias (Nov/Dez 2026)",
            "P1 — Alta Prioridade",
            "Reuniões técnicas com Coamo, Lar, C.Vale, Copacol e Fundação ABC",
            "Alpha, Fuze DS, Magna, GG16"
        ),
        (
            "Show Safra 2027 (Fundação Rio Verde)",
            "Lucas do Rio Verde / MT",
            "Março / 2027",
            "URGENTE: Contratação de vitrine tecnológica junto à Fundação Rio Verde em até 45 dias",
            "P1 — Prioridade Máxima Grãos",
            "Vitrine de protocolo de soja/milho safrinha para grupos de MT (Bom Futuro, Scheffer, Sinagro)",
            "Alpha, Fuze DS, Magna"
        ),
        (
            "Expodireto Cotrijal 2027",
            "Não-Me-Toque / RS",
            "Março / 2027",
            "Atenção: Fechamento de agenda com cooperativas gaúchas até Jan/2027",
            "P1 — Alta Prioridade Sul",
            "Posicionar descompactação e estruturação de solo com Cotrijal, Cotrisal e Assiferto RS",
            "Alpha, Magna, Liquid Carbon HC"
        ),
        (
            "Tecnoshow Comigo 2027",
            "Rio Verde / GO",
            "Abril / 2027",
            "URGENTE: Protocolo com ITC Comigo deve entrar agora em Nov/Dez 2026",
            "P1 — Prioridade Máxima Centro-Oeste",
            "Dia de campo com ITC Comigo + rodada comercial com Agrológica e Produtecnica",
            "Fuze DS, Alpha, Magna"
        ),
        (
            "Bahia Farm Show 2027",
            "Luís Eduardo Magalhães / BA",
            "Junho / 2027",
            "Preparar ensaio prévio com Fundação Bahia na safra 26/27",
            "P1 — Foco Algodão e Matopiba",
            "Apresentar ROI em algodão e soja em solos arenosos de baixa CTC (Fundação Bahia / Abapa)",
            "Alpha, Keal, Fuze DS"
        ),
        (
            "Congresso ANDAV 2027",
            "São Paulo / SP",
            "03 a 05 de Agosto / 2027",
            "Planejamento de rodada de negócios B2B no 1º trimestre 2027",
            "P1 — Principal Balcão de Distribuidores",
            "Fechamento de contratos de distribuição regional após resultados da 1ª safra de ensaios",
            "Portfólio Completo (humiZEN & humaPLUS)"
        ),
        (
            "Conexão Abisolo / Summit Abisolo 2027",
            "Campinas / Piracicaba / SP",
            "Anual — 2027",
            "Associar-se à Abisolo nos primeiros 90 dias (Meta Dias 31–90)",
            "P1 — Hub Industrial OEM & Regulatório",
            "Encontrar sócios industriais OEM (Vittia, Brandt, ILSA) e pesquisadores na mesma sala",
            "Fuze DS, XP100, MP30, Magna"
        ),
    ]
    cur.executemany(
        """
        INSERT INTO events_calendar (
            event_name, location, event_date, deadline_alert,
            priority_level, strategic_goal, target_skus
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        events,
    )

    # 7. Market News & Regulatory Radar Alerts
    news_alerts = [
        (
            "Janela de Feiras & Ensaios 2027",
            "ALERTA DE 60 DIAS: Fechamento de protocolos de ensaio para Show Safra, Tecnoshow Comigo e Show Rural 2027",
            "Estamos em novembro de 2026: a submissão de tratamentos nas fundações regionais (Fundação Rio Verde, ITC Comigo, Fundação ABC e Fundação MT) para vitrines do 1º semestre de 2027 encerra nos próximos 45–60 dias.",
            "CRÍTICO",
            "Agente 05 (Técnico) & Agente 01 (Estratégia)",
            "Disparar Cadência Semana 1 (Protocolo de 6 locais DBC custeado) para Fundação MT, Fundação Rio Verde e ITC Comigo.",
            "Diagnóstico Estratégico AgroRemoto",
            "https://www.eventosandav.com.br/en/",
            now_iso,
            1
        ),
        (
            "Regulatório MAPA / SIPEAGRO",
            "Filtro de Metais Pesados (IN 61/2020) e Registro de Estabelecimento Importador",
            "Fiscalização estadual e cooperativas (Coamo, Lar, C.Vale, Cooxupé) exigem LI, registro SIPEAGRO e laudo por lote comprovando Cd, Pb e As abaixo dos limites da IN 61/2020. A Humalite Black Earth (Cd 0,1 / Pb 3 / As 1 ppm) passa com ampla folga frente a leonarditas genéricas.",
            "ALTO",
            "Agente 04 (Regulatório)",
            "Executar Gate R0/R1 nos 30 primeiros dias e anexar COA de metais pesados e cinza (11%) em todas as propostas B2B.",
            "MAPA / SIPEAGRO Normativas",
            "https://www.gov.br/agricultura/pt-br/assuntos/insumos-agropecuarios",
            now_iso,
            1
        ),
        (
            "Crédito & Barter",
            "RenovAgro / Plano ABC+ 2026/27 amplia atratividade para Condicionadores de Solo e Bioinsumos",
            "Produtores de grãos com margem apertada estão priorizando insumos financiáveis via linhas RenovAgro/ABC+ (Banco do Brasil, Sicredi, Sicoob) ou operações de barter com tradings (Amaggi, Cargill, Bunge) e cooperativas.",
            "ALTO",
            "Agente 03 (Financeiro) & Agente 06 (Marketing)",
            "Incluir ficha de enquadramento RenovAgro/ABC+ e opção de barter (sem desconto de tabela) no kit do interlocutor financeiro.",
            "Radar Financeiro Agro",
            "https://www.gov.br/agricultura/pt-br/assuntos/politica-agricola/plano-safra",
            now_iso,
            1
        ),
        (
            "Inteligência Competitiva",
            "Pressão de preço de Leonardita Genérica no varejo digital vs Posicionamento Técnico B2B",
            "Monitoramento detectou ofertas de humato de potássio genérico entre R$ 35–85/kg no varejo e R$ 2/kg em lotes B2B sem laudo ISO 19822, enquanto HGS HumiK WSP mantém referência premium a R$ 158,90/kg.",
            "MÉDIO",
            "Agente 01 (Estratégia) & Agente 02 (Prospecção)",
            "Bloquear disputa por preço/tonelada bruta; apresentar comparativo de R$/kg de ácido húmico ISO 19822 entregue (11% de cinza Black Earth vs 60% de cinza inerte).",
            "Monitoramento de Concorrência Black Earth OS",
            "https://forbes.com.br/forbes-agro/",
            now_iso,
            1
        ),
        (
            "Economia de Culturas (Café & Soja)",
            "Relação de troca histórica no Café Arábica (R$ 23,33/kg) gera Break-Even de apenas 0,08 saca/ha para Keal",
            "Com o café arábica em patamar elevado, o custo de aplicação de Keal (R$ 113/ha) ou Alpha (R$ 123/ha) paga-se com menos de 5,3 kg de café beneficiado por hectare, gerando ROI projetado superior a 10x.",
            "ALTO",
            "Agente 05 (Técnico) & Agente 02 (Prospecção)",
            "Priorizar abordagem imediata em Minas Gerais (Cooxupé, Minasul, Expocaccer, EPAMIG/UFLA).",
            "Simulador Break-Even AgroRemoto",
            "https://www.cooxupe.com.br/",
            now_iso,
            1
        ),
    ]
    cur.executemany(
        """
        INSERT INTO market_news_alerts (
            category, title, summary, impact_level, affected_agent,
            recommended_action, source_name, source_url, published_at, is_automated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        news_alerts,
    )

    # 8. Campaigns & Playbooks (Cadência de 5 etapas + Kits por Interlocutor)
    playbooks = [
        (
            "Abordagem OEM / Formulador Industrial (Economia de Cinza + ISO 19822)",
            "OEM / Formulador Industrial (Vittia, Brandt, Atlântica, ILSA)",
            "Diretor de P&D / Gerente de Suprimentos Industriais",
            "Fuze DS, XP100, MP30, Magna",
            "Semana 1 — Abertura Técnica Industrial",
            "Matéria-prima Humalite (11% cinza | ISO 19822) — Redução de custo por kg de AH ativo em formulações",
            "Olá [Nome do Responsável Técnico/Industrial],\n\nNa formulação de condicionadores e fertilizantes especiais, o maior custo oculto das leonarditas tradicionais não está no preço por tonelada, mas nos 40% a 65% de cinza inerte e na variação de metais pesados (Cd, Pb, As) entre lotes.\n\nEstamos estruturando o fornecimento industrial no Brasil da linha humiZEN/humaLITE da Black Earth (depósito de Sheerness, Alberta — Canadá), com:\n• Apenas 11% de cinza (3 a 5x menos material inerte no frete e no reator)\n• Solubilidade validada (Fuze DS a 129 g/L reconstrói solução líquida plena no Brasil sem importar água)\n• Metais pesados drasticamente abaixo dos limites da IN 61/2020 (Cd 0,1 / Pb 3 / As 1 ppm) com COA ISO 19822 por lote.\n\nPodemos agendar 30 minutos na próxima semana para apresentar a planilha de custo por kg de substância húmica efetiva e enviar amostras de bancada do Fuze DS e XP100?",
            "1) Laudo COA ISO 19822 por lote; 2) Comparativo de Cinza (11% vs 60%) e Metais Pesados IN 61/2020; 3) Ficha de Blend Industrial.",
            "Gate R0/R1 Aprovado para cotação industrial B2B",
            "Pendente Aprovação (AgroRemoto)",
            now_iso
        ),
        (
            "Abordagem Cooperativas — Porta de Entrada Técnica (Semana 1 e 2)",
            "Cooperativas (Coamo, Comigo, Cooxupé, Lar, C.Vale, Cocamar)",
            "Coordenador Técnico / Gerente de Desenvolvimento Agronômico",
            "Alpha, Keal, Fuze DS, Magna",
            "Semana 1 — Proposta de Protocolo DBC (Sem pedir pedido)",
            "Protocolo DBC em 6 locais custeado + mitigação de P fixado e Al³⁺ para cooperados [Nome da Cooperativa]",
            "Prezado(a) [Nome do Coordenador Técnico],\n\nSabemos que o produtor cooperado hoje não busca mais um aditivo foliar genérico, mas sim estancar perdas reais de margem: R$ 159/ha em fósforo fixado no Latossolo e R$ 208/ha por toxidez de Al³⁺ em subsuperfície.\n\nRepresentando a plataforma técnica da Black Earth no Brasil (AgroRemoto), gostaríamos de submeter ao departamento técnico da [Cooperativa] um protocolo de validação em blocos casualizados (DBC), integralmente custeado por nós, com relatório assinado pela sua equipe.\n\nNa reunião de 40 minutos levaremos:\n1. Laudo gravimétrico ISO 19822 (diferença real frente ao método colorimétrico);\n2. Kit para teste de jarro ao vivo e matriz proativa de compatibilidade (incluindo regras claras para ureia e caldas ácidas);\n3. Planilha aberta de Break-Even (piso de 0,64 a 0,94 sc/ha em soja e 0,08 sc/ha em café).\n\nQual o melhor horário na próxima terça ou quinta-feira com sua coordenação técnica?",
            "1) Planilha Break-Even impressa com nome da Cooperativa; 2) Matriz de Incompatibilidade de Calda; 3) Laudo ISO 19822 + Kit Teste de Jarro.",
            "Gate R3 (Ensaio técnico / sem alegação comercial sem registro)",
            "Pendente Aprovação (AgroRemoto)",
            now_iso
        ),
        (
            "Abordagem Fundações de Pesquisa & Universidades (Regra de Ouro Camada 1)",
            "Fundações (Fundação MT, Rio Verde, ABC, Chapadão) & UENF / Embrapa",
            "Pesquisador Sênior de Fertilidade do Solo / Nutrição",
            "Alpha, Fuze DS, Magna, GG16",
            "Semana 1 — Contratação de Ensaio Oficial Safra 26/27",
            "Contratação de Protocolo Dose-Resposta e Substituição de 20% MAP — Humalite Canadense (ISO 19822)",
            "Caro(a) Dr(a). [Nome do Pesquisador],\n\nEstamos alocando o orçamento de pesquisa de campo 2026/2027 da Black Earth (Canadá) no Brasil e selecionamos a [Nome da Fundação/Instituição] para conduzir o protocolo regional de validação.\n\nNosso objetivo não é avaliar apenas produtividade final isolada, mas mensurar mecanismo de solo:\n• Eficiência de uso de Fósforo com redução de 20% da dose de MAP associado a Magna/GG16/Fuze DS;\n• Crescimento radicular e neutralização de Al³⁺ em subsuperfície (acidez funcional 7,0 mmol/g e CTC 275 meq/100g).\n\nPodemos alinhar ainda esta semana os termos de contratação do protocolo DBC para garantirmos a janela de instalação e participação no Dia de Campo 2027?",
            "1) Protocolo Experimental DBC (6 tratamentos × 4 repetições); 2) Raw Analysis & Fracionamento Húmico/Fúlvico ISO 19822; 3) SDS/FISPQ.",
            "Gate R3 Liberado (Pesquisa Científica)",
            "Pendente Aprovação (AgroRemoto)",
            now_iso
        ),
        (
            "Abordagem Contas Âncora / Usinas & Mega Produtores (Custo do Problema)",
            "Contas Âncora (Raízen, Copersucar, São Martinho, SLC, Bom Futuro)",
            "Agrônomo de Fazenda / Gerente de Tecnologia Agrícola",
            "Liquid Carbon HC, Alpha, Fuze DS",
            "Semana 1 — Talhão Demonstrativo de 20 ha",
            "Redução do custo de reforma de canavial (R$ 900/ha/ano) e proteção de stand em áreas restritivas",
            "Olá [Nome do Agrônomo / Gerente Agrícola],\n\nEm vez de apresentar mais um bioestimulante por preço de litro, gostaríamos de propor uma validação prática de 20 hectares em um talhão com histórico de desafio (queda precoce de soqueira, alto Al³⁺ ou baixa resposta a P).\n\nCom a linha concentrada da Black Earth (Alpha e Liquid Carbon HC / Fuze DS), trabalhamos na substituição parcial de adubação fosfatada (15% a 20%) e proteção radicular, com acompanhamento quinzenal junto ao consultor da fazenda e viabilidade de estruturação via Barter / RenovAgro.\n\nPodemos revisar em 30 minutos os dados de break-even para escolhermos o talhão piloto?",
            "1) Simulador Custo do Problema (R$ 208/ha Al³⁺ | R$ 159/ha P fixado | R$ 900/ha reforma cana); 2) Protocolo de 20 ha; 3) Enquadramento Barter/RenovAgro.",
            "Gate R3/R4 (Sujeito a validação de status SIPEAGRO por SKU)",
            "Pendente Aprovação (AgroRemoto)",
            now_iso
        ),
    ]
    cur.executemany(
        """
        INSERT INTO campaigns_playbooks (
            title, target_channel, target_interlocutor, sku_focus, cadence_step,
            subject_line, message_body, required_attachments, compliance_gate_status,
            human_approval_status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        playbooks,
    )

    # 9. Automation Schedules (100% scheduled cron jobs as chosen by user)
    schedules = [
        (
            "DAILY_MARKET_NEWS_RADAR",
            "Radar Diário de Mercado, Notícias, Regulatório MAPA & Eventos",
            "Agente 00 (Orquestrador) + Agente 04 (Regulatório)",
            "0 7 * * *",
            "Diário às 07:00 BRT",
            "Coleta notícias do agronegócio brasileiro (insumos, ácido húmico, bioinsumos, MAPA/SIPEAGRO, Abisolo, crédito RenovAgro/Barter), verifica prazos de feiras 2027 e gera briefing diário de alertas.",
            now_iso,
            "Diário 07:00",
            "COMPLETED",
            12,
            1
        ),
        (
            "DAILY_COMPETITOR_PRICE_WATCH",
            "Monitoramento de Concorrência, Preços & Simulador Break-Even",
            "Agente 01 (Estratégia) + Agente 03 (Financeiro)",
            "30 7 * * *",
            "Diário às 07:30 BRT",
            "Monitora preços públicos e posicionamento dos 17 concorrentes mapeados (HGS, Rigrantec, Coda, Plantpar, Healthy BioSolutions, Leonardita australiana), atualiza cotações (Soja, Café, Milho, Algodão, Cana, MAP) e recalcula o Semáforo de ROI.",
            now_iso,
            "Diário 07:30",
            "COMPLETED",
            17,
            1
        ),
        (
            "DAILY_B2B_PROSPECTING_SCORING",
            "Motor de Prospecção Reversa & Qualificação de Contas (CRM)",
            "Agente 02 (Prospecção) + Agente 05 (Técnico)",
            "0 8 * * *",
            "Diário às 08:00 BRT",
            "Qualifica e recalcula o Lead Score (0–100) das contas prioritárias por canal (OEM, Cooperativas, Usinas, Fundações, Distribuidores) nos estados foco (MT, GO, MG, PR, SP, BA), identificando lacunas e próxima ação.",
            now_iso,
            "Diário 08:00",
            "COMPLETED",
            11,
            1
        ),
        (
            "WEEKLY_CAMPAIGN_DOSSIER_GEN",
            "Geração Semanal de Dossiês Comerciais, Playbooks & Relatório Executivo",
            "Agente 06 (Marketing) + Agente 00 (Orquestrador)",
            "0 9 * * 1",
            "Semanal (Segundas às 09:00 BRT)",
            "Prepara lotes de abordagem personalizados por interlocutor (Pesquisador, Agrônomo de Cooperativa, Comprador OEM, Produtor), verifica Gates Regulatórios R0–R4 e publica o Relatório Semanal consolidado para aprovação humana.",
            now_iso,
            "Segundas 09:00",
            "COMPLETED",
            15,
            1
        ),
    ]
    cur.executemany(
        """
        INSERT INTO automation_schedules (
            job_code, job_name, agent_owner, cron_expression, frequency_label,
            description, last_run_at, next_run_at, last_status, items_processed, enabled
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        schedules,
    )


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
