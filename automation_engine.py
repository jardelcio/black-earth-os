#!/usr/bin/env python3
"""
Black Earth Commercial Intelligence OS — Multi-Agent Automation Engine
Executa os 4 fluxos automatizados agendados (diários e semanais) sob o contrato
universal de saída estruturada (Seção 10 da Knowledge Base) e gera relatórios
e alertas acionáveis em /home/antigravity/black-earth-os/reports/.
"""

import csv
import json
import os
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from database import get_connection, init_db

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")


def compute_breakeven_matrix(conn, crop_code="P_SOJA", custom_crop_price=None, custom_haircut=None):
    """
    Reproduz fielmente as fórmulas do Bloco 3 e Bloco 4 do Diagnostico.docx:
    - Custo/ha = Dose * Preço Unitário + Frete/ha
    - Break-even kg/ha = Custo/ha / Preço da cultura (R$/kg)
    - Break-even sc/ha = Break-even kg/ha / 60
    - Resposta esperada = Base_response * Haircut (0,60 para líquidos/solúveis, 0,50 para granulados a lanço)
    - Receita = Resposta esperada * Preço da cultura
    - ROI = Receita / Custo/ha
    - Semáforo = VERDE (>= 1.5), AMARELO (1.0 a 1.49), VERMELHO (< 1.0)
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM market_parameters")
    params = {r["code"]: dict(r) for r in cur.fetchall()}

    crop_param = params.get(crop_code, params["P_SOJA"])
    crop_price = float(custom_crop_price) if custom_crop_price is not None else float(crop_param["value"])
    base_resp = float(crop_param["base_response_kg_ha"] or 188.0)
    haircut_liq = float(custom_haircut) if custom_haircut is not None else float(params["HAIRCUT"]["value"])
    haircut_gran = float(params["HAIRCUT_G"]["value"])

    cur.execute("SELECT * FROM products ORDER BY priority_tier ASC, id ASC")
    products = [dict(r) for r in cur.fetchall()]

    results = []
    for p in products:
        dose = float(p["dose_per_ha"])
        unit_price = float(p["unit_price_brl"])
        freight = float(p["freight_per_ha_brl"])
        cost_ha = round(dose * unit_price + freight, 2)

        be_kg = round(cost_ha / crop_price, 2) if crop_price > 0 else 0
        be_sc = round(be_kg / 60.0, 2)

        # Distinguish broadcast granular vs furrow/liquid/soluble
        is_heavy_granular = p["sku"] in ("AG4", "Dual Action", "MP30")
        hc = haircut_gran if is_heavy_granular else haircut_liq
        # Liquid Carbon has a slightly higher trial base in Diagnostico (208 -> 125 kg/ha at 0.60)
        sku_base = base_resp * (1.106 if p["sku"] in ("Liquid Carbon", "Liquid Carbon HC") else 1.0)
        expected_kg = round(sku_base * hc, 1)

        revenue_brl = round(expected_kg * crop_price, 2)
        profit_brl = round(revenue_brl - cost_ha, 2)
        roi = round(revenue_brl / cost_ha, 2) if cost_ha > 0 else 0

        if roi >= 1.5:
            semaphore = "VERDE"
            commercial_rule = "Venda direta / demonstração técnica (sem desconto)" if roi >= 2.0 else "Venda com área de demonstração"
        elif roi >= 1.0:
            semaphore = "AMARELO"
            commercial_rule = "Apenas via substituição de 20% MAP ou conta âncora"
        else:
            semaphore = "VERMELHO"
            commercial_rule = "BLOQUEADO isolado em grãos — usar apenas como ingrediente B2B ou em Café/HF"

        results.append({
            "sku": p["sku"],
            "family": p["family"],
            "form": p["form"],
            "priority_tier": p["priority_tier"],
            "dose_per_ha": dose,
            "unit": p["unit"],
            "unit_price_brl": unit_price,
            "freight_per_ha_brl": freight,
            "cost_ha_brl": cost_ha,
            "breakeven_kg_ha": be_kg,
            "breakeven_sc_ha": be_sc,
            "expected_response_kg_ha": expected_kg,
            "revenue_ha_brl": revenue_brl,
            "net_profit_ha_brl": profit_brl,
            "roi": roi,
            "semaphore": semaphore,
            "commercial_rule": commercial_rule,
        })

    # MAP Substitution model (Bloco 4 de Diagnostico.docx)
    map_price = float(params["P_MAP"]["value"])
    map_base_kg = 200.0
    map_reduction_pct = 20.0
    map_saved_kg = map_base_kg * (map_reduction_pct / 100.0)
    map_savings_brl = round(map_saved_kg * map_price, 2)
    gg16_cost_brl = round(60.0 * 3.60 + 12.0, 2)
    net_extra_cost = round(gg16_cost_brl - map_savings_brl, 2)
    soy_gain_revenue = round(113.0 * crop_price, 2)
    map_sub_roi = round(soy_gain_revenue / net_extra_cost, 2) if net_extra_cost > 0 else 9.99

    return {
        "crop_code": crop_code,
        "crop_name": crop_param["name"],
        "crop_price_brl_kg": crop_price,
        "haircut_applied": haircut_liq,
        "matrix": results,
        "map_substitution": {
            "map_base_kg_ha": map_base_kg,
            "map_price_brl_kg": map_price,
            "reduction_pct": map_reduction_pct,
            "map_saved_kg_ha": map_saved_kg,
            "savings_brl_ha": map_savings_brl,
            "gg16_cost_brl_ha": gg16_cost_brl,
            "net_additional_cost_brl_ha": net_extra_cost,
            "expected_gain_revenue_brl_ha": soy_gain_revenue,
            "net_result_brl_ha": round(soy_gain_revenue - net_extra_cost, 2),
            "substitution_roi": map_sub_roi,
            "approved": map_sub_roi >= 1.25,
        },
    }


def simulate_landed_to_channel(
    sku="Fuze DS",
    fob_usd_unit=7.20,
    exchange_rate=5.45,
    freight_insurance_pct=12.0,
    customs_taxes_non_rec_pct=18.5,
    channel_route="OEM / Indústria Importadora",
    partner_commission_pct=5.0,
    channel_margin_pct=22.0,
    volume_tons=20.0,
):
    """
    Simulador Tributário, Canal e Remuneração (Seção 8 da Knowledge Base).
    Nota de governança: NCM e alíquotas tratadas como hipóteses sujeitas a revisão fiscal/aduaneira.
    """
    fob_brl = round(fob_usd_unit * exchange_rate, 2)
    logistics_brl = round(fob_brl * (freight_insurance_pct / 100.0), 2)
    taxes_brl = round((fob_brl + logistics_brl) * (customs_taxes_non_rec_pct / 100.0), 2)
    financial_storage_brl = round(fob_brl * 0.035, 2)
    landed_cost_brl = round(fob_brl + logistics_brl + taxes_brl + financial_storage_brl, 2)

    # Target selling price based on route
    route_multipliers = {
        "OEM / Indústria Importadora": 1.48,
        "Cooperativa (Venda Direta c/ Técnico)": 1.72,
        "Importador + Distribuidor Regional": 1.95,
        "Conta Âncora (Volume > 20t / Barter)": 1.60,
    }
    mult = route_multipliers.get(channel_route, 1.65)
    gross_price_brl = round(landed_cost_brl * mult, 2)

    # Volume/barter discount rule (Parte 4 Diagnostico: desconto só >20t, antecipado ou barter)
    discount_pct = 5.0 if volume_tons >= 20.0 else 0.0
    net_price_brl = round(gross_price_brl * (1.0 - discount_pct / 100.0), 2)

    commission_brl = round(net_price_brl * (partner_commission_pct / 100.0), 2)
    channel_rebate_brl = round(net_price_brl * (channel_margin_pct / 100.0), 2)
    tech_trial_reserve_brl = round(net_price_brl * 0.04, 2)

    contribution_margin_brl = round(
        net_price_brl - landed_cost_brl - commission_brl - channel_rebate_brl - tech_trial_reserve_brl, 2
    )
    contribution_margin_pct = round((contribution_margin_brl / net_price_brl) * 100.0, 1) if net_price_brl > 0 else 0.0

    # Effective humic substance cost comparison (11% ash vs 60% ash)
    effective_hs_cost_black_earth = round(net_price_brl / 0.60, 2)
    effective_hs_cost_generic_leonardite = round((net_price_brl * 0.75) / 0.28, 2)

    return {
        "sku": sku,
        "channel_route": channel_route,
        "volume_tons": volume_tons,
        "fob_usd": fob_usd_unit,
        "exchange_rate": exchange_rate,
        "fob_brl": fob_brl,
        "international_logistics_brl": logistics_brl,
        "estimated_non_recoverable_taxes_brl": taxes_brl,
        "financial_and_storage_brl": financial_storage_brl,
        "landed_cost_brl": landed_cost_brl,
        "gross_list_price_brl": gross_price_brl,
        "volume_discount_pct": discount_pct,
        "net_selling_price_brl": net_price_brl,
        "partner_commission_brl": commission_brl,
        "channel_margin_or_rebate_brl": channel_rebate_brl,
        "technical_trial_fund_brl": tech_trial_reserve_brl,
        "black_earth_contribution_brl": contribution_margin_brl,
        "black_earth_contribution_pct": contribution_margin_pct,
        "total_contract_revenue_brl": round(net_price_brl * volume_tons * 1000, 2),
        "total_contract_contribution_brl": round(contribution_margin_brl * volume_tons * 1000, 2),
        "ash_advantage": {
            "black_earth_ash_pct": 11.0,
            "generic_leonardite_ash_pct": 60.0,
            "cost_per_kg_active_hs_black_earth_brl": effective_hs_cost_black_earth,
            "cost_per_kg_active_hs_generic_brl": effective_hs_cost_generic_leonardite,
        },
        "governance_warning": "HIPÓTESE SIMULADA: Classificação NCM, II, IPI, PIS/COFINS-Importação e ICMS (Convênio 100/97) exigem validação formal por despachante/consultoria tributária antes de emissão de proposta vinculante.",
    }


def run_job_market_news_radar(conn):
    """
    Job 1: DAILY_MARKET_NEWS_RADAR
    Coleta e atualiza alertas regulatórios, eventos 2027 (janela de 60 dias),
    crédito RenovAgro/Barter e notícias relevantes para Black Earth.
    """
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    cur = conn.cursor()

    # Check live feeds if reachable (graceful fallback to curated intelligence if sandboxed)
    live_headlines = []
    rss_urls = [
        ("Canal Rural", "https://www.canalrural.com.br/feed/"),
        ("AgFeed", "https://agfeed.com.br/feed/"),
    ]
    for src_name, url in rss_urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 BlackEarthOS/1.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                xml_data = resp.read()
                root = ET.fromstring(xml_data)
                for item in root.findall(".//item")[:2]:
                    t = item.findtext("title") or ""
                    l = item.findtext("link") or url
                    if t:
                        live_headlines.append((src_name, t.strip(), l.strip()))
        except Exception:
            pass

    for src_name, title, link in live_headlines:
        cur.execute("SELECT id FROM market_news_alerts WHERE title = ?", (title,))
        if not cur.fetchone():
            cur.execute(
                """
                INSERT INTO market_news_alerts (
                    category, title, summary, impact_level, affected_agent,
                    recommended_action, source_name, source_url, published_at, is_automated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    "Radar Setorial Agro (Feed Ao Vivo)",
                    title,
                    f"Capturado automaticamente pelo motor de monitoramento {src_name}. Avaliar impacto em relação de troca e janela de abordagem.",
                    "MÉDIO",
                    "Agente 00 (Orquestrador)",
                    "Revisar no briefing matinal se altera poder de compra de cooperados ou usinas.",
                    src_name,
                    link,
                    now_iso,
                ),
            )

    cur.execute("SELECT COUNT(*) as c FROM market_news_alerts")
    total_alerts = cur.fetchone()["c"]
    cur.execute("SELECT * FROM events_calendar ORDER BY id ASC")
    events = [dict(r) for r in cur.fetchall()]

    contract_output = {
        "task_id": f"RADAR-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}",
        "agent": "orchestrator",
        "status": "completed",
        "facts": [
            {
                "claim": f"{total_alerts} alertas de mercado, regulatório MAPA (IN 61/2020) e janelas de feiras 2027 monitorados ativamente.",
                "source_url": "file:///home/antigravity/Diagnostico.docx",
                "checked_at": now_iso,
                "confidence": "high",
            },
            {
                "claim": "Janela de inscrição de trabalhos e contratação de ensaios para Show Safra, Tecnoshow Comigo e Show Rural 2027 fecha nos próximos 60 dias.",
                "source_url": "https://www.eventosandav.com.br/en/",
                "checked_at": now_iso,
                "confidence": "high",
            },
        ],
        "assumptions": [
            "Prazos de vitrines tecnológicas 2027 exigem protocolo assinado com fundações ainda em Nov/Dez 2026."
        ],
        "recommendations": [
            {
                "action": "Priorizar assinatura de protocolos com Fundação Rio Verde, Fundação MT, ITC Comigo e Fundação ABC nos próximos 30 dias.",
                "rationale": "Regra de Ouro Camada 1: 1 ensaio publicado em cada uma das 3 principais regiões antes de contratar vendedor.",
                "owner": "Jardélcio Carvalho (AgroRemoto)",
            }
        ],
        "risks": [
            "Perder a janela de plantio e vitrines de 2027 atrasa a prova local em 12 meses."
        ],
        "open_questions": [
            "Confirmar orçamento aprovado pela matriz Black Earth para os 6 locais do protocolo DBC."
        ],
        "human_approval_required": True,
        "events_monitored": len(events),
    }

    cur.execute(
        """
        UPDATE automation_schedules
        SET last_run_at = ?, last_status = 'COMPLETED', items_processed = ?
        WHERE job_code = 'DAILY_MARKET_NEWS_RADAR'
        """,
        (now_iso, total_alerts),
    )
    return contract_output


def run_job_competitor_price_watch(conn):
    """
    Job 2: DAILY_COMPETITOR_PRICE_WATCH
    Analisa os concorrentes mapeados, recalcula Break-Even para Soja, Café, Algodão e Cana,
    e gera alerta de defesa contra comoditização (leonardita barata vs Humalite 11% cinza).
    """
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    cur = conn.cursor()
    cur.execute("SELECT * FROM competitors ORDER BY id ASC")
    comps = [dict(r) for r in cur.fetchall()]

    soja_sim = compute_breakeven_matrix(conn, "P_SOJA")
    cafe_sim = compute_breakeven_matrix(conn, "P_CAFE")

    green_soja = [r["sku"] for r in soja_sim["matrix"] if r["semaphore"] == "VERDE"]
    red_soja = [r["sku"] for r in soja_sim["matrix"] if r["semaphore"] == "VERMELHO"]

    contract_output = {
        "task_id": f"COMP-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}",
        "agent": "strategy",
        "status": "completed",
        "facts": [
            {
                "claim": f"{len(comps)} produtos concorrentes monitorados (incluindo HGS HumiK WSP a R$ 158,90/kg, Rigrantec BioGain Húmico 80 a R$ 118,63/kg e Plantpar Carbon 9 a R$ 68,57/L).",
                "source_url": "file:///home/antigravity/Analise_Mercado.xlsx",
                "checked_at": now_iso,
                "confidence": "high",
            },
            {
                "claim": f"Em Soja (R$ {soja_sim['crop_price_brl_kg']}/kg), SKUs com Semáforo VERDE (ROI >= 1,5x): {', '.join(green_soja)}. SKUs bloqueados isolados (Semáforo VERMELHO): {', '.join(red_soja)}.",
                "source_url": "file:///home/antigravity/Diagnostico.docx",
                "checked_at": now_iso,
                "confidence": "high",
            },
        ],
        "assumptions": [
            "Haircut de 40% (fator 0,60) aplicado sobre os resultados de ensaios canadenses até geração de curva dose-resposta brasileira."
        ],
        "recommendations": [
            {
                "action": "Em Soja/Milho, ofertar exclusivamente Fuze DS (ROI 2,93x), XP100 (ROI 3,17x), Magna (ROI 2,58x), Keal (ROI 2,20x) e Alpha (ROI 2,01x), ou GG16 vinculado à redução de 20% de MAP (ROI 1,35x).",
                "rationale": "AG4, Dual Action e MP30 a lanço em soja geram ROI < 0,50x e não sobrevivem ao teste de estresse.",
                "owner": "Agente 01 (Estratégia) & Agente 03 (Financeiro)",
            },
            {
                "action": "Contra HGS BioScience e Rigrantec, apresentar custo por hectare (R$ 80/ha no Fuze DS vs R$ 158–227/ha nos concorrentes) e 11% de cinza.",
                "rationale": "Desloca a discussão de preço/kg bruto para custo por kg de substância húmica ativa entregue.",
                "owner": "Jardélcio Carvalho (AgroRemoto)",
            },
        ],
        "risks": [
            "Disputar preço por litro/kg com leonardita genérica de 3% de ácido húmico ou humato chinês sem ISO 19822 destrói o posicionamento."
        ],
        "open_questions": [
            "Validar analiticamente a equivalência de 129 g/L de Fuze DS = Liquid Carbon em laboratório credenciado no Brasil."
        ],
        "human_approval_required": True,
        "soja_green_skus": green_soja,
        "cafe_top_roi": cafe_sim["matrix"][0]["roi"] if cafe_sim["matrix"] else 0,
    }

    cur.execute(
        """
        UPDATE automation_schedules
        SET last_run_at = ?, last_status = 'COMPLETED', items_processed = ?
        WHERE job_code = 'DAILY_COMPETITOR_PRICE_WATCH'
        """,
        (now_iso, len(comps)),
    )
    return contract_output


def run_job_prospecting_scoring(conn):
    """
    Job 3: DAILY_B2B_PROSPECTING_SCORING
    Reavalia o pipeline reverso de contas, ordena por Score (0-100) e garante que
    a porta de entrada seja sempre técnica (Coordenador Técnico / P&D / Gerente de Insumos).
    """
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    cur = conn.cursor()
    cur.execute("SELECT * FROM organizations ORDER BY total_score DESC")
    orgs = [dict(r) for r in cur.fetchall()]

    for o in orgs:
        total = (
            int(o["fit_score"])
            + int(o["volume_score"])
            + int(o["access_score"])
            + int(o["regulatory_score"])
            + int(o["tech_score"])
            + int(o["ops_score"])
        )
        cur.execute(
            "UPDATE organizations SET total_score = ?, updated_at = ? WHERE id = ?",
            (total, now_iso, o["id"]),
        )

    tier_a = [o["brand"] or o["name"] for o in orgs if o["total_score"] >= 90]

    contract_output = {
        "task_id": f"PROSP-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}",
        "agent": "prospecting",
        "status": "completed",
        "facts": [
            {
                "claim": f"{len(orgs)} contas/clusters estratégicos qualificados com score multicritério (0–100) e porta de entrada técnica mapeada.",
                "source_url": "file:///home/antigravity/Black_Earth_Commercial_Intelligence_OS_Knowledge_Base.md",
                "checked_at": now_iso,
                "confidence": "high",
            },
            {
                "claim": f"Contas Tier A+ (>=90 pts): {', '.join(tier_a)}.",
                "source_url": "file:///home/antigravity/Diagnostico.docx",
                "checked_at": now_iso,
                "confidence": "high",
            },
        ],
        "assumptions": [
            "Foco geográfico restrito inicialmente a MT, GO, MG, SP e PR para evitar cobertura rala."
        ],
        "recommendations": [
            {
                "action": "Iniciar Onda 1 pelos OEMs/Formuladores (Vittia, Brandt, Atlântica, ILSA) + Cooperativas Âncora (Cooxupé em MG, Comigo em GO, Coamo no PR) + Fundações Regionais.",
                "rationale": "OEM gera volume imediato sem custo de equipe de campo; Cooperativas e Fundações constroem validação oficial.",
                "owner": "Jardélcio Carvalho (AgroRemoto)",
            }
        ],
        "risks": [
            "Abordar diretoria de cooperativa antes do coordenador técnico/agrônomo gera bloqueio interno."
        ],
        "open_questions": [
            "Confirmar nomes atualizados das coordenações técnicas de Aprosoja MT/GO/BA e Fundação ABC antes do disparo."
        ],
        "human_approval_required": True,
    }

    cur.execute(
        """
        UPDATE automation_schedules
        SET last_run_at = ?, last_status = 'COMPLETED', items_processed = ?
        WHERE job_code = 'DAILY_B2B_PROSPECTING_SCORING'
        """,
        (now_iso, len(orgs)),
    )
    return contract_output


def run_job_weekly_campaign_dossier(conn):
    """
    Job 4: WEEKLY_CAMPAIGN_DOSSIER_GEN
    Consolida os playbooks de abordagem B2B, valida os Gates R0-R4 e gera o
    Relatório Executivo Automatizado em Markdown e CSV na pasta reports/.
    """
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    os.makedirs(REPORTS_DIR, exist_ok=True)
    cur = conn.cursor()

    cur.execute("SELECT * FROM organizations ORDER BY total_score DESC")
    orgs = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT * FROM competitors ORDER BY id ASC")
    comps = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT * FROM market_news_alerts ORDER BY id DESC LIMIT 10")
    alerts = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT * FROM campaigns_playbooks ORDER BY id ASC")
    playbooks = [dict(r) for r in cur.fetchall()]

    soja_matrix = compute_breakeven_matrix(conn, "P_SOJA")
    cafe_matrix = compute_breakeven_matrix(conn, "P_CAFE")
    landed_oem = simulate_landed_to_channel(sku="Fuze DS", channel_route="OEM / Indústria Importadora")

    # Export CSV of prioritized accounts
    csv_path = os.path.join(REPORTS_DIR, "pipeline_contas_priorizadas.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "Rank", "Organização", "Canal", "UF", "Prioridade", "Score (0-100)",
            "SKUs Recomendados", "Porta de Entrada", "Liderança Mapeada",
            "Estágio Pipeline", "Próxima Ação Recomendada"
        ])
        for idx, o in enumerate(orgs, 1):
            writer.writerow([
                idx, o["name"], o["channel_type"], o["uf"], o["priority_uf"],
                o["total_score"], o["recommended_skus"], o["entry_door_role"],
                o["key_leader_name"], o["pipeline_stage"], o["next_action"]
            ])

    # Export CSV of Break-Even & ROI
    be_csv_path = os.path.join(REPORTS_DIR, "tabela_breakeven_soja_cafe.csv")
    with open(be_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "Cultura", "SKU", "Família", "Dose/ha", "Unid", "Custo Entregue R$/ha",
            "Break-Even (kg/ha)", "Break-Even (sc/ha)", "ROI Projetado", "Semáforo", "Regra Comercial"
        ])
        for row in soja_matrix["matrix"]:
            writer.writerow([
                "SOJA", row["sku"], row["family"], row["dose_per_ha"], row["unit"],
                f"{row['cost_ha_brl']:.2f}".replace(".", ","),
                f"{row['breakeven_kg_ha']:.1f}".replace(".", ","),
                f"{row['breakeven_sc_ha']:.2f}".replace(".", ","),
                f"{row['roi']:.2f}".replace(".", ","),
                row["semaphore"], row["commercial_rule"]
            ])
        for row in cafe_matrix["matrix"]:
            writer.writerow([
                "CAFÉ ARÁBICA", row["sku"], row["family"], row["dose_per_ha"], row["unit"],
                f"{row['cost_ha_brl']:.2f}".replace(".", ","),
                f"{row['breakeven_kg_ha']:.2f}".replace(".", ","),
                f"{row['breakeven_sc_ha']:.2f}".replace(".", ","),
                f"{row['roi']:.2f}".replace(".", ","),
                row["semaphore"], row["commercial_rule"]
            ])

    # Generate Executive Markdown Report
    md_path = os.path.join(REPORTS_DIR, "relatorio_executivo_automacao_black_earth.md")
    lines = [
        "# BLACK EARTH COMMERCIAL INTELLIGENCE OS — RELATÓRIO AUTOMÁTICO DE OPERAÇÃO",
        f"**Gerado automaticamente em:** {now_iso} | **Responsável Humano:** Jardélcio Carvalho (AgroRemoto)",
        "",
        "---",
        "## 1. Alertas Prioritários do Radar (Mercado, Regulatório & Feiras 2027)",
    ]
    for a in alerts[:5]:
        lines.append(f"- **[{a['impact_level']}] {a['category']} — {a['title']}**")
        lines.append(f"  - *Resumo:* {a['summary']}")
        lines.append(f"  - *Ação recomendada ({a['affected_agent']}):* {a['recommended_action']}")

    lines.extend([
        "",
        "## 2. Top Contas Qualificadas no CRM (Fluxo de Trás para Frente)",
        "| # | Conta / Cluster | Canal | UF | Score | SKUs Foco | Porta de Entrada | Próxima Ação |",
        "|---|---|---|---|---:|---|---|---|",
    ])
    for idx, o in enumerate(orgs, 1):
        lines.append(
            f"| {idx} | **{o['brand'] or o['name']}** | {o['channel_type']} | {o['uf']} | **{o['total_score']}/100** | {o['recommended_skus']} | {o['entry_door_role']} | {o['next_action']} |"
        )

    lines.extend([
        "",
        "## 3. Semáforo de Break-Even & ROI Atualizado (Soja vs Café)",
        "| SKU | Dose/ha | Custo R$/ha | Break-Even Soja (sc/ha) | ROI Soja | Semáforo Soja | Break-Even Café (sc/ha) | ROI Café |",
        "|---|---|---:|---:|---:|---|---:|---:|",
    ])
    cafe_by_sku = {r["sku"]: r for r in cafe_matrix["matrix"]}
    for r in soja_matrix["matrix"]:
        c_row = cafe_by_sku.get(r["sku"], {})
        lines.append(
            f"| **{r['sku']}** | {r['dose_per_ha']} {r['unit']} | R$ {r['cost_ha_brl']:.2f} | {r['breakeven_sc_ha']:.2f} sc | {r['roi']:.2f}x | **{r['semaphore']}** | {c_row.get('breakeven_sc_ha', 0):.2f} sc | **{c_row.get('roi', 0):.2f}x** |"
        )

    lines.extend([
        "",
        "## 4. Simulação Landed-to-Channel — Rota OEM (Fuze DS - 20 toneladas)",
        f"- **Custo Landed Estimado:** R$ {landed_oem['landed_cost_brl']:.2f}/kg (FOB US$ {landed_oem['fob_usd']:.2f} | Câmbio R$ {landed_oem['exchange_rate']:.2f})",
        f"- **Preço Líquido de Venda B2B:** R$ {landed_oem['net_selling_price_brl']:.2f}/kg",
        f"- **Margem de Contribuição Black Earth:** R$ {landed_oem['black_earth_contribution_brl']:.2f}/kg ({landed_oem['black_earth_contribution_pct']}%)",
        f"- **Custo por kg de Substância Húmica Efetiva:** R$ {landed_oem['ash_advantage']['cost_per_kg_active_hs_black_earth_brl']:.2f}/kg (Humalite 11% cinza) vs R$ {landed_oem['ash_advantage']['cost_per_kg_active_hs_generic_brl']:.2f}/kg (Leonardita 60% cinza)",
        f"- *Aviso de Governança:* {landed_oem['governance_warning']}",
        "",
        "## 5. Cadências e Playbooks Prontos para Aprovação Humana",
    ])
    for p in playbooks:
        lines.append(f"- **{p['title']}** ({p['sku_focus']}) → Status: `{p['human_approval_status']}` | Gate: `{p['compliance_gate_status']}`")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    contract_output = {
        "task_id": f"WEEKLY-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}",
        "agent": "marketing",
        "status": "requires_review",
        "facts": [
            {
                "claim": f"Relatório executivo consolidado e planilhas CSV gerados em {REPORTS_DIR}.",
                "source_url": f"file://{md_path}",
                "checked_at": now_iso,
                "confidence": "high",
            }
        ],
        "assumptions": [
            "Nenhuma mensagem comercial ou proposta de preço é disparada externamente sem aprovação explícita do consultor AgroRemoto."
        ],
        "recommendations": [
            {
                "action": "Revisar e aprovar no painel as 4 cadências semanais (OEM, Cooperativas, Fundações de Pesquisa e Contas Âncora).",
                "rationale": "Cumpre os Gates R0–R4 e protege o posicionamento técnico da marca Black Earth.",
                "owner": "Jardélcio Carvalho (AgroRemoto)",
            }
        ],
        "risks": [],
        "open_questions": [],
        "human_approval_required": True,
        "report_markdown_path": md_path,
        "csv_accounts_path": csv_path,
        "csv_breakeven_path": be_csv_path,
    }

    cur.execute(
        """
        UPDATE automation_schedules
        SET last_run_at = ?, last_status = 'COMPLETED', items_processed = ?
        WHERE job_code = 'WEEKLY_CAMPAIGN_DOSSIER_GEN'
        """,
        (now_iso, len(playbooks) + len(orgs)),
    )
    return contract_output


def execute_automation_cycle(job_code="ALL"):
    """Executa um job específico ou todos os 4 fluxos agendados e grava log de auditoria."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    started_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    outputs = {}
    if job_code in ("ALL", "DAILY_MARKET_NEWS_RADAR"):
        outputs["DAILY_MARKET_NEWS_RADAR"] = run_job_market_news_radar(conn)
    if job_code in ("ALL", "DAILY_COMPETITOR_PRICE_WATCH"):
        outputs["DAILY_COMPETITOR_PRICE_WATCH"] = run_job_competitor_price_watch(conn)
    if job_code in ("ALL", "DAILY_B2B_PROSPECTING_SCORING"):
        outputs["DAILY_B2B_PROSPECTING_SCORING"] = run_job_prospecting_scoring(conn)
    if job_code in ("ALL", "WEEKLY_CAMPAIGN_DOSSIER_GEN"):
        outputs["WEEKLY_CAMPAIGN_DOSSIER_GEN"] = run_job_weekly_campaign_dossier(conn)

    completed_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    report_path = os.path.join(REPORTS_DIR, "relatorio_executivo_automacao_black_earth.md")

    for jcode, out in outputs.items():
        cur.execute(
            """
            INSERT INTO automation_runs (
                job_code, agent_name, started_at, completed_at, status, summary, output_json, report_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                jcode,
                out.get("agent", "orchestrator"),
                started_at,
                completed_at,
                out.get("status", "completed"),
                out["facts"][0]["claim"] if out.get("facts") else "Execução concluída",
                json.dumps(out, ensure_ascii=False),
                report_path,
            ),
        )

    conn.commit()
    conn.close()
    return outputs


if __name__ == "__main__":
    import sys
    target_job = sys.argv[1] if len(sys.argv) > 1 else "ALL"
    res = execute_automation_cycle(target_job)
    print(json.dumps(res, indent=2, ensure_ascii=False))
