#!/usr/bin/env python3
"""
Black Earth Commercial Intelligence OS — Full-Stack Web Server & Background Scheduler Daemon
Serve a aplicação web em http://localhost:8080, expõe a API REST completa para o CRM,
Simulador de Break-Even/Substituição MAP, Simulador Landed-to-Channel, Radar de Concorrência
e Notícias, e mantém um agendador em background (100% automatizado) para os 4 cron jobs.
"""

import json
import mimetypes
import os
import threading
import time
import urllib.parse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from automation_engine import (
    REPORTS_DIR,
    compute_breakeven_matrix,
    execute_automation_cycle,
    simulate_landed_to_channel,
)
from database import get_connection, init_db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
PORT = int(os.environ.get("PORT", "8080"))


def background_cron_loop():
    """
    Loop de agendamento contínuo em background:
    Verifica a cada 60 segundos os horários agendados (07:00, 07:30, 08:00 e Segundas 09:00)
    e executa automaticamente os fluxos sem intervenção humana.
    """
    last_triggered_minute = ""
    while True:
        try:
            now = datetime.now()
            stamp = now.strftime("%Y-%m-%d %H:%M")
            if stamp != last_triggered_minute:
                hm = now.strftime("%H:%M")
                if hm == "07:00":
                    execute_automation_cycle("DAILY_MARKET_NEWS_RADAR")
                    last_triggered_minute = stamp
                elif hm == "07:30":
                    execute_automation_cycle("DAILY_COMPETITOR_PRICE_WATCH")
                    last_triggered_minute = stamp
                elif hm == "08:00":
                    execute_automation_cycle("DAILY_B2B_PROSPECTING_SCORING")
                    last_triggered_minute = stamp
                elif hm == "09:00" and now.weekday() == 0:
                    execute_automation_cycle("WEEKLY_CAMPAIGN_DOSSIER_GEN")
                    last_triggered_minute = stamp
        except Exception as exc:
            print(f"[Scheduler Warning] {exc}")
        time.sleep(30)


class BlackEarthOSHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if path == "/api/overview":
            conn = get_connection()
            cur = conn.cursor()

            cur.execute("SELECT * FROM products ORDER BY priority_tier ASC, id ASC")
            products = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT * FROM organizations ORDER BY total_score DESC")
            organizations = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT * FROM competitors ORDER BY id ASC")
            competitors = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT * FROM market_news_alerts ORDER BY id DESC")
            news_alerts = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT * FROM events_calendar ORDER BY id ASC")
            events = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT * FROM soil_problems ORDER BY estimated_loss_brl_ha DESC")
            soil_problems = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT * FROM campaigns_playbooks ORDER BY id ASC")
            playbooks = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT * FROM automation_schedules ORDER BY id ASC")
            schedules = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT * FROM automation_runs ORDER BY id DESC LIMIT 12")
            runs = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT * FROM market_parameters ORDER BY id ASC")
            parameters = [dict(r) for r in cur.fetchall()]

            breakeven_soja = compute_breakeven_matrix(conn, "P_SOJA")
            breakeven_cafe = compute_breakeven_matrix(conn, "P_CAFE")
            default_landed = simulate_landed_to_channel()

            conn.close()
            return self._send_json({
                "products": products,
                "organizations": organizations,
                "competitors": competitors,
                "news_alerts": news_alerts,
                "events": events,
                "soil_problems": soil_problems,
                "playbooks": playbooks,
                "schedules": schedules,
                "runs": runs,
                "parameters": parameters,
                "breakeven_soja": breakeven_soja,
                "breakeven_cafe": breakeven_cafe,
                "default_landed": default_landed,
            })

        if path == "/api/simulators/breakeven":
            crop_code = qs.get("crop_code", ["P_SOJA"])[0]
            price_str = qs.get("crop_price", [None])[0]
            hc_str = qs.get("haircut", [None])[0]
            conn = get_connection()
            data = compute_breakeven_matrix(
                conn,
                crop_code=crop_code,
                custom_crop_price=float(price_str) if price_str else None,
                custom_haircut=float(hc_str) if hc_str else None,
            )
            conn.close()
            return self._send_json(data)

        if path == "/api/simulators/landed":
            sku = qs.get("sku", ["Fuze DS"])[0]
            fob = float(qs.get("fob_usd", ["7.20"])[0])
            fx = float(qs.get("exchange_rate", ["5.45"])[0])
            freight_pct = float(qs.get("freight_pct", ["12.0"])[0])
            tax_pct = float(qs.get("tax_pct", ["18.5"])[0])
            route = qs.get("route", ["OEM / Indústria Importadora"])[0]
            comm_pct = float(qs.get("commission_pct", ["5.0"])[0])
            margin_pct = float(qs.get("channel_margin_pct", ["22.0"])[0])
            vol = float(qs.get("volume_tons", ["20.0"])[0])

            sim = simulate_landed_to_channel(
                sku=sku,
                fob_usd_unit=fob,
                exchange_rate=fx,
                freight_insurance_pct=freight_pct,
                customs_taxes_non_rec_pct=tax_pct,
                channel_route=route,
                partner_commission_pct=comm_pct,
                channel_margin_pct=margin_pct,
                volume_tons=vol,
            )
            return self._send_json(sim)

        if path == "/api/reports/download":
            fname = qs.get("file", ["relatorio_executivo_automacao_black_earth.md"])[0]
            safe_name = os.path.basename(fname)
            fpath = os.path.join(REPORTS_DIR, safe_name)
            if os.path.isfile(fpath):
                with open(fpath, "rb") as f:
                    content = f.read()
                self.send_response(200)
                ctype = "text/csv; charset=utf-8" if safe_name.endswith(".csv") else "text/markdown; charset=utf-8"
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Disposition", f'attachment; filename="{safe_name}"')
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            return self._send_json({"error": "File not found"}, 404)

        # Serve static files
        if path == "/" or path == "":
            path = "/index.html"
        file_path = os.path.normpath(os.path.join(STATIC_DIR, path.lstrip("/")))
        if file_path.startswith(STATIC_DIR) and os.path.isfile(file_path):
            ctype, _ = mimetypes.guess_type(file_path)
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", ctype or "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            body = json.loads(raw)
        except Exception:
            body = {}

        if path == "/api/automations/trigger":
            job_code = body.get("job_code", "ALL")
            results = execute_automation_cycle(job_code)
            return self._send_json({"status": "ok", "job_code": job_code, "results": results})

        if path == "/api/playbooks/approve":
            pb_id = int(body.get("id", 0))
            new_status = body.get("status", "Aprovado para Disparo (AgroRemoto)")
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "UPDATE campaigns_playbooks SET human_approval_status = ? WHERE id = ?",
                (new_status, pb_id),
            )
            conn.commit()
            conn.close()
            return self._send_json({"status": "ok", "id": pb_id, "human_approval_status": new_status})

        if path == "/api/accounts/stage":
            org_id = int(body.get("id", 0))
            new_stage = body.get("stage", "Abordagem Autorizada")
            now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "UPDATE organizations SET pipeline_stage = ?, updated_at = ? WHERE id = ?",
                (new_stage, now_iso, org_id),
            )
            conn.commit()
            conn.close()
            return self._send_json({"status": "ok", "id": org_id, "pipeline_stage": new_stage})

        if path == "/api/accounts/add":
            now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            name = body.get("name", "").strip()
            if not name:
                return self._send_json({"error": "Nome da organização obrigatório"}, 400)
            fit = int(body.get("fit_score", 22))
            vol = int(body.get("volume_score", 17))
            acc = int(body.get("access_score", 12))
            reg = int(body.get("regulatory_score", 13))
            tech = int(body.get("tech_score", 13))
            ops = int(body.get("ops_score", 8))
            total = fit + vol + acc + reg + tech + ops
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO organizations (
                    name, brand, cnpj_status, channel_type, uf, region, priority_uf,
                    crops, key_leader_name, key_leader_role, entry_door_role,
                    recommended_skus, fit_score, volume_score, access_score,
                    regulatory_score, tech_score, ops_score, total_score,
                    pipeline_stage, provenance_status, next_action, notes, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    body.get("brand", name),
                    body.get("cnpj_status", "Em verificação"),
                    body.get("channel_type", "Cooperativa"),
                    body.get("uf", "MT"),
                    body.get("region", "Centro-Oeste"),
                    body.get("priority_uf", "P1"),
                    body.get("crops", "Soja, Milho"),
                    body.get("key_leader_name", "A confirmar"),
                    body.get("key_leader_role", "Coordenador Técnico"),
                    body.get("entry_door_role", "Coordenador Técnico / Gerente de Insumos"),
                    body.get("recommended_skus", "Alpha, Fuze DS, Magna"),
                    fit, vol, acc, reg, tech, ops, total,
                    "Empresa Mapeada",
                    "Hipótese (Adicionado pelo Consultor)",
                    body.get("next_action", "Validar coordenador técnico e enviar protocolo DBC"),
                    body.get("notes", ""),
                    now_iso,
                ),
            )
            conn.commit()
            conn.close()
            return self._send_json({"status": "ok", "total_score": total})

        self._send_json({"error": "Unknown endpoint"}, 404)


if __name__ == "__main__":
    init_db()
    t = threading.Thread(target=background_cron_loop, daemon=True)
    t.start()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), BlackEarthOSHandler)
    print(f"Black Earth Commercial Intelligence OS listening on http://localhost:{PORT}")
    server.serve_forever()
