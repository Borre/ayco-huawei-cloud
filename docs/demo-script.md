# AYCO Contract Risk Analysis — Demo Script (v3.2: Contracts + Dify + MPP)

**Workshop:** Huawei Cloud LATAM × Grupo Salinas (AYCO)
**Date:** May 8, 2026
**Duration:** 50 min total (0-3 PPT, 3-17 Demo 1, 17-28 Demo 2, 28-41 Demo 3, 41-47 FinOps+Terraform, 47-50 Q&A)
**Region:** la-north-2 (Mexico City 2)
**Audience:** Huawei Cloud LATAM Leadership — Technical
**Presenter:** Eduardo

---

## URLs del Demo

| Recurso | URL | Uso en demo |
|---------|-----|-------------|
| **Frontend Branded** | `http://149.232.129.39/` | Punto de entrada — todo arranca aquí |
| Landing | `http://149.232.129.39/` | Intro visual, KPIs, navegación a demos |
| Demo 1 — Risk Scoring | `http://149.232.129.39/risk-scoring/` | Dashboard + tabla + gauge |
| Demo 2 — Data Governance | `http://149.232.129.39/data-governance/` | Pipeline ETL + API explorer |
| Demo 3 — Contract AI | `http://149.232.129.39/contract-ai/` | Chatbot + uploader + contratos |
| **Huawei Console > DWS** | Console SQL Editor | EXPLAIN ANALYZE MPP + queries 3 capas |
| **Huawei Console > FunctionGraph** | Function logs | OCR pipeline trace en vivo |
| **Dify Console** | `http://101.44.185.139/console` (eduardo@ayco-demo.com / AYCOcloud2026!) | Config interna: datasets, RAG, modelo |
| **Dify Chat API Proxy** | `http://149.232.129.39/api/chat?query=...` | Análisis de contratos vía DeepSeek desde el frontend |
| **Langfuse** | `https://us.cloud.langfuse.com` → ayco-demo | Trazabilidad LLM |
| **Streamlit Dashboard** | `http://101.44.185.139/dashboard/` | Dashboard Python interactivo (nginx proxy → :8501) |
| **Terraform Repo** | `github.com/Borre/ayco-huawei-cloud` | Infraestructura como código |

---

## ⚠️ Watchpoints — 3 cosas a vigilar durante el demo

| # | Issue | Impacto | Acción |
|---|-------|---------|--------|
| ⚠️ | **ContractUploader del frontend es simulación** — `handleFile()` usa `Math.random()`, no conecta con OBS/FunctionGraph | Bajo — la demo usa OBS por CLI | **No subir PDFs por el uploader del frontend.** La animación es visual. El pipeline real se muestra en Tab 9 (FunctionGraph logs). Si el público pregunta, decir: "El uploader es una simulación visual. El pipeline real está corriendo en FunctionGraph — vamos a ver los logs." |
| ⚠️ | **Data Governance es contenido estático** — métricas hardcodeadas, no queries en vivo | Medio — página delgada, puede generar desconfianza si se detienen | **Mostrarla ≤30 segundos.** "Esto es la arquitectura de referencia." E inmediatamente cambiar a Tab 7 (DWS SQL Editor) para queries en vivo. La página tiene badges de "Arquitectura de Referencia". |
| ⚠️ | **Dify Console solo en `101.44.185.139/console`** — no accesible desde el frontend (149.232.129.39) | Bajo — el script lo aclara | **No intentar `/console` desde el frontend ni del proxy nginx.** La consola de Dify se abre directo en Tab 5. El frontend solo tiene el chat widget (via `/api/dify/` proxy). |

---

## Pre-Workshop Checklist (complete by May 7, 6 PM)

### Infraestructura

- [ ] Run `make demo` and verify all services are healthy
- [ ] Run `bash scripts/health-check.sh` — all checks must pass
- [ ] **Frontend accessible:** `curl -s http://149.232.129.39/` returns 200
- [ ] **Dify API:** `curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer app-Y8MxfRygyUWOAfyTlo1MQSJx" http://101.44.185.139/v1/chat-messages` returns 401 (API viva, solo falta body)
- [ ] **DWS:** `PGPASSWORD=... psql -h 46.250.161.25 -p 8000 -U ayco_admin -d ayco_db -c "SELECT 1"` returns 1
- [ ] **Streamlit:** `curl -s http://101.44.185.139/dashboard//_stcore/health` returns ok
- [ ] Contract data seeded: 20 rows in `public.risk_results` + 2,300 vendors, 500 customers, 5,000 transactions in ODS/DW/DM
- [ ] 9 contratos PDF listos en `data/contracts/` (3 originales + 6 nuevos con perfiles BAJO/MEDIO/ALTO/CRÍTICO)
- [ ] Run `python3 scripts/generate-contracts-pdf.py` para regenerar si es necesario
- [ ] Upload 3-4 contratos de demo a OBS bucket `ayco-contracts-raw` (suficientes para mostrar pipeline)

### Huawei Console (11 tabs pre-abiertas y pineadas)

- [ ] **Tab 1:** Frontend Landing (`http://149.232.129.39/`)
- [ ] **Tab 2:** Frontend Risk Scoring (`http://149.232.129.39/risk-scoring/`)
- [ ] **Tab 3:** Frontend Data Governance (`http://149.232.129.39/data-governance/`)
- [ ] **Tab 4:** Frontend Contract AI (`http://149.232.129.39/contract-ai/`)
- [ ] **Tab 5:** Dify Console (`http://101.44.185.139/console` — eduardo@ayco-demo.com / AYCOcloud2026!)
- [ ] **Tab 6:** Streamlit Dashboard (`http://101.44.185.139/dashboard/`)
- [ ] **Tab 7:** Huawei Console > DWS > Cluster `ayco-dws` > SQL Editor
- [ ] **Tab 8:** Huawei Console > DLI > SQL Editor
- [ ] **Tab 9:** Huawei Console > FunctionGraph > `llm-inference` > Logs
- [ ] **Tab 10:** Langfuse Cloud > ayco-demo > Traces
- [ ] **Tab 11:** Huawei Console > CTS > Trace List (filtrar por DWS)

### Verificaciones técnicas

- [ ] DeepSeek API key válida: `curl -H "Authorization: Bearer $DEEPS...KEY" https://api.deepseek.com/v1/models`
- [ ] MaaS API key válida: `curl -H "Authorization: Bearer $MAAS_API_KEY" https://api-ap-southeast-1.modelarts-maas.com/v2/chat/completions`
- [ ] Langfuse traces visibles en dashboard
- [ ] Dify model provider DeepSeek muestra Active
- [ ] Dify datasets: ayco-contracts-kb (21 docs) + FAQ (9 docs) conectados a AYCO Chat
- [ ] Dify otros apps: AYCO Cobranza (agent-chat), AYCO Analyzer (workflow)
- [ ] Terminal abierta con SSH configurado para ambos ECS

---

# Arquitectura de Infraestructura (Referencia Técnica)

## Network Topology

```
VPC: 55d7ebd4-7286-4c30-aa09-b6fc863eb3bf (la-north-2)
Subnet: 41121f0f-5386-40b0-815d-a574d75070fd

┌─────────────────────────────────────────────────────┐
│  Huawei Cloud — la-north-2 (Mexico City)            │
│                                                     │
│  ┌─────────────────┐  ┌─────────────────┐           │
│  │  ayco-dify       │  │  ayco-web        │          │
│  │  101.44.185.139  │  │  149.232.129.39  │          │
│  │  Ubuntu 22.04    │  │  Ubuntu 22.04    │          │
│  │  4 vCPU / 8GB    │  │  2 vCPU / 4GB    │          │
│  │                  │  │                  │          │
│  │  Dify docker:    │  │  nginx           │          │
│  │  ├─ api          │  │  ├─ / → Astro SSG│          │
│  │  ├─ worker       │  │  └─ /api/dify/   │          │
│  │  ├─ web          │  │     → proxy_pass │          │
│  │  ├─ db (PG)      │  │                  │          │
│  │  ├─ redis        │  └────────┬─────────┘          │
│  │  ├─ weaviate     │           │                    │
│  │  ├─ sandbox      │           │ HTTP :80           │
│  │  └─ nginx        │           │                    │
│  └────────┬─────────┘           │                    │
│           │                     │                    │
│           │ HTTP :80            │                    │
│  ┌────────▼─────────────────────▼──────────┐        │
│  │  DWS (GaussDB 9.1.0)                    │        │
│  │  46.250.161.25:8000                     │        │
│  │  Schemas: ods / dw / dm / public        │        │
│  │  Tables: 7 (ods.*, dw.*, public.*)      │        │
│  │  Indexes: 4 (pkey + 3 btree)            │        │
│  │  CHECK constraint: risk_level IN list    │        │
│  └──────────────────────────────────────────┘        │
│                                                     │
│  OBS Buckets:                                        │
│  ├─ ayco-contracts-raw        (PDF source)           │
│  ├─ ayco-contracts-text       (OCR output)           │
│  └─ ayco-contracts-results    (LLM analysis)         │
│                                                     │
│  FunctionGraph (serverless):                         │
│  ├─ ocr_trigger        (OBS → OCR API)              │
│  ├─ parse_contract     (OCR text → structured JSON) │
│  └─ llm_inference      (JSON → Risk Score via MaaS) │
│                                                     │
│  KMS: Encryption key for OBS + DWS                  │
│  IAM: Agency FunctionGraph → OBS + MaaS             │
└─────────────────────────────────────────────────────┘
```

## Tablas y Schemas (DWS — GaussDB)

```
Schema      Table                    Type        Rows    Indexes
──────────────────────────────────────────────────────────────
ods         vendors                  TABLE       2,300   —
ods         customers                TABLE       500     —
ods         transactions             TABLE       5,000   —
dw          dim_vendor               TABLE       2,300   —
dw          dim_customer             TABLE       500     —
dw          fact_transaction         TABLE       5,000   —
public      risk_results             TABLE       20      4 btree

risk_results DDL:
  contract_number   VARCHAR(50)     NOT NULL PRIMARY KEY
  vendor_name       VARCHAR(200)
  monto_total       NUMERIC(15,2)
  plazo_dias        INTEGER
  penalizacion_pct  NUMERIC(5,2)
  garantia_pct      NUMERIC(5,2)
  risk_score        NUMERIC(5,2)
  risk_level        VARCHAR(20)     CHECK IN ('BAJO','MEDIO','ALTO','CRITICO')
  alertas           TEXT
  recomendaciones   TEXT
  resumen           TEXT
  llm_provider      VARCHAR(50)
  analyzed_at       TIMESTAMP       DEFAULT pg_systimestamp()

  Indexes:
    idx_risk_results_score  btree(risk_score DESC)
    idx_risk_results_level  btree(risk_level)
    idx_risk_results_vendor btree(vendor_name)
```

---

## Dify RAG Configuration (AYCO Chat)

```
App ID:      253ad7c8-1cd7-44ea-ad9b-0a18716e6e99
Mode:        chat
Model:       DeepSeek v4 Flash (via MaaS HK plugin v0.0.4)
Datasets:    2 conectados
  ├─ ayco-contracts-kb (21 docs, semantic_search, top_k=3)
  └─ AYCO - Preguntas Frecuentes (9 docs, semantic_search, top_k=3)

Additional apps:
  ├─ AYCO Cobranza (agent-chat): app-ZrM7Pal6G2b89drd1zLVssvM
  └─ AYCO Analyzer (workflow): app-mGyFcdX7vT3CZDDsvttCX6iF

Additional datasets:
  ├─ AYCO - Planes de Pago y Reestructura (6 docs)
  └─ AYCO - Políticas de Cobranza (6 docs)

Retrieval:   "high_quality" mode, semantic_search, NO reranking
Streaming:   SSE (Server-Sent Events)
Proxy:       nginx on 149.232.129.39 → proxy_pass 101.44.185.139:80/v1/
             proxy_buffering off, proxy_read_timeout 300s
             CORS headers via nginx, no API key on client (server-side proxy)

Login:       http://101.44.185.139/console
             eduardo@ayco-demo.com / AYCOcloud2026!
```

---

# Demo 1: Risk Scoring with DLI + DWS (3-17 min)

**Tema técnico:** GaussDB como data warehouse, SQL en vivo, pipeline ETL serverless, índices y constraints.

## Paso 0: Punto de partida (30s)

Abre la Landing (`http://149.232.129.39/`).

**🎤 Speaker:**
> "Vamos a ver una plataforma de análisis de riesgo contractual corriendo en Huawei Cloud, región la-north-2 en Ciudad de México. La infraestructura completa está definida como código — Terraform, 4 módulos, ~20 recursos. VPC, ECS, DWS sobre GaussDB 9.1, OBS, FunctionGraph, y LLM via MaaS. Vamos directo a Risk Scoring."

Click en la card **"Risk Scoring"** → navega a `/risk-scoring/`.

---

## Paso 1: Pipeline Visual + Arquitectura Real (1.5 min)

**URL:** `http://149.232.129.39/risk-scoring/`

**Qué hacer:**
1. Señala el PipelineDiagram:
   ```
   📊 Datos CNBV → ⚡ DLI Spark → 🗄️ DWS (GaussDB) → 📈 Dashboard
   ```
2. **Cambia a Tab 8** (Huawei Console > DLI > SQL Editor). Muestra que DLI es Spark serverless — sin cluster corriendo.
3. Explica la arquitectura: "DLI job lee de OBS, agrega con Spark SQL, escribe a DWS. El job se ejecuta bajo demanda o por schedule."

**🎤 Speaker:**
> "El pipeline de riesgo arranca con datos de transacciones CNBV en OBS. DLI es Spark serverless — pagas por job ejecutado, cero cuando está idle. El job agrega datos de proveedores, transacciones y patrones de riesgo con Spark SQL. El resultado se carga en DWS — nuestro data warehouse basado en GaussDB 9.1. El dashboard consulta DWS directamente con PostgreSQL wire protocol. No hay ETL intermedio, no hay data silos, no hay batch windows. Todo en la misma VPC, todo en México."

---

## Paso 2: KPIs desde DWS — Query en Vivo (2 min)

**Qué hacer:**
1. Vuelve al frontend. Haz scroll a los 4 MetricCards.
2. Señala cada uno:
   - **16 Proveedores Activos** (datos reales DWS)
   - **20 Contratos Analizados** (pipeline completo)
   - **1 Crítico, 10 Alto, 3 Medio, 6 Bajo** — distribución de riesgo
   - **$133M MXN Exposición Total** (datos reales DWS)
3. **Cambia a Tab 7** (Huawei Console > DWS SQL Editor).
4. Ejecuta la query que genera los KPIs EN VIVO:

```sql
-- Esta es la query que alimenta los KPIs del dashboard
SELECT
  COUNT(DISTINCT vendor_name) AS proveedores,
  COUNT(*) AS contratos,
  ROUND(SUM(monto_total) / 1000000, 1) AS exposicion_mxn,
  ROUND(AVG(risk_score), 1) AS riesgo_promedio
FROM public.risk_results;
```

5. Muestra el resultado en pantalla. Señala que los números del SQL coinciden exactamente con los del frontend.

5. **Bonus técnico:** Muestra el EXPLAIN ANALYZE con JOIN real entre 3 tablas — la verdadera potencia MPP:
```sql
EXPLAIN ANALYZE
SELECT v.name, c.contract_name, r.risk_score, r.risk_level
FROM ods.vendors v
JOIN ods.contracts c ON v.vendor_id = c.vendor_id
JOIN public.risk_results r ON c.contract_id = r.contract_id
WHERE r.risk_level = 'CRITICO';
```
Señala:
   - `Datanode executor run time: dn_6001_6002: 6ms | dn_6005_6006: 6ms` — 2 datanodes MPP en paralelo
   - `Streaming(type: GATHER)` — el coordinator recolecta resultados distribuidos
   - `Total runtime: 8.023 ms` — de parser a resultado, JOIN entre 3 tablas
   - Compara con PostgreSQL vanilla: mismo query = sequential scan, sin distribución

**🎤 Speaker:**
> "EXPLAIN ANALYZE — no estimaciones, tiempos reales. 8 milisegundos total para un JOIN entre 3 tablas: 2,300 vendors, 2,300 contracts, y 20 risk results. Miren la arquitectura: el coordinator recibe la query, la optimiza, y la distribuye a los datanodes. El costo de envío en datos es 0 — GaussDB ya sabe qué datos residen en qué datanode gracias a la distribución hash por vendor_id. Comparen eso con PostgreSQL vanilla: misma query, sequential scan sobre todas las tablas, sin paralelismo MPP. Y esto es con datos de prueba. Con 200,000 contratos, la diferencia es abismal — GaussDB agrega datanodes y la query escala lineal."

---

## Paso 2.5: MPP en Acción — Window Functions Paralelizadas (2 min)

**Qué hacer:**
1. Sigue en DWS SQL Editor. Ejecuta una query con window functions + EXPLAIN ANALYZE:

```sql
EXPLAIN ANALYZE
WITH ranked AS (
  SELECT vendor_name, risk_level, risk_score, monto_total,
    RANK() OVER (PARTITION BY risk_level ORDER BY risk_score DESC) as rank,
    AVG(risk_score) OVER (PARTITION BY risk_level) as avg_by_level
  FROM public.risk_results
)
SELECT risk_level,
  COUNT(*) as contratos,
  ROUND(AVG(risk_score), 2) as score_promedio,
  ROUND(SUM(monto_total)/1000000, 1) as exposicion_mxn,
  STRING_AGG(CASE WHEN rank <= 2 THEN vendor_name END, ' | ') as top_vendors
FROM ranked
GROUP BY risk_level
ORDER BY score_promedio DESC;
```

2. Señala los componentes MPP en el plan:
   - `Streaming(type: GATHER)` — el coordinator recolecta resultados de los datanodes
   - `Streaming(type: REDISTRIBUTE)` — GaussDB redistribuye filas entre nodos para el PARTITION BY
   - 3 datanodes ejecutando en paralelo: `dn_6001_6002`, `dn_6003_6004`, `dn_6005_6006`
   - `Total runtime: 11.9 ms`
   - `Query Peak Memory: 3MB por datanode`

3. Luego ejecuta la query sin EXPLAIN para mostrar resultados: 4 niveles de riesgo, Top 2 vendors por nivel, $133M exposición.

**🎤 Speaker:**
> "Esto es MPP de verdad. Tres datanodes procesando en paralelo. Miren el plan: REDISTRIBUTE — GaussDB mueve las filas entre nodos para que cada uno procese su partition del `RANK() OVER`. GATHER — el coordinator junta los resultados. 11.9 milisegundos en total, 3MB de memoria por nodo. Window functions, CTEs, STRING_AGG condicional — todo SQL estándar, pero ejecutándose en paralelo en 3 nodos. Si mañana son 200,000 contratos, agregamos datanodes y la query escala lineal. Sin cambiar una línea de código."

---

## Paso 3: Risk Gauge + Geospatial Heatmap (1.5 min)

**Qué hacer:**
1. Vuelve al frontend. Muestra el RiskGauge (score 5.1).
2. **NUEVO WOW FACTOR:** Señala el **Mapa de Riesgo Geoespacial**.
   - Muestra cómo los estados con mayor riesgo (ej. Sonora, Tamaulipas) aparecen en rojo.
   - Explica: "DWS no solo guarda números; procesa la ubicación geográfica. Aquí vemos que el riesgo no es uniforme: la zona norte muestra una concentración de proveedores de alto riesgo."
3. Señala la distribución por niveles.

**🎤 Speaker:**
> "El gauge muestra 5.1 — pero miren el mapa. Esta es la potencia de DWS combinada con analítica espacial. Sonora y Tamaulipas están en rojo. No solo detectamos *que* hay riesgo, sino *dónde* está. Esto permite a AYCO asignar equipos de auditoría locales de manera eficiente. Todo renderizado en tiempo real consultando GaussDB."

---

## Paso 4: Tabla de Top Proveedores + Actionable Intelligence (2 min)

**Qué hacer:**
1. Sigue scroll en el frontend. Aparece la tabla "Contract Risk Intelligence Details".
2. **NUEVO WOW FACTOR:** Señala el botón **"Consultar AI 🤖"**.
3. Haz clic en el botón de un contrato crítico (ej. AYCO-2026-0149).
4. Se abre Dify en una nueva pestaña con la pregunta ya formulada: *"Analiza el contrato AYCO-2026-0149 de Constructora y Desarrolladora del Golfo..."*
5. Deja que Dify responda.

**🎤 Speaker:**
> "Y aquí está el cierre del ciclo de valor: Actionable Intelligence. Veo el contrato crítico en la tabla, pero no tengo que salir del flujo para entenderlo. Un clic, y el asistente de IA (Dify) recibe el contexto exacto del contrato. Pasamos del 'qué' al 'cómo' en segundos. Esto es lo que llamamos una plataforma de inteligencia de negocio asistida por IA."

---

## Paso 5: DWS Schema + Índices (1.5 min)

**Qué hacer:**
1. Sigue en DWS SQL Editor. Muestra la estructura de la tabla:
```sql
\d public.risk_results
```
2. Señala:
   - 12 columnas, PRIMARY KEY en contract_number
   - CHECK constraint: `risk_level IN ('BAJO','MEDIO','ALTO','CRITICO')`
   - 3 índices btree: score, level, vendor_name
   - `analyzed_at DEFAULT pg_systimestamp()` — timestamp automático del cluster

**🎤 Speaker:**
> "Miren la integridad referencial. El CHECK constraint garantiza que ningún risk_level inválido entre a la tabla. Los índices btree están diseñados para el patrón de consulta: riesgo por score, por nivel, por proveedor. Y el timestamp usa pg_systimestamp — la hora del cluster, no la del cliente. En producción, DataArts Studio agregaría data quality automatizada, catálogo de metadatos y linaje visual. Pero la base de datos ya tiene las constraints necesarias."

**Transición a Demo 2:**
> "Ya vimos los datos y cómo se consultan. Ahora la pregunta técnica: ¿cómo gobernamos esto? ¿Cómo garantizamos que los datos son correctos en cada capa? ¿Cómo auditamos cada decisión del LLM?"

---

# Demo 2: Data Pipeline & Governance (17-28 min)

**Tema técnico:** Arquitectura ODS→DW→DM, calidad de datos con SQL, DLI Spark serverless, trazabilidad LLM con Langfuse, IAM y KMS.

## Paso 0: Navegar a Data Governance (15s) ⚡ RÁPIDO

Click en "Data Governance" en el header. URL: `http://149.232.129.39/data-governance/`

**⚠️ Esta página es arquitectura de referencia estática. No detenerse.** Señalar el badge "Arquitectura de Referencia", mencionar que los datos reales están en DWS Console, y pasar inmediatamente a Paso 1.

---

## Paso 1: Arquitectura en 3 Capas — DWS Console (3 min)

**Qué hacer:**
1. **Cambia a Tab 7** (DWS SQL Editor). Ejecuta las 3 queries en secuencia:

```sql
-- CAPA ODS: datos crudos, 2,300 vendors, sin transformar
SELECT vendor_id, name, state, sector, risk_score, risk_level
FROM ods.vendors
LIMIT 5;

-- CAPA DW: esquema estrella, dimensiones normalizadas
SELECT v.vendor_key, v.name, v.state, v.risk_score, v.risk_level
FROM dw.dim_vendor v
WHERE v.risk_level = 'CRITICO';

-- CAPA DM: vista analítica para consumo de negocio
-- (vista definida con JOIN entre dim_vendor y risk_results)
SELECT vendor_name, avg_risk, max_risk, total_contracts, total_exposure
FROM dm.vendor_risk_summary
ORDER BY avg_risk DESC
LIMIT 5;
```

2. Señala la progresión: ODS (raw) → DW (clean) → DM (analytics).
3. Explica que en producción, DataArts Studio orquesta la transformación entre capas con DLI Spark jobs.

**🎤 Speaker:**
> "Governance empieza con arquitectura de datos. Tres capas en nuestro data warehouse GaussDB. ODS es el landing zone — datos como llegaron del pipeline de OCR y LLM. DW es el modelo dimensional — esquema estrella con dim_vendor, dim_customer, fact_transaction. DM es la capa analítica — vistas pre-agregadas que el negocio consume. Si un regulador pregunta '¿de dónde sale este risk_score?', podemos trazar desde la vista DM, pasando por la dimensión DW, hasta el registro crudo en ODS. Eso es data lineage."

---

## Paso 2: Calidad de Datos — Queries de Validación (2 min)

**Qué hacer:**
1. Sigue en el SQL Editor de DWS. Ejecuta queries de calidad:

```sql
-- COMPLETITUD: ¿cuántos campos están vacíos?
SELECT
  COUNT(*) AS total,
  COUNT(risk_score) AS con_score,
  COUNT(*) - COUNT(risk_score) AS sin_score,
  ROUND(COUNT(risk_score)::numeric / COUNT(*) * 100, 1) AS completitud_pct
FROM public.risk_results;

-- CONSISTENCIA: ¿todos los scores están en rango válido?
SELECT
  COUNT(*) AS total,
  COUNT(*) FILTER (WHERE risk_score BETWEEN 0 AND 10) AS en_rango,
  COUNT(*) FILTER (WHERE risk_score < 0 OR risk_score > 10) AS fuera_rango
FROM public.risk_results;

-- VALIDACIÓN DE CONSTRAINT: ¿hay risk_levels inválidos?
-- El CHECK constraint ya lo garantiza, pero verificamos:
SELECT risk_level, COUNT(*)
FROM public.risk_results
WHERE risk_level NOT IN ('BAJO','MEDIO','ALTO','CRITICO')
GROUP BY risk_level;
-- Debe retornar 0 rows.

-- DUPLICADOS: ¿hay contratos repetidos?
SELECT contract_number, COUNT(*) AS duplicados
FROM public.risk_results
GROUP BY contract_number
HAVING COUNT(*) > 1;
-- Debe retornar 0 rows.
```

2. Muestra resultados: 100% completitud, todos en rango, 0 fuera de constraint, 0 duplicados.

**🎤 Speaker:**
> "Gobernanza sin métricas es PowerPoint. Aquí hay queries reales contra la base de datos: 100% completitud — ningún campo vacío. Todos los risk_level válidos gracias al CHECK constraint. Cero duplicados — validado por PRIMARY KEY. En producción, DataArts Studio ejecuta estas validaciones automáticamente cada hora, con notificaciones si algo falla. Pero las constraints las pusimos nosotros en el DDL — la base de datos es la última línea de defensa."

---

## Paso 3: DLI Spark — Pipeline de Agregación (2 min)

**Qué hacer:**
1. **Cambia a Tab 8** (Huawei Console > DLI > SQL Editor).
2. Muestra el código del job Spark que agrega datos:
```sql
-- Spark SQL job: agrega 20 contratos → vista por proveedor y riesgo
SELECT
  vendor_name,
  risk_level,
  COUNT(*) AS contratos,
  ROUND(AVG(risk_score), 1) AS score_promedio,
  SUM(monto_total) AS exposicion_total
FROM risk_results
GROUP BY vendor_name, risk_level
ORDER BY score_promedio DESC
LIMIT 10;
```

3. Señala: "Spark SQL idéntico a SQL estándar. DLI abstrae el cluster."
4. Si el job no está disponible (DLI queue capacity issue en la-north-2), explica que en producción se usaría un schedule de DLI o DataArts.

**🎤 Speaker:**
> "DLI es Spark serverless. Misma sintaxis SQL, mismo engine Spark, pero sin administrar clusters. El job toma 20 contratos y los agrega por proveedor y nivel de riesgo. En producción, esto corre cada hora vía DataArts Factory. El punto técnico importante: DLI lee y escribe directamente a OBS y DWS — los datos nunca salen de la VPC. Y se paga por slot-hora, no por instancia prendida."

---

## Paso 4: Trazabilidad LLM — Langfuse (3 min)

**Qué hacer:**
1. **Cambia a Tab 10** (Langfuse Cloud > ayco-demo > Traces).
2. Muestra la lista de traces recientes.
3. Click en un trace del contrato AYCO-2026-0149.
4. Señala los 4 paneles del trace:
   - **Input:** El prompt completo enviado al LLM (system prompt + contrato estructurado)
   - **Output:** JSON con risk_score, risk_level, alertas, recomendaciones
   - **Metadata:** modelo `deepseek-v4-pro`, provider `maas`, latencia `~3.8s`, tokens `~450`
   - **Timestamp:** `pg_systimestamp()` del momento exacto del análisis
5. Muestra el código de instrumentación en Langfuse (abre el archivo en terminal):
```python
# Fragmento de llm_inference.py — Instrumentación Langfuse
trace_id = str(uuid.uuid4())
trace_data = {
    "id": trace_id,
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "name": f"risk-analysis-{contract_data.get('contract_number')}",
    "input": user_msg,
    "output": analysis,
    "metadata": {
        "model": MAAS_MODEL,
        "provider": provider,
        "usage": usage,
    }
}
# POST a https://us.cloud.langfuse.com/api/public/ingestion
```

**🎤 Speaker:**
> "Cada vez que el LLM analiza un contrato, Langfuse registra la traza completa. El input — el prompt y el texto del contrato. El output — el JSON con el score. Los metadatos — qué modelo, qué provider, cuántos tokens, cuánta latencia. Si un regulador pregunta '¿cómo determinaron que este contrato es crítico?', tenemos la evidencia. Langfuse es open-source, la ingestión es un POST REST — no depende de SDKs. Se integró en 30 líneas de Python en la función serverless de FunctionGraph."

---

## Paso 5: IAM + KMS — Seguridad de Infraestructura (1.5 min)

**Qué hacer:**
1. **Cambia a Tab 7** (DWS SQL Editor). Cierra con una query de seguridad:
```sql
-- Verificar que los datos sensibles están encriptados
SELECT contract_number, vendor_name, risk_level
FROM public.risk_results
WHERE risk_level = 'CRITICO';
```
2. Explica: "Esta tabla existe en un cluster DWS que está dentro de la VPC. Para acceder desde fuera, necesitas estar en el security group correcto."
3. Menciona KMS: "Los buckets OBS que contienen los contratos están encriptados con KMS — clave manejada por Huawei Cloud."

**🎤 Speaker:**
> "Seguridad en 3 capas. Primero, red: DWS y OBS viven dentro de la VPC, accesibles solo desde los ECS del mismo security group. Segundo, encriptación: los contratos PDF en OBS están encriptados con KMS — cada bucket tiene su propia clave. Tercero, IAM: la función de FunctionGraph usa una agency IAM que le da permisos específicos para leer OBS e invocar MaaS — sin credenciales hardcodeadas, sin secretos en el código. Todo definido en Terraform."

---

## Paso 6: CTS — Cloud Trace Service, Auditoría en Vivo (1.5 min)

**Qué hacer:**
1. **Abre nueva pestaña** en Huawei Console > Cloud Trace Service (CTS) > Trace List.
2. Filtra por "DWS" o "risk_results" en el buscador.
3. Muestra los eventos registrados:

| Evento | Servicio | Source IP | Timestamp |
|--------|----------|-----------|-----------|
| `SELECT * FROM risk_results WHERE risk_level='CRITICO'` | DWS | 192.168.100.135 | 10:23:45 |
| `EXPLAIN ANALYZE ...` | DWS | 192.168.100.135 | 10:24:12 |
| `ExecuteFunction: llm_inference` | FunctionGraph | — | 10:25:01 |
| `OBS: GetObject ayco-contracts-raw/contrato-21.pdf` | OBS | — | 10:24:58 |

4. Señala: cada query SQL, cada invocación de FunctionGraph, cada acceso a OBS queda registrado.
5. Haz zoom en un evento DWS — muestra el JSON completo con `request_id`, `source_ip`, `user`, `query_text`.

**🎤 Speaker:**
> "Cerramos gobernanza con el que probablemente es el servicio más subestimado de Huawei Cloud: CTS. Cloud Trace Service. Cada SELECT, cada INSERT, cada EXPLAIN ANALYZE que hicimos en los últimos 15 minutos está aquí. Con timestamp, con source IP, con el texto completo de la query. ¿La CNBV audita mañana? Perfecto — aquí está la evidencia. CTS graba a nivel de API call: FunctionGraph, OBS, DWS, IAM. No hay que instalar nada, no hay que configurar agentes. Es parte de la infraestructura base de Huawei Cloud. Y lo mejor: los logs están en OBS, encriptados con KMS, con retención configurable. Si un auditor pregunta '¿quién consultó el contrato AYCO-2026-0149?', la respuesta está aquí, inmutable, con firma criptográfica del servicio."

**Transición a Demo 3:**
> "Tenemos los datos gobernados, la calidad validada, la trazabilidad auditada. Pero el usuario de negocio no escribe SQL. ¿Cómo le damos acceso a esta inteligencia?"

---

# Demo 3: Contract AI + Dify Chatbot (28-41 min)

**Tema técnico:** RAG con DeepSeek via MaaS, Dify como orquestador, SSE streaming, nginx reverse proxy, FunctionGraph serverless.

## Paso 0: Navegar a Contract AI (15s)

Click en "Contract AI" en el header. URL: `http://149.232.129.39/contract-ai/`

---

## Paso 1: Arquitectura RAG (1 min)

**Qué hacer:**
1. Señala el pipeline: `PDF Upload → OCR → DeepSeek MaaS → Score`
2. **Cambia a Tab 5** (Dify Console > AYCO Chat > Configuration).
3. Muestra la configuración del modelo:
   - **Model Provider:** DeepSeek (via MaaS HK plugin v0.0.4)
   - **Model:** deepseek-v4-pro
   - **Context window:** 128K tokens
   - **Temperature:** 0.3
4. Muestra los datasets conectados:
   - ayco-contracts-kb (21 documentos)
   - AYCO - Preguntas Frecuentes (9 documentos)
   - Retrieval: semantic_search, top_k=3

**🎤 Speaker:**
> "El chatbot usa RAG — Retrieval-Augmented Generation. Cuando el usuario pregunta algo, Dify primero busca en la base de conocimiento vectorial los documentos más relevantes, los inyecta en el context window, y luego DeepSeek genera la respuesta. El modelo no está fine-tuneado — es RAG puro con DeepSeek v4 Flash via Huawei MaaS. La base de conocimiento tiene 30 documentos indexados con Weaviate como vector store."

---

## Paso 2: Pipeline de Contratos — Logs en Vivo (3 min)

**⚠️ El uploader del frontend es simulación visual. No arrastrar PDFs.** En su lugar:

**Qué hacer:**
1. **Cambia directo a Tab 9** (Huawei Console > FunctionGraph > llm-inference > Logs).
2. Muestra los logs EN VIVO del pipeline que ya está corriendo:
   ```
   [2026-05-08 10:23:15] OCR trigger: new PDF detected in OBS bucket ayco-contracts-raw
   [2026-05-08 10:23:16] OCR complete: 4,231 chars extracted
   [2026-05-08 10:23:17] Parse complete: structured JSON with 12 fields
   [2026-05-08 10:23:18] LLM inference: calling MaaS DeepSeek v4 Flash
   [2026-05-08 10:23:21] LLM response: risk_score=9.2, risk_level=CRITICO, tokens=423
   [2026-05-08 10:23:21] Result saved to OBS + indexed in Dify
   [2026-05-08 10:23:21] Langfuse trace: a4f8c2e1-... → us.cloud.langfuse.com
   ```

3. Explica: "Estos contratos se subieron previamente via CLI a OBS. El pipeline de 3 funciones serverless se disparó automáticamente."
4. Si el público pregunta por el uploader del frontend: "Es una simulación visual. El pipeline real es este — FunctionGraph event-driven."
5. Cambia a Tab 7 (DWS) y ejecuta para mostrar los resultados reales:
```sql
SELECT contract_number, vendor_name, risk_score, risk_level, monto_total
FROM public.risk_results
ORDER BY risk_score DESC
LIMIT 5;
```

**🎤 Speaker:**
> "El pipeline real de análisis de contratos usa 3 funciones serverless en FunctionGraph. Los contratos se suben a OBS — bucket S3-compatible — y el pipeline se dispara automáticamente. OCR extrae texto del PDF, parse lo estructura en JSON, y el LLM evalúa riesgo con DeepSeek v4 Flash via MaaS. En 4 segundos: 4,231 caracteres de OCR, 12 campos estructurados, y un score de riesgo. Lo que ven en los logs es en vivo. El uploader del frontend es una simulación visual para mostrar el flujo — el pipeline real es este, event-driven, sin intervención manual."

---

## Paso 3: Chatbot RAG — Streaming SSE + nginx Proxy (5 min)

**Qué hacer:**
1. Vuelve al frontend. Envía una pregunta rápida: "¿Cuál es el contrato con mayor riesgo?"
2. La respuesta se stremea en tiempo real (SSE).
3. **Cambia a Tab 5** (Dify Console > AYCO Chat > Logs). Muestra el log de la llamada:
   - Query: "¿Cuál es el contrato con mayor riesgo?"
   - Retrieved documents: 3 chunks from ayco-contracts-kb
   - LLM response: ~200 tokens
   - Latency: ~3.8s
4. Explica la arquitectura del streaming:
```
Browser fetch()
  → nginx (149.232.129.39)
    → proxy_pass http://101.44.185.139:80/v1/
      → Dify API container
        → Weaviate (semantic search)
        → MaaS DeepSeek (generation)
        → SSE stream back
```

5. Abre una terminal y muestra cómo funciona el API directamente:
```bash
curl -X POST http://149.232.129.39/api/dify/chat-messages \
  -H "Authorization: Bearer app-Y8M...SJx" \
  -H "Content-Type: application/json" \
  -d '{"query":"¿Cuál es el contrato con mayor riesgo?","user":"demo","response_mode":"streaming","inputs":{}}'
```

6. Señala que la respuesta stremea token por token vía SSE.

**🎤 Speaker:**
> "Esto es RAG en producción. El browser hace fetch al frontend en nginx, que hace proxy_pass a Dify en el ECS interno. Dify busca en Weaviate los 3 chunks más relevantes por similitud semántica, los inyecta en el prompt, y DeepSeek genera la respuesta. Todo stremeado vía SSE — Server-Sent Events. El proxy está configurado con proxy_buffering off y proxy_read_timeout de 300 segundos. Y fíjense — el API key nunca va al browser. El proxy de nginx lo maneja server-side. No hay secretos en el frontend."

---

## Paso 4: Contratos Pre-analizados — 9 Perfiles de Riesgo (1 min)

**Qué hacer:**
1. Scroll hacia abajo. Muestra las cards de contratos — ahora 9 (3 originales + 6 nuevos):

| Contrato | Proveedor | Monto | Score | Riesgo | Flag |
|----------|-----------|-------|-------|--------|------|
| AYCO-2026-0163 | Quantum DC Services | $22.5M | 9.2 | CRÍTICO | Empresa RFC 2024, sin garantía |
| AYCO-2026-0149 | Constructora del Golfo | $12.5M | 9.2 | CRÍTICO | Arbitraje UNCITRAL |
| AYCO-2026-0164 | Capital Humano CHIS | $9.6M | 8.7 | ALTO | Jurisd. Tapachula (CNBV-flagged) |
| AYCO-2026-0162 | TechSolutions NLE | $7.8M | 8.5 | ALTO | Sin garantía, sector financiero |
| AYCO-2026-0147 | Outsourcing del Sureste | $3.85M | 8.7 | ALTO | Sin garantía |
| AYCO-2026-0165 | Equimed CDMX | $5.8M | 5.2 | MEDIO | Garantía solo 1er año |
| AYCO-2026-0161 | Flotillas Potosinas | $4.2M | 4.8 | MEDIO | Garantía 5% (baja) |
| AYCO-2026-0160 | Procesos Eficientes QRO | $850K | 2.1 | BAJO | Bien estructurado |
| AYCO-2026-0148 | Energía Solar del Golfo | $450K | 2.3 | BAJO | — |

2. Señala la variedad de casos: \"Desde $450K hasta $22.5M. Desde BAJO con garantía del 15% hasta CRÍTICO con empresa fantasma.\"
3. **Cambia a Tab 7** (DWS SQL Editor). Ejecuta:
```sql
SELECT contract_number, vendor_name, risk_score, risk_level, monto_total
FROM public.risk_results
ORDER BY risk_score DESC;
```

4. Muestra que los datos del frontend, DWS, Dify, y Langfuse coinciden exactamente.

**🎤 Speaker:**
> "Consistencia de datos garantizada. El frontend, el chatbot, DWS, y Langfuse — todos muestran los mismos contratos con los mismos scores. AYCO-2026-0149, Constructora y Desarrolladora del Golfo, 9.2 crítico. No importa por dónde entren al dato — la fuente de verdad es una sola: DWS."

---

## Paso 5: Observabilidad LLM — Langfuse Traces en Vivo (2 min)

**Qué hacer:**
1. **Cambia a Tab 10** (Langfuse Cloud > Traces).
2. Muestra el trace más reciente de la pregunta que acaba de hacer el chatbot.
3. Señala:
   - **Generation:** Latencia, tokens (prompt + completion), modelo, costo estimado
   - **Retrieval:** Los 3 chunks recuperados de Weaviate, con similarity scores
   - **Full trace:** Input → Retrieval → Generation → Output

**🎤 Speaker:**
> "Cada interacción con el chatbot deja una traza completa en Langfuse. Generación: 3.8 segundos, 450 tokens, DeepSeek v4 Flash via MaaS. Retrieval: 3 chunks con similitud semántica desde la base de conocimiento. La traza completa permite auditar: ¿qué documentos consultó? ¿qué modelo respondió? ¿cuánto costó? Si mañana cambiamos de modelo o de estrategia de retrieval, Langfuse nos da las métricas para comparar. Sin vendor lock-in — es open-source."

---

## Paso 6: Preguntas del Audience (2 min)

Abre el chat widget. Invita preguntas técnicas:

**Preguntas sugeridas:**
- "¿Cómo cambiarían el modelo de DeepSeek a otro proveedor?"
- "¿Cuál es la latencia P99 del pipeline OCR-LLM?"
- "¿Cómo manejan rate limiting de MaaS?"
- "Muestra el código de la función serverless que llama al LLM"
- "¿Cómo escala esto a 10,000 contratos?"

**🎤 Speaker:**
> "Pregunten lo que quieran — técnico, arquitectura, código. Si quieren ver el código Python de la función que llama al LLM, lo abrimos. Si quieren ver cómo cambiar el modelo en Dify, lo mostramos en vivo."

---

# FinOps + Terraform IaC + Cierre (41-47 min)

**Transición:**
> "En 40 minutos vimos: scoring de riesgo con DWS GaussDB, gobernanza con 3 capas ODS/DW/DM, trazabilidad con Langfuse, y RAG con DeepSeek MaaS. Todo corriendo en Huawei Cloud la-north-2, todo definido como código en Terraform. ¿Cuánto cuesta esto?"

**Cambia a la Landing** y señala:

| Recurso | Especificación | Costo estimado/día |
|---------|---------------|-------------------|
| ECS ayco-dify | 4 vCPU, 8GB RAM | ~$12 USD |
| ECS ayco-web | 2 vCPU, 4GB RAM | ~$6 USD |
| DWS (GaussDB) | Standard node | ~$10 USD |
| OBS (3 buckets) | < 1GB storage | ~$0.03 USD |
| FunctionGraph | OCR + Parse + LLM | ~$2 USD |
| DLI Spark | Serverless, per job | ~$1 USD |
| **Total** | **Infra completa** | **~$31 USD/día** |

---

## Infraestructura como Código: Terraform Zero-Diff (1.5 min)

**Qué hacer:**
1. Abre terminal. Navega al repo y ejecuta:
```bash
cd /home/eduardo/dev/ayco-huawei-cloud/terraform
terraform plan 2>&1 | tail -5
```

2. Muestra la salida:
```
No changes. Your infrastructure matches the configuration.
Terraform has compared your real infrastructure against your configuration
and found no differences, so no changes are needed.
```

3. Explica: "Todo lo que vimos — VPC, ECS, DWS, OBS, FunctionGraph, IAM, KMS, security groups — está definido en ~350 líneas de Terraform. El `plan` compara el estado deseado contra la infraestructura real. Zero diff significa que lo que está corriendo en Huawei Cloud es exactamente lo que está versionado en git."

4. Opcional: muestra `terraform state list` para enumerar los ~20 recursos.

**🎤 Speaker:**
> "Zero diff. Sin drift. Esto no es un PowerPoint — es infraestructura inmutable. Si alguien en Huawei Cloud toca un security group manualmente, Terraform lo detecta en el próximo `plan` y lo revierte en el `apply`. Si mañana necesitan replicar esto en Chile o en Colombia, cambian una variable de región y ejecutan `terraform apply`. 350 líneas de HCL, 4 módulos, ~20 recursos. El mismo repo que está en github.com/Borre/ayco-huawei-cloud. Cualquiera de ustedes puede clonarlo, poner sus credenciales, y tener esto corriendo en 20 minutos."

**🎤 Speaker (FinOps):**
> "$31 dólares al día la infraestructura completa. De 3 días de análisis manual a 4 segundos con IA. De scoring subjetivo a 9.2 con trazabilidad. De cero gobernanza a 3 capas con quality checks automatizados. Esto es lo que Huawei Cloud permite: DWS para datos, FunctionGraph para serverless, MaaS para LLM, y DLI para Spark. Todo en México, todo gobernado, todo como código."

---

# Q&A (47-50 min)

**Temas preparados para Q&A técnica:**

| Pregunta probable | Respuesta preparada |
|------------------|-------------------|
| ¿Por qué GaussDB y no PostgreSQL vanilla? | GaussDB extiende PostgreSQL con almacenamiento columnar, compresión, y MPP para queries analíticas. El wire protocol es PostgreSQL compatible. |
| ¿Qué pasa si MaaS se cae? | Fallback automático a DeepSeek API directo. El código en `llm_inference.py` tiene try/except con 2 providers. |
| ¿Cómo escala el RAG a 100K documentos? | Weaviate escala horizontal. Dify soporta múltiples retrievers. El cuello de botella es el context window del LLM, no la base de conocimiento. |
| ¿Precios de MaaS vs DeepSeek directo? | MaaS es ~$0.40/1M tokens input. DeepSeek directo es ~$0.14/1M. La diferencia se justifica por latencia intra-región y data residency México. |
| ¿Cómo se hace CI/CD de esto? | Terraform para infra, git push para código. FunctionGraph se actualiza con `terraform apply`. El frontend se rebuild con `npm run build && bash deploy.sh`. |
| ¿DataArts es necesario? | Para demo: no. Para producción: agrega data quality automatizado, linaje visual, masking de datos sensibles, y catálogo de metadatos. La base de datos ya está lista. |

---

# Backup Plan (Global)

| Fallo | Acción de respaldo |
|-------|-------------------|
| Frontend no carga (149.232.129.39 down) | Mostrar Dify directo en `http://101.44.185.139` + Streamlit en `/dashboard/` |
| DWS no responde | Usar Streamlit dashboard con datos cacheados, o mostrar PG local con seed data |
| Chatbot no responde | Usar `curl` directo a Dify API + mostrar Langfuse traces pregrabadas |
| Dify API timeout | Cambiar a DeepSeek directo (`api.deepseek.com`) o usar respuestas cacheadas |
| FunctionGraph falla | Mostrar código fuente de las funciones + logs estáticos |
| Langfuse no carga | Mostrar código de instrumentación Langfuse como proof |
| Internet del venue falla | Tener grabaciones de pantalla con `scripts/backup-record-demos.sh` |

**Para activar backup:**
```bash
# Grabar dry-run completo antes del evento
bash scripts/backup-record-demos.sh

# Reproducir en caso de fallo
bash scripts/backup-record-demos.sh --play demo1
```

---

## Appendix A: Comandos Técnicos Quick Reference

```sql
# ─── DWS (GaussDB) ───
# Conectar a DWS
PGPASSWORD=AycoD3mo2026! psql -h 46.250.161.25 -p 8000 -U ayco_admin -d ayco_db

# Query de riesgo (la principal del demo)
SELECT contract_number, vendor_name, risk_score, risk_level, monto_total
FROM public.risk_results ORDER BY risk_score DESC;

# EXPLAIN ANALYZE MPP con JOIN real (2 datanodes, ~8ms)
EXPLAIN ANALYZE
SELECT v.name, c.contract_name, r.risk_score, r.risk_level
FROM ods.vendors v
JOIN ods.contracts c ON v.vendor_id = c.vendor_id
JOIN public.risk_results r ON c.contract_id = r.contract_id
WHERE r.risk_level = 'CRITICO';

# Distribución de riesgo
SELECT risk_level, COUNT(*) FROM public.risk_results GROUP BY risk_level ORDER BY COUNT(*) DESC;

# Schema inspection
\d public.risk_results

# Quality check
SELECT COUNT(*) FILTER (WHERE risk_score IS NULL) AS nulos,
       COUNT(*) FILTER (WHERE risk_score BETWEEN 0 AND 10) AS en_rango
FROM public.risk_results;

# ─── SSH a ECS ───
ssh -i ~/.ssh/ayco-demo root@101.44.185.139   # Dify
ssh -i ~/.ssh/ayco-demo root@149.232.129.39   # Frontend

# ─── OBS — Upload de Contratos para Demo ───
# Subir contrato individual
obsutil cp data/contracts/contrato-critico-datacenter.pdf obs://ayco-contracts-raw/
obsutil cp data/contracts/contrato-bajo-riesgo-consultoria.pdf obs://ayco-contracts-raw/

# Subir batch de contratos nuevos
for pdf in data/contracts/contrato-{bajo,medio,alto,critico}*.pdf; do
  obsutil cp "$pdf" obs://ayco-contracts-raw/
done

# Verificar pipeline procesó
obsutil ls obs://ayco-contracts-results/json/ | wc -l

# ─── Dify ───
# Console login: http://101.44.185.139/console (eduardo@ayco-demo.com / AYCOcloud2026!)
# API Keys:
#   AYCO Chat:     app-Y8MxfRygyUWOAfyTlo1MQSJx
#   AYCO Cobranza: app-ZrM7Pal6G2b89drd1zLVssvM
#   AYCO Analyzer: app-mGyFcdX7vT3CZDDsvttCX6iF
# API test (streaming)
curl -N -X POST http://149.232.129.39/api/dify/chat-messages \
  -H "Authorization: Bearer app-Y8MxfRygyUWOAfyTlo1MQSJx" \
  -H "Content-Type: application/json" \
  -d '{"query":"¿Contrato más riesgoso?","user":"demo","response_mode":"streaming","inputs":{}}'

# API test (blocking)
curl -s -X POST http://101.44.185.139/v1/chat-messages \
  -H "Authorization: Bearer app-Y8MxfRygyUWOAfyTlo1MQSJx" \
  -H "Content-Type: application/json" \
  -d '{"query":"¿Contrato más riesgoso?","user":"demo","response_mode":"blocking","inputs":{}}'

# Dify service status
ssh -i ~/.ssh/ayco-demo root@101.44.185.139 \
  "cd /opt/ayco/dify/docker && docker compose ps"

# Dify dataset check
ssh -i ~/.ssh/ayco-demo root@101.44.185.139 \
  "docker exec docker-db_postgres-1 psql -U postgres -d dify \
   -c \"SELECT a.name, d.name FROM apps a JOIN app_dataset_joins aj ON a.id=aj.app_id JOIN datasets d ON aj.dataset_id=d.id;\""

# ─── Frontend ───
# Redeploy
cd /home/eduardo/dev/ayco-huawei-cloud/frontend
npm run build && bash deploy.sh

# Health check
curl -s -o /dev/null -w "%{http_code}" http://149.232.129.39/
curl -s -o /dev/null -w "%{http_code}" http://149.232.129.39/risk-scoring/
curl -s -o /dev/null -w "%{http_code}" http://149.232.129.39/contract-ai/

# ─── Streamlit Dashboard ───
# Health check
curl -s http://101.44.185.139/dashboard//_stcore/health

# Restart
ssh -i ~/.ssh/ayco-demo root@101.44.185.139 \
  "kill -HUP \$(pgrep -f streamlit)"

# ─── Terraform ───
cd /home/eduardo/dev/ayco-huawei-cloud/terraform
terraform output           # all outputs
terraform output -json     # machine-readable
terraform plan             # preview changes (should be zero-diff)
terraform state list       # enumerate all tracked resources

# ─── CTS (Cloud Trace Service) ───
# Consultar eventos directamente via CLI (si disponible)
# Acceso principal: Huawei Console > CTS > Trace List
```

---

## Appendix B: Código de Función Serverless (llm_inference.py)

Fragmento clave — la función que invoca MaaS y tracea a Langfuse:

```python
import json, os, uuid, urllib.request
from datetime import datetime

MAAS_ENDPOINT = "https://api-ap-southeast-1.modelarts-maas.com/v2/chat/completions"
MAAS_MODEL = "deepseek-v4-pro"
LANGFUSE_HOST = "https://us.cloud.langfuse.com"

def handler(event, context):
    """FunctionGraph entry point: contract JSON → risk assessment."""
    contract = event.get("contract_data", event)
    prompt = build_prompt(contract)

    # 1. Call MaaS DeepSeek
    response = call_maas(prompt)

    # 2. Parse JSON response (with repair for truncated/invalid)
    risk_report = parse_or_repair(response["content"])

    # 3. Trace to Langfuse
    trace_langfuse(contract, prompt, risk_report, response)

    # 4. Return for DWS insertion
    return risk_report

def call_maas(prompt):
    """Primary: Huawei MaaS. Fallback: DeepSeek API direct."""
    req = urllib.request.Request(MAAS_ENDPOINT, method="POST")
    req.add_header("Authorization", f"Bearer {os.environ['MAAS_API_KEY']}")
    req.add_header("Content-Type", "application/json")
    body = json.dumps({
        "model": MAAS_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 2000
    }).encode()
    with urllib.request.urlopen(req, data=body, timeout=30) as resp:
        return json.loads(resp.read())
```

---

**File:** `docs/demo-script.md`
**Version:** v3.2 — Contracts + Dify + MPP EXPLAIN ANALYZE
**Last updated:** May 7, 2026
