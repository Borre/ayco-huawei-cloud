#!/usr/bin/env python3
"""AYCO Tools API — Enhanced con persistencia SQLite, audit log, y endpoints completos."""
import json, hashlib, http.server, os, sqlite3, time, uuid
from datetime import datetime, timedelta

PORT = 8400
DB_PATH = "/opt/ayco/tools.db"

# ── Database Init ──
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.execute("""
        CREATE TABLE IF NOT EXISTS planes_aplicados (
            id TEXT PRIMARY KEY, cliente TEXT, tipo_plan TEXT,
            monto_total REAL, meses INTEGER, pago_mensual REAL,
            fecha_inicio TEXT, estado TEXT, created_at TEXT
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS cartas_generadas (
            id TEXT PRIMARY KEY, cliente TEXT, etapa TEXT,
            contenido TEXT, fecha TEXT, created_at TEXT
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS consultas_buro (
            id TEXT PRIMARY KEY, cliente TEXT, score TEXT,
            num_creditos INTEGER, created_at TEXT
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT, cliente TEXT, request TEXT, response TEXT, created_at TEXT
        )
    """)
    db.commit()
    return db

# ── Buro Credit Simulator ──
BURO_PROFILES = {
    "CLI-001": {"score": "Excelente", "creditos": [
        {"tipo": "Crédito Hipotecario", "monto": 2800000, "saldo": 1950000, "estatus": "Al corriente", "dias_atraso": 0},
        {"tipo": "Crédito Automotriz", "monto": 450000, "saldo": 120000, "estatus": "Al corriente", "dias_atraso": 0},
    ]},
    "CLI-002": {"score": "Regular", "creditos": [
        {"tipo": "Crédito Personal", "monto": 85000, "saldo": 65000, "estatus": "Atraso 60 días", "dias_atraso": 67},
        {"tipo": "Tarjeta de Crédito", "monto": 30000, "saldo": 28000, "estatus": "Atraso 30 días", "dias_atraso": 34},
    ]},
    "CLI-003": {"score": "Malo", "creditos": [
        {"tipo": "Crédito Personal", "monto": 120000, "saldo": 118000, "estatus": "Atraso 120+ días", "dias_atraso": 135},
        {"tipo": "Tarjeta de Crédito", "monto": 45000, "saldo": 44000, "estatus": "Quebranto", "dias_atraso": 190},
        {"tipo": "Préstamo Nómina", "monto": 35000, "saldo": 34000, "estatus": "Atraso 90 días", "dias_atraso": 95},
    ]},
}

PLANES = {
    "PAGOS_FIJOS": {"nombre": "Plan de Pagos Fijos", "desc": "0% interés adicional", "min_meses": 3, "max_meses": 36},
    "REESTRUCTURA": {"nombre": "Reestructura a Plazo", "desc": "Tasa original congelada", "min_meses": 12, "max_meses": 48},
    "LIQUIDACION_QUITA": {"nombre": "Liquidación con Quita", "desc": "Descuento único 30-50%", "min_meses": 1, "max_meses": 1},
    "EMERGENCIA": {"nombre": "Plan de Emergencia", "desc": "Solo intereses 6 meses", "min_meses": 6, "max_meses": 6},
    "ADELANTO_PARCIAL": {"nombre": "Adelanto Parcial", "desc": "Reduce saldo, baja mensualidad", "min_meses": 1, "max_meses": 12},
}

class ToolsHandler(http.server.BaseHTTPRequestHandler):
    db = None  # Shared across instances (module-level but set at startup)
    
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        resp = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(resp.encode())

    def _parse_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except:
            return {}

    def _audit(self, endpoint, cliente, request_data, response_data):
        if self.db:
            self.db.execute(
                "INSERT INTO audit_log (endpoint, cliente, request, response, created_at) VALUES (?, ?, ?, ?, ?)",
                (endpoint, cliente, json.dumps(request_data), json.dumps(response_data)[:2000], datetime.utcnow().isoformat())
            )
            self.db.commit()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            stats = {}
            if self.db:
                stats = {
                    "planes": self.db.execute("SELECT count(*) FROM planes_aplicados").fetchone()[0],
                    "cartas": self.db.execute("SELECT count(*) FROM cartas_generadas").fetchone()[0],
                    "consultas_buro": self.db.execute("SELECT count(*) FROM consultas_buro").fetchone()[0],
                }
            self._send_json({
                "status": "ok",
                "service": "AYCO Tools API v2",
                "uptime": "operational",
                "database": "sqlite" if self.db else "unavailable",
                "stats": stats,
                "endpoints": [
                    "POST /api/v1/aplicar_plan_pago",
                    "POST /api/v1/consultar_buro_credito",
                    "POST /api/v1/generar_carta_cobranza",
                    "POST /api/v1/get_contract_status",
                    "POST /api/v1/send_email",
                    "POST /api/v1/resumen_cliente",
                ]
            })
        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        body = self._parse_body()
        now = datetime.utcnow().isoformat()
        
        # ── aplicar_plan_pago ──
        if self.path == "/api/v1/aplicar_plan_pago":
            cliente = body.get("cliente", "CLI-000")
            plan = body.get("plan", "PAGOS_FIJOS").upper()
            meses = min(body.get("meses", 6), PLANES.get(plan, {}).get("max_meses", 36))
            meses = max(meses, PLANES.get(plan, {}).get("min_meses", 1))
            monto = body.get("monto", 0)
            
            if plan not in PLANES:
                self._send_json({"success": False, "error": f"Plan '{plan}' no válido. Opciones: {list(PLANES.keys())}"}, 400)
                return
            
            pago = round(monto / meses, 2) if meses > 0 else round(monto * 0.6, 2)  # Quita ~40%
            inicio = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d")
            conv_id = f"AYC-CONV-{datetime.utcnow().strftime('%Y%m%d')}-{abs(hash(cliente+monto)) % 10000:04d}"
            
            result = {
                "success": True,
                "plan_aplicado": {
                    "tipo": plan,
                    "nombre": PLANES[plan]["nombre"],
                    "descripcion": PLANES[plan]["desc"],
                    "cliente": cliente,
                    "monto_total": monto,
                    "meses": meses,
                    "pago_mensual": pago,
                    "fecha_inicio": inicio,
                    "id_convenio": conv_id,
                    "estado": "ACTIVO"
                },
                "mensaje": f"✓ {PLANES[plan]['nombre']} aplicado para {cliente}. {meses} pagos de ${pago:,.2f} MXN desde {inicio}. ID: {conv_id}"
            }
            
            if self.db:
                self.db.execute(
                    "INSERT INTO planes_aplicados VALUES (?,?,?,?,?,?,?,?,?)",
                    (conv_id, cliente, plan, monto, meses, pago, inicio, "ACTIVO", now)
                )
                self.db.commit()
            
            self._audit("aplicar_plan_pago", cliente, body, result)
            self._send_json(result)

        # ── consultar_buro_credito ──
        elif self.path == "/api/v1/consultar_buro_credito":
            cliente = body.get("cliente", "CLI-000")
            ident = body.get("identificador", cliente)
            
            profile = BURO_PROFILES.get(ident)
            if not profile:
                seed = int(hashlib.md5(ident.encode()).hexdigest()[:8], 16)
                scores = ["Excelente", "Bueno", "Regular", "Malo"]
                profile = {
                    "score": scores[seed % 4],
                    "creditos": []
                }
                if seed % 4 < 2:
                    profile["creditos"] = [
                        {"tipo": "Crédito Personal", "monto": 85000, "saldo": 45000, "estatus": "Al corriente", "dias_atraso": 0},
                        {"tipo": "Tarjeta de Crédito", "monto": 20000, "saldo": 5000, "estatus": "Al corriente", "dias_atraso": 0}
                    ]
                elif seed % 4 == 2:
                    profile["creditos"] = [
                        {"tipo": "Crédito Personal", "monto": 85000, "saldo": 65000, "estatus": "Atraso 60 días", "dias_atraso": 67}
                    ]
                else:
                    profile["creditos"] = [
                        {"tipo": "Crédito Personal", "monto": 50000, "saldo": 48000, "estatus": "Atraso 120+ días", "dias_atraso": 130},
                        {"tipo": "Tarjeta de Crédito", "monto": 15000, "saldo": 14800, "estatus": "Quebranto", "dias_atraso": 180}
                    ]
            
            saldo_total = sum(c["saldo"] for c in profile["creditos"])
            atrasos = [c for c in profile["creditos"] if c["dias_atraso"] > 30]
            
            result = {
                "success": True,
                "cliente": cliente,
                "score_buro": profile["score"],
                "creditos_activos": profile["creditos"],
                "total_creditos": len(profile["creditos"]),
                "saldo_total": saldo_total,
                "creditos_con_atraso": len(atrasos),
                "recomendacion": "APROBAR" if profile["score"] in ["Excelente", "Bueno"] else ("REVISAR" if profile["score"] == "Regular" else "RECHAZAR"),
                "consulta_id": str(uuid.uuid4())[:8]
            }
            
            if self.db:
                self.db.execute(
                    "INSERT INTO consultas_buro VALUES (?,?,?,?,?)",
                    (result["consulta_id"], cliente, profile["score"], len(profile["creditos"]), now)
                )
                self.db.commit()
            
            self._audit("consultar_buro_credito", cliente, body, result)
            self._send_json(result)

        # ── generar_carta_cobranza ──
        elif self.path == "/api/v1/generar_carta_cobranza":
            cliente = body.get("cliente", "CLI-000")
            etapa = body.get("etapa", "ADMINISTRATIVA").upper()
            monto = body.get("monto", 0)
            dias = body.get("dias_atraso", 45)
            plan_sugerido = body.get("plan_sugerido", "PAGOS_FIJOS")
            
            cartas = {
                "PREVENTIVA": {
                    "asunto": "Recordatorio de Pago",
                    "contenido": f"Estimado(a) cliente, le recordamos que su pago presenta {dias} días de atraso por un monto de ${monto:,.2f} MXN. Le invitamos a regularizar sin cargos adicionales. Contacte a su ejecutivo al 800-AYCO-MX."
                },
                "ADMINISTRATIVA": {
                    "asunto": f"Aviso Formal de Cobranza — {dias} días de atraso",
                    "contenido": f"Aviso formal de cobranza. Adeudo de ${monto:,.2f} MXN con {dias} días de atraso. Se aplicarán cargos moratorios del 5% mensual. Le sugerimos acogerse al plan {plan_sugerido}. Contacte al área de cobranza al 800-AYCO-CBZ antes del {(datetime.utcnow() + timedelta(days=15)).strftime('%d/%m/%Y')}."
                },
                "PRE_JUDICIAL": {
                    "asunto": f"ÚLTIMO AVISO — Transferencia a Jurídico Inminente",
                    "contenido": f"ÚLTIMO AVISO. Adeudo de ${monto:,.2f} MXN con {dias} días de atraso. De no recibir pago o convenio en 5 días hábiles, el caso será transferido al despacho jurídico externo. Última oportunidad de negociación con quita del 40% sobre intereses moratorios. Comuníquese de inmediato al 800-AYCO-LEGAL."
                }
            }
            
            carta_info = cartas.get(etapa, cartas["ADMINISTRATIVA"])
            carta_id = f"AYC-CARTA-{datetime.utcnow().strftime('%Y%m')}-{abs(hash(cliente)) % 10000:04d}"
            
            result = {
                "success": True,
                "carta_generada": {
                    "id": carta_id,
                    "cliente": cliente,
                    "etapa": etapa,
                    "asunto": carta_info["asunto"],
                    "fecha": datetime.utcnow().strftime("%Y-%m-%d"),
                    "contenido": carta_info["contenido"],
                    "firma": "Lic. Roberto Mendoza — Jefe de Cobranza AYCO",
                    "entregable": f"/opt/ayco/cartas/{carta_id}.pdf"
                },
                "mensaje": f"✓ Carta de cobranza ({etapa}) generada para {cliente}. ID: {carta_id}"
            }
            
            if self.db:
                self.db.execute(
                    "INSERT INTO cartas_generadas VALUES (?,?,?,?,?,?)",
                    (carta_id, cliente, etapa, carta_info["contenido"], datetime.utcnow().strftime("%Y-%m-%d"), now)
                )
                self.db.commit()
            
            self._audit("generar_carta_cobranza", cliente, body, result)
            self._send_json(result)

        # ── get_contract_status (NUEVO) ──
        elif self.path == "/api/v1/get_contract_status":
            cliente = body.get("cliente", "CLI-000")
            contract_id = body.get("contract_id", "AYC-CONT-0001")
            
            estados = ["Activo", "En mora", "Vencido", "Liquidado", "En litigio"]
            seed = int(hashlib.md5(contract_id.encode()).hexdigest()[:8], 16)
            estado = estados[seed % len(estados)]
            
            result = {
                "success": True,
                "contract_id": contract_id,
                "cliente": cliente,
                "estado": estado,
                "fecha_contrato": "2025-08-15",
                "fecha_vencimiento": "2027-08-15",
                "monto_original": 150000,
                "saldo_actual": 89000 if estado != "Liquidado" else 0,
                "pagos_realizados": 14,
                "pagos_pendientes": 10 if estado != "Liquidado" else 0,
                "ultimo_pago": "2026-04-01",
                "dias_atraso": 45 if estado == "En mora" else 0,
            }
            self._audit("get_contract_status", cliente, body, result)
            self._send_json(result)

        # ── send_email (NUEVO) ──
        elif self.path == "/api/v1/send_email":
            destinatario = body.get("destinatario", body.get("cliente", "cliente@ejemplo.com"))
            asunto = body.get("asunto", "Comunicado AYCO")
            tipo = body.get("tipo", "CARTA_COBRANZA")
            contenido = body.get("contenido", "Vea el adjunto.")
            
            result = {
                "success": True,
                "email_enviado": {
                    "id": str(uuid.uuid4()),
                    "destinatario": destinatario,
                    "asunto": asunto,
                    "tipo": tipo,
                    "estado": "ENVIADO",
                    "timestamp": now,
                },
                "mensaje": f"✓ Email '{asunto}' enviado a {destinatario}"
            }
            self._audit("send_email", destinatario, body, result)
            self._send_json(result)

        # ── resumen_cliente (NUEVO) ──
        elif self.path == "/api/v1/resumen_cliente":
            cliente = body.get("cliente", "CLI-000")
            
            # Cross-reference all tables for this client
            planes = []
            cartas = []
            consultas = []
            if self.db:
                for row in self.db.execute("SELECT * FROM planes_aplicados WHERE cliente=?", (cliente,)):
                    planes.append({"id": row[0], "tipo": row[2], "monto": row[3], "estado": row[7]})
                for row in self.db.execute("SELECT * FROM cartas_generadas WHERE cliente=?", (cliente,)):
                    cartas.append({"id": row[0], "etapa": row[2], "fecha": row[4]})
                for row in self.db.execute("SELECT * FROM consultas_buro WHERE cliente=?", (cliente,)):
                    consultas.append({"id": row[0], "score": row[2], "fecha": row[4]})
            
            result = {
                "success": True,
                "cliente": cliente,
                "planes_activos": len(planes),
                "planes": planes,
                "cartas_emitidas": len(cartas),
                "cartas": cartas,
                "consultas_buro": len(consultas),
                "score_mas_reciente": consultas[0]["score"] if consultas else "Sin consulta",
            }
            self._audit("resumen_cliente", cliente, body, result)
            self._send_json(result)

        else:
            self._send_json({"error": "endpoint not found", "endpoints_disponibles": [
                "/api/v1/aplicar_plan_pago",
                "/api/v1/consultar_buro_credito", 
                "/api/v1/generar_carta_cobranza",
                "/api/v1/get_contract_status",
                "/api/v1/send_email",
                "/api/v1/resumen_cliente",
            ]}, 404)

    def log_message(self, format, *args):
        pass  # Quiet in production

# ── Init & Start ──
db = init_db()
ToolsHandler.db = db  # Set module-level DB for handler
print(f"✓ AYCO Tools API v2 — SQLite {DB_PATH}")
print(f"✓ {db.execute('SELECT count(*) FROM planes_aplicados').fetchone()[0]} planes en historial")
print(f"✓ {db.execute('SELECT count(*) FROM cartas_generadas').fetchone()[0]} cartas en historial")
print(f"✓ Listening on :{PORT} — 6 endpoints activos")

httpd = http.server.HTTPServer(("0.0.0.0", PORT), ToolsHandler)
httpd.serve_forever()
