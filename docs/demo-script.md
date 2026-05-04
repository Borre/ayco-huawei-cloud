# AYCO Contract Risk Analysis — Demo Script

**Workshop:** Huawei Cloud LATAM × Grupo Salinas (AYCO)  
**Date:** May 8, 2026  
**Duration:** 45 min total (0-5 PPT, 5-15 Demo 1, 15-25 Demo 2, 25-38 Demo 3, 38-41 ROI/FinOps, 41-45 Q&A)  
**Region:** la-north-2 (Mexico City 2)  
**Audience:** Huawei Cloud LATAM Leadership  
**Presenter:** Eduardo  

---

## Pre-Workshop Checklist (complete by May 7, 6 PM)

- [ ] Run `make demo` and verify all services are healthy
- [ ] Run `bash scripts/health-check.sh` — all checks must pass
- [ ] Confirm Dify is accessible at ECS public IP, port 80
- [ ] Confirm DWS endpoint responds (PG client test)
- [ ] Confirm DataArts Studio instance is running in Huawei Console
- [ ] Upload the 3 demo contract PDFs to OBS bucket `ayco-contracts-raw`
- [ ] Run `bash scripts/backup-record-demos.sh` to record a dry-run of each demo
- [ ] Have Huawei Console tabs open and pinned: OBS, FunctionGraph, DLI, DWS, DataArts, ECS/Dify
- [ ] Test psql connection to DWS from your machine: `psql -h $DWS_ENDPOINT -U ayco_admin -d ayco_db`
- [ ] Have a browser with Huawei Cloud console logged in
- [ ] Verify DeepSeek API key is valid: `curl -H "Authorization: Bearer $DEEPSEEK_API_KEY" https://api.deepseek.com/v1/models`
- [ ] Confirm the 3 sample PDFs exist in OBS:
  - `contrato-01-alto-riesgo.pdf`
  - `contrato-02-bajo-riesgo.pdf`
  - `contrato-03-critico.pdf`
- [ ] Run `bash scripts/langfuse-setup.sh` and verify Langfuse dashboard displays traces
- [ ] Open Langfuse dashboard tab: https://cloud.langfuse.com → project ayco-demo (pinned)
- [ ] Verify Streamlit dashboard accessible at `http://<dify-ip>:8501`
- [ ] Confirm DataArts Catalog metadata collection task executed (lineage graph populated)
- [ ] Confirm DataArts Architecture — subject area + model + table visible in console
- [ ] Have browser tabs pinned: OBS, FunctionGraph, DLI, DWS, DataArts (Catalog/Architecture/Security/Factory), ECS/Dify, Streamlit Dashboard, Langfuse

---

# Demo 1: Risk Scoring with DLI + DWS (5-15 min)

## 1. Pre-demo Setup

- OBS bucket `ayco-contracts-raw` has the 3 contract PDFs uploaded
- FunctionGraph functions deployed: `ayco-ocr-trigger`, `ayco-parse-contract`, `ayco-llm-inference`
- DLI database `ayco_contracts` exists with `contracts` and `risk_results` tables
- DWS `ayco_db` has the `risk_results` table (created by `seed-dws.sql`)
- DWS pre-seeded with 3 contract records
- Terminal open with environment variables loaded: `DWS_ENDPOINT`, `DWS_ADMIN_PASSWORD`, `OBS_BUCKET`

## 2. Step-by-Step Commands / Screen Actions

### Step 1: Show PDFs in OBS (1 min)

Navigate to Huawei Cloud Console > OBS > Bucket `ayco-contracts-raw`

Show the 3 uploaded files:
- `contrato-01-alto-riesgo.pdf`
- `contrato-02-bajo-riesgo.pdf`
- `contrato-03-critico.pdf`

### Step 2: Trigger OCR via FunctionGraph (2 min)

Upload a new PDF to trigger the pipeline:

```bash
# Option A: Upload via CLI to trigger FunctionGraph event
huaweicloud-sdk-cli obs upload \
  --bucket ayco-contracts-raw \
  --key contrato-01-alto-riesgo.pdf \
  --file ./data/contracts/contrato-01-alto-riesgo.pdf

# Option B: Manually invoke FunctionGraph test
huaweicloud-sdk-cli fg invoke \
  --function-urn ayco-ocr-trigger \
  --body '{"bucket":"ayco-contracts-raw","key":"contrato-01-alto-riesgo.pdf"}'
```

Navigate to Huawei Console > FunctionGraph > `ayco-ocr-trigger` > Execution Logs

Show the real-time log output:
```
[OCR] Processing contrato-01-alto-riesgo.pdf
[OCR] Text extracted: 4,523 characters
[PARSE] Extracted 12 fields from contract text
[LLM] Calling DeepSeek v4 Flash for risk analysis...
[LLM] Response received: risk_score=8.7, level=ALTO
[OBS] Results saved: contrato-01-alto-riesgo.json
[Langfuse] ✓ Trace sent (450ms)
[Langfuse] ✓ Trace sent (320ms)
```

> **🎤 Speaker:** "Cada llamada al LLM genera automáticamente un trace en Langfuse — sin código extra. Latencia, tokens, provider, todo queda registrado. Abran el dashboard."

### Step 2b: Show Langfuse Observability Dashboard (1 min)

Switch to browser tab: **Langfuse Cloud → ayco-demo project**

Show the real-time trace dashboard:
- **Traces:** list of contract-risk-analysis traces with latency (ms) per call
- **Generations:** each MaaS/DeepSeek call with model, input/output preview, token count
- **Metrics:** average latency, total tokens, error rate over time

> **🎤 Speaker:** "Esto es lo que llamamos *LLM observability*. Langfuse Cloud free tier, desplegado como sidecar — no toca el pipeline principal. Si falla Langfuse, el análisis de riesgo sigue funcionando sin interrupción. Non-blocking."

### Step 3: Show DLI Spark Job (2 min)

```bash
# Submit Spark aggregation job
dli spark-submit \
  --cluster ayco-dli-cluster \
  --app scripts/spark-risk-aggregation.py \
  --database ayco_contracts \
  --output obs://ayco-contracts-results/aggregated/
```

Navigate to Huawei Console > DLI > Spark Jobs > Show job running

Show Spark UI output:

```
=== RISK SUMMARY ===
+------------+--------------+--------------+--------------+--------------+
|risk_level  |contract_count|avg_risk_score|min_risk_score|max_risk_score|
+------------+--------------+--------------+--------------+--------------+
|CRITICO     |1             |9.20          |9.20          |9.20          |
|ALTO        |1             |8.70          |8.70          |8.70          |
|BAJO        |1             |2.30          |2.30          |2.30          |
+------------+--------------+--------------+--------------+--------------+

=== HIGH RISK CONTRACTS ===
+-----------------+------------------+------------+----------+----------+---------------------------+
|contract_number  |contratista       |monto_total |risk_score|risk_level|alertas                    |
+-----------------+------------------+------------+----------+----------+---------------------------+
|CTR-2024-003     |Constructora XYZ |$15,000,000 |9.20      |CRITICO   |Penalización excesiva...   |
|CTR-2024-001     |TechMex SA       |$8,500,000  |8.70      |ALTO      |Cláusulas de terminación...|
+-----------------+------------------+------------+----------+----------+---------------------------+
```

### Step 4: DWS Queries — Live Analytics (3 min)

```bash
# Connect to DWS
PGPASSWORD=$DWS_ADMIN_PASSWORD psql -h $DWS_ENDPOINT -U ayco_admin -d ayco_db
```

```sql
-- Query 1: Risk distribution by level
SELECT risk_level, COUNT(*) AS count,
       ROUND(AVG(risk_score), 1) AS avg_score
FROM risk_results
GROUP BY risk_level
ORDER BY avg_score DESC;
```

Expected output:
```
 risk_level | count | avg_score
------------+-------+-----------
 CRITICO    |     1 |       9.2
 ALTO       |     1 |       8.7
 BAJO       |     1 |       2.3
```

```sql
-- Query 2: High-risk contracts
SELECT contract_number, vendor_name, risk_score, risk_level, alertas
FROM risk_results
WHERE risk_score >= 7
ORDER BY risk_score DESC;
```

Expected output:
```
 contract_number | vendor_name      | risk_score | risk_level | alertas
-----------------+------------------+------------+------------+-------------------------------
 CTR-2024-003    | Constructora XYZ |       9.20 | CRITICO    | Penalización excesiva, ...
 CTR-2024-001    | TechMex SA       |       8.70 | ALTO       | Cláusulas de terminación...
```

```sql
-- Query 3: Vendor exposure
SELECT vendor_name, COUNT(*) AS contracts,
       SUM(monto_total) AS total_exposure,
       AVG(risk_score) AS avg_risk
FROM risk_results
GROUP BY vendor_name
ORDER BY total_exposure DESC;
```

Expected output:
```
   vendor_name   | contracts | total_exposure | avg_risk
-----------------+-----------+----------------+-----------
 Constructora XYZ|         1 |  15000000.00   |   9.20
 TechMex SA      |         1 |   8500000.00   |   8.70
 LogiPro MX      |         1 |   2300000.00   |   2.30
```

```sql
-- Query 4: Materialized view refresh (show governance)
REFRESH MATERIALIZED VIEW dm.vendor_risk_summary;
SELECT * FROM dm.vendor_risk_summary;
```

Exit psql with `\q`

## 3. Talking Points

**Opening (Spanish):**
> "Buenos días a todos. Hoy vamos a mostrarles cómo AYCO — una empresa del Grupo Salinas — está usando Huawei Cloud para analizar contratos de proveedores y detectar riesgos de forma automatizada. Vamos a empezar con el scoring de riesgo usando DLI y DWS."

**While uploading PDFs:**
> "Aquí tenemos 3 contratos de ejemplo: uno de alto riesgo, uno de bajo riesgo, y uno crítico. Cuando estos PDFs llegan a OBS, se dispara automáticamente una función en FunctionGraph que hace OCR para extraer el texto."

**While showing FunctionGraph logs:**
> "Miren cómo funciona el pipeline: primero el OCR extrae el texto del PDF. Luego la función parse_contract.py extrae los campos clave — monto, penalizaciones, garantías, jurisdicción — usando expresiones regulares. Y finalmente, llamamos al modelo DeepSeek v4 Flash a través de MaaS para que analice el contrato completo y nos dé un puntaje de riesgo. Todo esto es serverless, sin servidores que administrar."

**While showing DLI Spark job:**
> "Una vez que tenemos los resultados de cada contrato, usamos DLI — el servicio de Spark administrado de Huawei Cloud — para agregar toda la información. Con un solo job de Spark, correlacionamos contratos con resultados de riesgo y generamos métricas consolidadas."

**While running DWS queries:**
> "Y finalmente, todo aterriza en DWS, nuestro data warehouse. Aquí podemos hacer consultas analíticas en tiempo real: distribución de riesgo por nivel, contratos de alto riesgo con sus alertas, y exposición total por proveedor. Todo esto con latencia de milisegundos."

**Closing (Spanish):**
> "En menos de 10 minutos, pasamos de PDFs en bruto a insights de negocio accionables. Sin infraestructura que administrar, sin pipelines manuales. Esto es lo que Huawei Cloud nos permite hacer con DLI, DWS y FunctionGraph."

## 4. Expected Output

- FunctionGraph execution logs showing successful OCR, parsing, and LLM inference
- DLI Spark job completes with `SUCCESS` status
- 3 DWS queries return meaningful results with risk scores and alerts
- Total demo time: ~10 minutes

## 5. Backup Plan

| Failure Scenario | Backup Action |
|---|---|
| FunctionGraph invocation fails | Pre-recorded video of FunctionGraph execution logs |
| DLI Spark job stuck | Use pre-generated Spark output files in `backports/demo1-spark-output.txt` |
| DWS connection refused | Use recorded screenshots of query results |
| DeepSeek API timeout | Use pre-cached LLM response in `backports/demo1-llm-response.json` |
| PDFs not in OBS | Use `make demo` seed data that pre-loads contracts into DWS |

To switch to backup:
```bash
# Play recorded demo
bash scripts/backup-record-demos.sh --play demo1
# Or show pre-recorded screenshots
open backports/demo1-screenshots/
```

## 6. Transition to Demo 2

**Transition (Spanish):**
> "Ahora que ya tenemos nuestros datos de riesgo analizados y almacenados, la pregunta es: ¿cómo gobernamos todo este pipeline de datos? ¿Cómo aseguramos la calidad? ¿Cómo exponemos estos datos de forma segura? Para eso, vamos a ver DataArts Studio, la plataforma de gobernanza de datos de Huawei Cloud."

---

# Demo 2: Data Governance & Intelligence (15-25 min)

## 1. Pre-demo Setup

- DataArts Studio instance created (via Terraform `data-platform/dataarts.tf`)
- DataArts workspace: `ayco-dataarts-workspace`
- **DataArts Catalog:** metadata collection task executed, lineage graph populated
- **DataArts Architecture:** subject area + data model + table model defined
- **DataArts Security:** recognition rule + secrecy level + dynamic masking policy created
- Data connections configured:
  - `ayco-dli-connection` (DLI)
  - `ayco-dws-connection` (DWS) via CDM Agent
- Factory job `contract-risk-etl-pipeline` created with 3 nodes
- DataService APIs published:
  - `GET /api/v1/risk-results`
  - `GET /api/v1/contracts/{id}`
- DataService API key generated and saved
- **Streamlit dashboard** deployed on ECS `ayco-dify` (port 8501)
- **Langfuse dashboard** open in browser tab (cloud.langfuse.com > ayco-demo)
- Browser tabs:
  - Huawei Console > DataArts Studio > Catalog (lineage view)
  - Huawei Console > DataArts Studio > Architecture
  - Huawei Console > DataArts Studio > Security
  - Huawei Console > DataArts Studio > Factory
  - Streamlit Dashboard (`http://<dify-ip>:8501`)
  - Langfuse Traces (`https://cloud.langfuse.com/project/ayco-demo`)

## 2. Step-by-Step Commands / Screen Actions

### Step 1: DataArts Catalog — Data Lineage (1.5 min)

Navigate to Huawei Console > DataArts Studio > Catalog > Data Map

Show the **data lineage graph**:

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   OBS            │     │  FunctionGraph   │     │  DLI (Spark)     │
│  contracts-raw   │────>│  OCR + LLM       │────>│  Aggregation     │
│                  │     │  (DeepSeek MaaS) │     │                  │
└──────────────────┘     └──────────────────┘     └────────┬─────────┘
                                                           │
                                                           ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  DataService API │     │  DWS             │     │  CDM Agent       │
│  GET /risk-      │<────│  risk_results    │<────│  Data Transfer   │
│  results         │     │                  │     │                  │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

**Speaker (Spanish):**
> "DataArts Catalog nos da trazabilidad completa — de punta a punta. Pueden ver exactamente cómo el dato viaja: desde el PDF en OBS, pasa por FunctionGraph para OCR y análisis con IA, se agrega en DLI Spark, se carga a DWS, y se expone como API. Si un regulador pregunta '¿de dónde salió este risk score?', tenemos la respuesta en un click. Esto ningún otro cloud lo da integrado."

Click on any node to show field-level lineage (contract_number, risk_score columns traversing the pipeline).

### Step 2: DataArts Architecture — Data Modeling (1 min)

Navigate to DataArts Studio > Architecture > Data Architecture

Show:
- **Subject Area:** "Gestión de Riesgo Contractual" (AYCO_CONTRACT_RISK)
- **Data Model:** "AYCO Contract Risk Model" (3NF, físico)
- **Table Model:** `risk_results` con 5 columnas documentadas (contract_number, vendor_name, monto_total, risk_score, risk_level)

**Speaker:**
> "No solo movemos datos — los gobernamos. Aquí tenemos el modelo de datos documentado: área temática, modelo lógico, y mapeo a la tabla física en DWS. Esto es gobierno de datos de verdad: cada columna tiene dueño, tipo, y está vinculada a un estándar de arquitectura."

### Step 3: DataArts Security — Classification & Masking (1 min)

Navigate to DataArts Studio > Security > Data Recognition

Show:
- **Secrecy Level:** "Contract_Financial_Sensitive" — clasifica datos financieros de contratos
- **Recognition Rule:** "Detect_Financial_Amounts" — detecta montos, penalizaciones y garantías automáticamente
- **Dynamic Masking Policy:** "Mask_Vendor_Names" — enmascara nombres de proveedores en la API para usuarios no autorizados

**Speaker:**
> "En el sector financiero, la seguridad de datos no es opcional. Aquí DataArts clasifica automáticamente los campos sensibles — montos, proveedores, penalizaciones — y aplica enmascaramiento dinámico. Si alguien sin permisos consulta la API, en lugar de 'Constructora XYZ' ve 'C***Z'. Los datos están protegidos desde el origen."

### Step 4: DataArts Factory — ETL Pipeline (2 min)

Navigate to DataArts Studio > Factory > Jobs > `contract-risk-etl-pipeline`

Show the DAG visualization and click "Run":

```
┌─────────────┐     ┌─────────────┐     ┌───────────────┐
│   PARSE     │────>│    LOAD     │────>│ QUALITY CHECK │
│             │     │             │     │               │
│ Read from   │     │ Load to     │     │ Validate      │
│ OBS/JSON    │     │ DWS tables  │     │ completeness  │
└─────────────┘     └─────────────┘     └───────────────┘
```

Show job execution log:
```
[PARSER] Reading from obs://ayco-contracts-results/aggregated/
[PARSER] Found 3 JSON files, parsed 12 records
[LOADER] Loading to dws://ayco_db.risk_results
[LOADER] 12 records inserted successfully
[QUALITY] Running 5 quality checks...
[QUALITY] ✓ No null contract_number
[QUALITY] ✓ Risk scores in range 0-10
[QUALITY] ✓ All dates valid
[QUALITY] ✓ Vendor names non-empty
[QUALITY] ✓ Risk levels valid enum
[PIPELINE] All quality checks passed — status: SUCCESS
```

**Speaker:**
> "Pipeline orquestado, con quality checks automatizados. Si cualquier validación falla, el pipeline se detiene. No tomamos decisiones con datos sucios."

### Step 5: Streamlit Dashboard — Visual Intelligence (1.5 min)

Switch to browser tab: Streamlit Dashboard (`http://<dify-ip>:8501`)

Show the live dashboard:
- **KPI Row:** Total Contracts, Avg Risk Score, Critical Alerts, Total Exposure, Pipeline Status
- **Risk Distribution Chart:** Bar chart with color-coded risk levels (verde=bajo, amarillo=medio, naranja=alto, rojo=crítico)
- **Vendor Exposure Chart:** Horizontal bars showing exposure by vendor, colored by avg risk
- **Contract Details Table:** Full sortable/filterable table with risk scores as progress bars

**Speaker:**
> "Y esto es lo mejor: todo este dashboard corre en Streamlit, una herramienta open-source, en el mismo ECS donde tenemos Dify. Cero infraestructura adicional. Conectado directo a DWS, datos en tiempo real. En producción, esto se puede publicar con HTTPS y autenticación SSO."

Note the footer showing: "Data: Huawei Cloud DWS | AI: DeepSeek v4 Flash via MaaS | Observability: Langfuse"

### Step 6: Langfuse — LLM Observability (1 min)

Switch to Langfuse dashboard tab (cloud.langfuse.com > ayco-demo)

Show:
- **Traces view:** Cada llamada al LLM registrada con trace_id, latencia, tokens, provider, y contract_number
- **Latency distribution:** 200-500ms promedio para DeepSeek v4 Flash
- **Cost tracking:** ~$0.0001 por análisis de contrato

**Speaker:**
> "Cada llamada al modelo de IA está trazada. Sabemos exactamente cuánto tarda, cuánto cuesta, y qué contrato analizó. Si el modelo empieza a alucinar, lo detectamos inmediatamente. Langfuse es open-source y se integra en 3 líneas de código — sin vendor lock-in."

### Step 7: DataService REST API — Live Demo (2 min)

```bash
# Set API key from Terraform outputs
export DATAARTS_API_KEY="<api-key-from-dataarts-console>"
export DATAARTS_BASE_URL="<data-service-endpoint>"

# Call 1: Get all risk results (shows masked vendor names for unauthorized users)
curl -s -H "X-DataArts-Token: $DATAARTS_API_KEY" \
  "$DATAARTS_BASE_URL/api/v1/risk-results?risk_level=CRITICO" | python3 -m json.tool
```

Expected output (note masked vendor_name):
```json
{
  "code": 0,
  "data": [
    {
      "contract_number": "CTR-2024-003",
      "vendor_name": "C***Z",
      "monto_total": 15000000.00,
      "risk_score": 9.20,
      "risk_level": "CRITICO",
      "alertas": "Penalización excesiva del 15%. Garantía insuficiente.",
      "recomendaciones": "Renegociar penalización. Aumentar garantía al 15%.",
      "llm_provider": "deepseek-v4-flash"
    }
  ]
}
```

**Speaker:**
> "API lista para consumo, con enmascaramiento dinámico activo. El equipo legal ve 'C***Z', el equipo de riesgos con permisos ve 'Constructora XYZ'. Mismos datos, diferentes vistas según el rol."

## 3. Talking Points

**Opening (Spanish):**
> "Acabamos de ver cómo se analizan los contratos con IA. Ahora vamos a ver cómo gobernamos esos datos: trazabilidad, modelado, seguridad, calidad, visualización, y observabilidad. Porque en una empresa como AYCO, no basta con analizar — necesitas confiar en los datos."

**During Catalog (lineage):**
> "Data lineage automatizado. Sin configurar nada, DataArts descubre de dónde vienen los datos y a dónde van. Si cambia algo en el pipeline, el grafo se actualiza solo."

**During Architecture:**
> "Modelo de datos documentado, no adivinado. Cada tabla, cada columna, está registrada en el catálogo de arquitectura. Esto es lo que separa un data lake de un data swamp."

**During Security:**
> "Clasificación automática y enmascaramiento dinámico. Cumplimos con regulación financiera sin escribir una sola regla manual."

**During Dashboard:**
> "Dashboard en tiempo real, open-source, corriendo en el mismo ECS. Sin licencias, sin infraestructura extra. Puro valor."

**During API:**
> "APIs gobernadas. El consumidor no necesita saber SQL, no necesita acceso a DWS. Solo consume la API con su token."

**Closing (Spanish):**
> "En 10 minutos cubrimos las 6 dimensiones de gobierno de datos: linaje, modelo, seguridad, calidad, visualización, y exposición. Todo integrado en DataArts Studio. Esto no es un pipeline de datos más — es una plataforma de confianza."

## 4. Expected Output

- Catalog lineage graph shows OBS → FunctionGraph → DLI → DWS → API
- Architecture shows subject area + data model + table with 5 documented columns
- Security shows 1 secrecy level, 1 recognition rule, 1 masking policy
- ETL pipeline executes 3 nodes with SUCCESS status and 5/5 quality checks passed
- Streamlit dashboard loads with KPIs, charts, and full data table
- Langfuse shows trace for the most recent LLM call (latency, tokens, cost)
- DataService API returns JSON with masked vendor_name for unauthorized user
- Total demo time: ~10 minutes

## 5. Backup Plan

| Failure Scenario | Backup Action |
|---|---|
| DataArts Catalog not loading | Show architecture diagram (docs/architecture.drawio) with lineage |
| DataArts Architecture page error | Show Terraform code as proof of resource definition |
| Security masking not active | Show API response manually with `sed 's/vendor_name.*/vendor_name": "C***Z"/'` |
| ETL pipeline fails | Use `backports/demo2-etl-output.txt` with pre-captured log |
| Streamlit dashboard 502 | Show dashboard screenshot in `backports/demo2-dashboard.png` |
| Langfuse not loading | Show Langfuse Terraform vars + code as proof of integration |
| DataService API returns 500 | Use `backports/demo2-api-outputs.json` |

To switch to backup:
```bash
# Show pre-recorded dashboard
open backports/demo2-dashboard.png
# Show pre-recorded API responses
cat backports/demo2-api-outputs.json | python3 -m json.tool
# Show lineage diagram
open docs/architecture.drawio
```

## 6. Transition to Demo 3

**Transition (Spanish):**
> "Ya tenemos los datos gobernados, visibles en dashboard, y expuestos como APIs. Ahora vamos a dar el salto más interesante: ¿qué pasa cuando un usuario de negocio — sin saber SQL, sin conocer DataArts — quiere hacer preguntas sobre estos contratos? Vamos a ver nuestro chatbot de IA con Dify."

---

# Demo 3: Contract AI + Dify Chatbot (22-35 min)

## 1. Pre-demo Setup

- Dify deployed on ECS instance `s6.xlarge.2` (4vCPU/8GB) (confirmed via `make status`)
- Dify accessible at ECS public IP (port 80)
- Dify admin credentials available
- Knowledge base `ayco-contracts-kb` created and indexed
- Contract data documents uploaded to knowledge base
- Dify chatbot app `ayco-contract-assistant` published
- OCR processing endpoint available via FunctionGraph
- Browser tabs:
  - Dify Web UI (logged in)
  - Huawei Console > ECS (to show instance)
  - Huawei Console > FunctionGraph (for live OCR demo)
- Terminal with environment: `DIFY_PUBLIC_IP`, `DIFY_API_KEY`

## 2. Step-by-Step Commands / Screen Actions

### Step 1: Show Dify Deployment on ECS (1 min)

```bash
# Show ECS instance running Dify
huaweicloud-sdk-cli ecs list-instances --name dify-ayco
```

Navigate to Huawei Console > ECS > Show `dify-ayco` instance (s6.large.2)

Show docker-compose status:
```bash
ssh root@$DIFY_PUBLIC_IP "cd /opt/dify/docker && docker compose ps"
```

Expected output:
```
NAME                STATUS         PORTS
dify-api            Up 2 hours     0.0.0.0:5001->5001/tcp
dify-web            Up 2 hours     0.0.0.0:80->3000/tcp
dify-worker         Up 2 hours
dify-sandbox        Up 2 hours
dify-db             Up 2 hours     5432/tcp
dify-redis          Up 2 hours     6379/tcp
dify-weaviate       Up 2 hours     8080/tcp
```

### Step 2: Show Knowledge Base (1 min)

Navigate to Dify UI > Knowledge > `ayco-contracts-kb`

Show:
- Indexing status: `Indexed`
- Documents: `3 contracts indexed`
- Embedding model: `bge-large-zh` or equivalent
- Retrieval settings: Top-K = 3, Score threshold = 0.5

### Step 3: Chatbot — Query 1 (2 min)

Navigate to Dify UI > Apps > `ayco-contract-assistant` > Chat

**User question:** "Cuáles son los contratos de alto riesgo?"

Expected chatbot response:
> "Actualmente hay 2 contratos con nivel de riesgo ALTO o CRÍTICO:
>
> 1. **CTR-2024-003 — Constructora XYZ** (Riesgo CRÍTICO, Score: 9.2)
>    - Monto: $15,000,000 MXN
>    - Alertas: Penalización excesiva del 15%. Garantía insuficiente. Sin cláusula de confidencialidad.
>    - Recomendación: Renegociar penalización. Aumentar garantía al 15%. Agregar cláusula de confidencialidad.
>
> 2. **CTR-2024-001 — TechMex SA** (Riesgo ALTO, Score: 8.7)
>    - Monto: $8,500,000 MXN
>    - Alertas: Cláusulas de terminación anticipada desfavorables. Penalización por retraso excesiva.
>    - Recomendación: Negociar cláusula de terminación. Reducir penalización a 2%.
>
> El contrato de bajo riesgo es CTR-2024-002 (LogiPro MX, Score: 2.3)."

### Step 4: Chatbot — Query 2 (2 min)

**User question:** "Cuál es la penalización del contrato 001?"

Expected chatbot response:
> "El contrato CTR-2024-001 (TechMex SA) tiene las siguientes penalizaciones:
>
> - **Penalización por terminación anticipada:** 5% del monto total
> - **Penalización por retraso:** $15,000 MXN por día de retraso
> - **Monto total del contrato:** $8,500,000 MXN
>
> ⚠️ Esta penalización por terminación anticipada del 5% está por encima del promedio del mercado (2-3%). Se recomienda renegociar esta cláusula."

### Step 5: Live OCR Processing (3 min)

```bash
# Upload a new contract PDF to trigger the full pipeline live
huaweicloud-sdk-cli obs upload \
  --bucket ayco-contracts-raw \
  --key contrato-demo-nuevo.pdf \
  --file ./data/contracts/contrato-03-critico.pdf
```

Navigate to Huawei Console > FunctionGraph > `ayco-ocr-trigger` > Logs

Show the real-time processing:

```
[OCR] Processing contrato-demo-nuevo.pdf
[OCR] Extracting text from PDF...
[OCR] 3,891 characters extracted
[PARSE] Extracting fields...
[PARSE] Found: contract_number=CTR-2024-005, monto_total=$5,200,000, penalizacion=3%
[LLM] Sending to DeepSeek v4 Flash...
[LLM] Risk analysis complete: score=6.1, level=MEDIO
[LLM] Alertas: Cláusula de jurisdicción ambigua. Falta definición de SLA.
[OBS] Results saved to obs://ayco-contracts-results/contrato-demo-nuevo.json
```

### Step 6: Chatbot — Query about new contract (2 min)

**User question:** "Acaban de subir un nuevo contrato, qué riesgo tiene?"

Expected chatbot response:
> "Detecto que se acaba de procesar un nuevo contrato:
>
> **CTR-2024-005** — (Vendor pending)
> - Monto: $5,200,000 MXN
> - Riesgo: MEDIO (Score: 6.1)
> - Alertas: Cláusula de jurisdicción ambigua. Falta definición de SLA.
> - Recomendación: Definir jurisdicción clara. Agregar SLA con métricas de cumplimiento.
>
> Este contrato tiene un riesgo moderado. Las alertas principales son sobre ambigüedad en la jurisdicción y falta de SLA, que son fáciles de corregir en una renegociación."

### Step 7: Show Dify Architecture (1 min)

Briefly show in Dify:
- Prompt template configuration
- Knowledge base retrieval settings
- LLM provider: DeepSeek v4 Flash via MaaS

## 3. Talking Points

**Opening (Spanish):**
> "Ya tenemos los datos analizados, gobernados y expuestos como APIs. Ahora vamos a ver la capa de inteligencia artificial que permite a cualquier usuario de negocio — sin saber SQL, sin saber programación — consultar todos estos contratos en lenguaje natural."

**While showing Dify on ECS:**
> "Dify está corriendo en una instancia ECS de Huawei Cloud, tipo s6.large.2. Usamos docker-compose para levantar todos los microservicios: el frontend, la API, el worker, la base de datos, Redis y Weaviate para la búsqueda vectorial. Todo en un solo servidor, sin costos innecesarios."

**While showing Knowledge Base:**
> "Aquí indexamos todos los contratos analizados. Dify usa embeddings para convertir el texto de cada contrato en vectores, y cuando alguien hace una pregunta, busca los contratos más relevantes antes de generar la respuesta. Esto se llama Retrieval-Augmented Generation o RAG."

**During chat queries:**
> "Miren cómo el chatbot entiende la pregunta, busca en la base de conocimiento de contratos, y genera una respuesta estructurada con los datos reales. No está inventando — está citando los resultados de nuestro análisis de riesgo que vimos en el Demo 1."

**During live OCR:**
> "Y aquí viene la parte más impresionante: subimos un contrato nuevo y en tiempo real pueden ver cómo se procesa. OCR, extracción de campos, análisis con IA, y almacenamiento de resultados. Todo automatizado."

**Closing (Spanish):**
> "Con esta combinación — OCR con FunctionGraph, análisis con DeepSeek MaaS, procesamiento con DLI, almacenamiento con DWS, gobernanza con DataArts, y chatbot con Dify — AYCO tiene una plataforma completa de análisis de riesgo contractual. Desde el PDF crudo hasta la respuesta en lenguaje natural, todo en la nube de Huawei."

## 4. Expected Output

- Dify dashboard accessible and responsive
- Knowledge base shows 3 indexed contracts
- Chatbot answers 2 pre-defined questions with accurate, structured responses
- Live OCR pipeline processes a new PDF end-to-end in ~30-60 seconds
- Chatbot provides information about the newly processed contract
- Total demo time: ~13 minutes

## 5. Backup Plan

| Failure Scenario | Backup Action |
|---|---|
| Dify ECS not responding | Show pre-recorded video of Dify chatbot interaction |
| Knowledge base not indexed | Use `backports/demo3-chat-outputs.txt` with pre-captured responses |
| Live OCR pipeline fails | Show pre-recorded FunctionGraph logs of OCR processing |
| Chatbot gives wrong answer | Use pre-recorded screenshots of correct chatbot responses |
| DeepSeek MaaS unavailable | Switch to backup LLM provider or use cached responses |

To switch to backup:
```bash
# Show pre-recorded chatbot interaction
cat backports/demo3-chat-outputs.txt
# Or play video recording
bash scripts/backup-record-demos.sh --play demo3
```

## 6. Transition to ROI Slide

**Transition (Spanish):**
> "En 35 minutos, vimos una plataforma completa de análisis de riesgo contractual corriendo 100% en Huawei Cloud. Ahora déjenme mostrarles el impacto de negocio — el ROI que esto genera para AYCO."

---

## Appendix A: Terraform Output Reference

```bash
# Get all outputs needed for the demo
cd /home/eduardo/dev/ayco-huawei-cloud/terraform

# Core endpoints
terraform output -raw dify_public_ip          # Dify web UI
terraform output -raw dws_endpoint            # DWS connection
terraform output -json obs_buckets            # OBS bucket names (list)
terraform output -raw dataarts_workspace_id   # DataArts workspace

# All outputs
terraform output
```

## Appendix B: Environment Variables

```bash
# Source before demo
export DWS_ENDPOINT=$(cd /home/eduardo/dev/ayco-huawei-cloud/terraform && terraform output -raw dws_endpoint)
export DWS_ADMIN_PASSWORD=$(op read "op://Huawei/AK-SK HUAWEI CLOUD/dws_password")
export DIFY_PUBLIC_IP=$(cd /home/eduardo/dev/ayco-huawei-cloud/terraform && terraform output -raw dify_public_ip)
export DEEPSEEK_API_KEY=$(op read "op://DeepSeek/API/key")
export OBS_BUCKET="ayco-contracts-raw"
export HUAWEI_ACCESS_KEY=$(op read "op://Huawei/AK-SK/username")
export HUAWEI_SECRET_KEY=$(op read "op://Huawei/AK-SK/password")
```

## Appendix C: Emergency Contacts

| Issue | Contact |
|---|---|
| Huawei Cloud support | Support ticket via console, priority: Critical |
| DeepSeek API issues | deepseek-support@deepseek.com |
| Dify deployment issues | Check /opt/dify/docker/logs/ |
| Terraform issues | `terraform plan` to diagnose drift |

## Appendix D: File Locations

| File | Path |
|---|---|
| Demo script | `docs/demo-script.md` |
| Spark aggregation job | `scripts/spark-risk-aggregation.py` |
| DWS seed SQL | `scripts/seed-dws.sql` |
| Contract parser | Inline in `terraform/modules/ai-ocr/functiongraph.tf` |
| LLM inference | Inline in `terraform/modules/ai-ocr/functiongraph.tf` |
| OCR trigger | Inline in `terraform/modules/ai-ocr/functiongraph.tf` |
| Health check | `scripts/health-check.sh` |
| Backup recordings | `scripts/backup-record-demos.sh` |
| Dify setup | `scripts/setup-dify.sh` |
| KB indexing | `scripts/index-knowledge-base.py` |
| Contract data gen | `scripts/generate-contract-data.py` |
| Upload to OBS | `scripts/upload-contracts-to-obs.sh` |
| DataArts test | `scripts/test-dataarts-api.sh` |
| Financial data gen | `scripts/generate-test-data.py` |
