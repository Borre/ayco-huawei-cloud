---
title: AYCO × Huawei Cloud — Guía de Handover para Presentador
subtitle: Demos para Workshop de Transformación Digital · Mayo 2026
author: Preparado por Eduardo (CTO LATAM)
geometry: margin=2.5cm
fontsize: 11pt
toc: true
toc-depth: 3
numbersections: true
---

# Resumen Ejecutivo

## Qué es esto

Tres demos técnicos que muestran cómo AYCO (Grupo Salinas) moderniza su plataforma de crédito y cobranza usando Huawei Cloud. Cada demo es independiente y dura 5-7 minutos. El workshop completo toma 20 minutos con Q&A.

## Las 3 Demos

| # | Demo | Duración | Tecnología Clave | URL |
|---|------|----------|-----------------|-----|
| 1 | Risk Scoring | 5 min | DWS + DLI Spark | http://149.232.129.39/risk-scoring/ |
| 2 | Data Governance | 5 min | Frontend + DataArts (Plan B) | http://149.232.129.39/data-governance/ |
| 3 | Contract AI | 10 min | Dify + DeepSeek V4 | http://101.44.185.139 |

## Público Objetivo

- **Primario:** Dirección General, Comités de Crédito y Cobranza
- **Secundario:** Áreas de TI, Innovación, Riesgos
- **Tono:** Técnico-ejecutivo. Datos duros, no PowerPoint theater. "Esto está corriendo en vivo, no es un mockup."

## Lo Que Necesitas Saber (30 Segundos)

1. AYCO es una financiera del ecosistema Grupo Salinas
2. Procesan ~5,000 transacciones/mes de proveedores y créditos
3. Están migrando de infraestructura on-premise legacy a Huawei Cloud
4. El workshop muestra 3 casos de uso reales corriendo en vivo
5. Todo está en la región la-north-2 (CDMX)

---

# Arquitectura General

## Infraestructura Cloud

```
┌─────────────────────────────────────────────────────────┐
│                   Huawei Cloud la-north-2                 │
│                   Proyecto: fbb6435c...                   │
│                                                           │
│  ┌──────────────────┐  ┌──────────────────┐              │
│  │  ECS: ayco-dify   │  │  ECS: ayco-web    │              │
│  │  101.44.185.139   │  │  149.232.129.39   │              │
│  │                    │  │                    │              │
│  │  Dify Platform     │  │  Frontend Astro    │              │
│  │  ├ 3 Apps          │  │  ├ 4 páginas       │              │
│  │  ├ 3 Datasets      │  │  └ Proxy → Dify    │              │
│  │  ├ Streamlit :8501 │  │                    │              │
│  │  └ Agent Tools     │  └──────────────────┘              │
│  └──────────────────┘                                      │
│                                                           │
│  ┌──────────────────┐  ┌──────────────────┐              │
│  │  DWS Cluster      │  │  OBS (3 buckets)  │              │
│  │  46.250.168.254    │  │  ├ contracts-raw  │              │
│  │  8000             │  │  ├ contracts-text │              │
│  │  risk_results(24) │  │  └ contracts-res  │              │
│  └──────────────────┘  └──────────────────┘              │
│                                                           │
│  ┌──────────────────┐  ┌──────────────────┐              │
│  │  FunctionGraph    │  │  DLI (serverless) │              │
│  │  3 funciones OCR  │  │  DB: ayco        │              │
│  │  Trigger: OBS     │  │  (on-demand)      │              │
│  └──────────────────┘  └──────────────────┘              │
│                                                           │
│  ┌──────────────────┐                                     │
│  │  DataArts Studio  │  ❌ NO PROVISIONADO                │
│  │  (Plan B)         │  Razón: billing prePaid mensual   │
│  └──────────────────┘                                     │
└─────────────────────────────────────────────────────────┘
```

## Cómo Acceder

| Recurso | URL / Comando | Credenciales |
|---------|--------------|-------------|
| Frontend (Demo 1, 2) | http://149.232.129.39 | Público |
| Dify (Demo 3) | http://101.44.185.139 | eduardo@ayco-demo.com / ver 1Password |
| **Dashboard Streamlit** | http://101.44.185.139:8501 | Público (desde IP del presentador) |
| **Agent Tools** | localhost:8400 (via SSH) | Solo localhost — SG bloquea acceso externo |
| DWS (psql) | 46.250.168.254:8000 | ayco_admin / ver 1Password |
| SSH Dify | ssh -i ~/.ssh/ayco-demo root@101.44.185.139 | Key SSH en repo |
| SSH Web | ssh -i ~/.ssh/ayco-demo root@149.232.129.39 | Key SSH en repo |

**⚠️ La llave SSH está en el repo:** `~/.ssh/ayco-demo`. Debes copiarla a tu máquina.

---

# Checklist Pre-Demo (30 Minutos Antes)

Ejecuta estos comandos EN ORDEN. Si algo falla, ve a la sección de emergencia.

```
# 1. Verificar SSH a ambos servidores
ssh -i ~/.ssh/ayco-demo root@101.44.185.139 'hostname'
ssh -i ~/.ssh/ayco-demo root@149.232.129.39 'hostname'

# 2. Verificar Dify
curl -s http://101.44.185.139/console/api/version?current_version=1.0.0

# 3. Verificar DWS
PGPASSWORD=AycoD3mo2026! psql -h 46.250.168.254 -p 8000 -U ayco_admin -d ayco_db -c "SELECT count(*) FROM risk_results;"

# 4. Verificar frontend
for p in "" "/risk-scoring/" "/data-governance/" "/contract-ai/"; do
  echo "$p: $(curl -s -o /dev/null -w '%{http_code}' http://149.232.129.39$p)"
done

# 5. Verificar dashboard
curl -s -o /dev/null -w '%{http_code}' http://101.44.185.139:8501

# 6. Verificar Agent Tools
# NOTA: puerto 8400 no expuesto (SG). Verificar via SSH:
ssh -i ~/.ssh/ayco-demo root@101.44.185.139 'curl -s http://localhost:8400/health'
```

---

# Demo 1 — Risk Scoring (5 minutos)

**URL:** http://149.232.129.39/risk-scoring/
**Objetivo:** Mostrar evaluación de riesgo financiero en tiempo real.

## Narrativa

**Apertura (30 seg):**
"AYCO procesa más de 5,000 transacciones mensuales de proveedores. Cada una representa riesgo. Con Huawei Cloud podemos evaluar ese riesgo en segundos, no en días. Esto corre en vivo."

**Demostración (3 min):**

1. **KPIs (1 min):** Señalar los 4 KPIs superiores
   - "24 contratos en DWS. +5.2% este mes."
   - "24 contratos procesados analizadas."
   - "47 alertas CNBV activas, 12 críticas." ← Punto de tensión
   - "Exposición total: $2.1 mil millones de pesos."

2. **Dashboard Streamlit (1 min):** El iframe muestra datos
   - Si no carga: "El dashboard se conecta directo a DWS. Los KPIs muestran los datos agregados en vivo."

3. **Gauge de Riesgo (30 seg):**
   - "Riesgo promedio global: 5.8/10. Categoría Alto."
   - Señalar distribución por nivel (5 bajo, 5 medio, 11 alto, 3 crítico)

4. **Top 5 Proveedores (30 seg):**
   - "Constructora Delta MX: score 8.7, $385M exposición. Priorización automática."

**Cierre (30 seg):**
"Todo sobre DWS de Huawei Cloud. 2 nodos, datos en vivo, sin infraestructura que mantener."

---

# Demo 2 — Data Governance (5 minutos)

**URL:** http://149.232.129.39/data-governance/
**Objetivo:** Mostrar el pipeline de datos end-to-end.

## Narrativa

**Apertura (30 seg):**
"El scoring no aparece de la nada. Hay un pipeline que ingiere, transforma y expone datos. Esto es gobierno de datos."

**Demostración (3 min):**

1. **Pipeline Visual (1 min):**
   - CNBV Data → DLI Spark → DWS → API DataService
   - "De CSV crudo a datos listos en menos de 2 minutos."

2. **API Explorer (1 min):**
   - Probar GET /risk-results
   - "Esta misma API alimenta el dashboard del Demo 1."

**Transición DataArts (1 min):**
"En producción, DataArts agrega gobierno automatizado: catálogo, linaje, reglas de calidad. Por restricciones de billing prePaid, está en sandbox. Les muestro cómo se ve."

Mostrar screenshots de `docs/screenshots/dataarts/`:
1. Workspace Overview
2. Data Catalog (tablas AYCO)
3. Data Lineage (OBS → DLI → DWS)
4. Quality Rules

**Cierre (30 seg):**
"Gobierno automatizado. Sin silos, sin scripts manuales, sin 'yo creo que los datos están bien'."

---

# Demo 3 — Contract AI (10 minutos)

**URL:** http://101.44.185.139
**Login:** eduardo@ayco-demo.com / ver 1Password

## 3a. AYCO Chat — FAQ (3 min)

**URL:** http://101.44.185.139/chat/253ad7c8-1cd7-44ea-a27d-9d67f031e5a1

**Preguntas sugeridas:**

1. "¿Cómo solicito un crédito personal con AYCO?"
2. "¿Qué pasa si no pago a tiempo mi crédito?"
3. "¿Puedo adelantar pagos sin penalización?"

**Puntos a destacar:** Respuestas de 9 documentos de políticas AYCO. < 2 segundos.

## 3b. AYCO Cobranza — Agent con Tools (4 min)

**URL:** http://101.44.185.139/chat/7e0472b6-249f-47bb-a2c1-cf298b7287f7

**Flujo:**

1. "Tengo un cliente que debe $45,000. ¿Qué opciones de pago hay?" → Muestra 5 planes
2. "Aplícale plan de pagos fijos a 12 meses." → Devuelve plan_id, cuota, plazo
3. "Consulta su buró de crédito, cliente CLI-001." → Devuelve score, historial
4. "Genérale una carta de recordatorio." → Devuelve carta_id, texto

**Punto clave:** El agente NO solo responde — ejecuta acciones en sistemas.

## 3c. AYCO Doc Analyzer — OCR (3 min)

**URL:** http://101.44.185.139/chat/b7e99855-1fc9-4374-82c8-9a47693205d7

**Preparación:** Tener `contrato-01-alto-riesgo.pdf` descargado de `data/contracts/`.

**Flujo:**

1. Subir factura → Clasifica FACTURA, extrae RFC, monto, IVA
2. Subir INE → Clasifica INE, extrae CURP, nombre
3. Subir contrato → Clasifica CONTRATO, extrae cláusulas, riesgo

**5 tipos de documentos:** Factura, INE, Carta Cobranza, Estado de Cuenta, Contrato.

---

# Procedimientos de Emergencia

## Dify no responde (Error 502)

```bash
ssh -i ~/.ssh/ayco-demo root@101.44.185.139
cd /opt/ayco/dify/docker && docker compose restart api worker web
# Esperar 15s
curl -s http://localhost/console/api/version?current_version=1.0.0
```

## Dashboard Streamlit caído

```bash
ssh ayco-dify 'systemctl restart streamlit-dashboard'
curl -s -o /dev/null -w '%{http_code}' http://101.44.185.139:8501
```

## Agent Tools caído

```bash
ssh ayco-dify 'systemctl restart ayco-tools'
# Puerto 8400 no expuesto — verificar via SSH:
ssh ayco-dify 'curl -s http://localhost:8400/health'
```

### Redeploy (si se pierde el server.py o el service)
```bash
cd /home/eduardo/dev/ayco-huawei-cloud
ECS_IP=101.44.185.139 SSH_KEY_PATH=~/.ssh/ayco-demo bash scripts/deploy-agent-tools.sh
```

## Frontend caído

```bash
ssh ayco-web 'systemctl restart nginx'
```

## TODO caído (Apocalipsis)

```bash
ssh ayco-dify 'docker compose restart'  # 11 containers
ssh ayco-dify 'systemctl restart streamlit-dashboard ayco-tools'
# Verificar: ssh ayco-dify 'curl -s http://localhost:8400/health'
ssh ayco-web 'systemctl restart nginx'
# Esperar 60 segundos
# Si sigue caído: usar screenshots + narrativa verbal
```

---

# Quick Reference

## URLs

| Recurso | URL |
|---------|-----|
| Frontend | http://149.232.129.39 |
| Risk Scoring | http://149.232.129.39/risk-scoring/ |
| Data Governance | http://149.232.129.39/data-governance/ |
| Dify | http://101.44.185.139 |
| FAQ Chat | http://101.44.185.139/chat/253ad7c8-1cd7-44ea-a27d-9d67f031e5a1 |
| Cobranza Agent | http://101.44.185.139/chat/7e0472b6-249f-47bb-a2c1-cf298b7287f7 |
| Doc Analyzer | http://101.44.185.139/chat/b7e99855-1fc9-4374-82c8-9a47693205d7 |
| Dashboard | http://101.44.185.139:8501 |

## API Keys

| App | Key |
|-----|-----|
| Chat | app-Y8MxfRygyUWOAfyTlo1MQSJx |
| Agent | app-ZrM7Pal6G2b89drd1zLVssvM |
| Workflow | app-mGyFcdX7vT3CZDDsvttCX6iF |

## Comandos Críticos

```
# Reiniciar Dify
ssh ayco-dify 'cd /opt/ayco/dify/docker && docker compose restart api worker web'

# Reiniciar Dashboard
ssh ayco-dify 'systemctl restart streamlit-dashboard'

# Reiniciar Agent Tools
ssh ayco-dify 'systemctl restart ayco-tools'
# Verificar: ssh ayco-dify 'curl -s http://localhost:8400/health'
```

---

# Apéndice: Contexto AYCO

AYCO es una empresa del ecosistema **Grupo Salinas** (TV Azteca, Elektra, Banco Azteca, Total Play, Italika). Opera crédito y cobranza en México: ~5,000 transacciones/mes, exposición $2.1B MXN. Migrando de on-premise legacy a Huawei Cloud bajo regulación CNBV.

---

*Documento preparado el 13 de mayo de 2026. Versión 1.1. CONFIDENCIAL — Huawei Cloud LATAM.*
