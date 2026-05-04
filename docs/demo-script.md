# AYCO Contract Risk Analysis — Demo Script

**Workshop:** Huawei Cloud LATAM × Grupo Salinas (AYCO)  
**Date:** May 8, 2026  
**Duration:** 45 min total (0-5 PPT, 5-15 Demo 1, 15-22 Demo 2, 22-35 Demo 3, 35-40 ROI, 40-45 Q&A)  
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
- [ ] Upload the 3 demo contract PDFs to OBS bucket `ayco-contracts-input`
- [ ] Run `bash scripts/backup-record-demos.sh` to record a dry-run of each demo
- [ ] Have Huawei Console tabs open and pinned: OBS, FunctionGraph, DLI, DWS, DataArts, ECS/Dify
- [ ] Test psql connection to DWS from your machine: `psql -h $DWS_ENDPOINT -U ayco_admin -d ayco_db`
- [ ] Have a browser with Huawei Cloud console logged in
- [ ] Verify DeepSeek API key is valid: `curl -H "Authorization: Bearer $DEEPSEEK_API_KEY" https://api.deepseek.com/v1/models`
- [ ] Confirm the 3 sample PDFs exist in OBS:
  - `contrato-01-alto-riesgo.pdf`
  - `contrato-02-bajo-riesgo.pdf`
  - `contrato-03-critico.pdf`

---

# Demo 1: Risk Scoring with DLI + DWS (5-15 min)

## 1. Pre-demo Setup

- OBS bucket `ayco-contracts-input` has the 3 contract PDFs uploaded
- FunctionGraph functions deployed: `ayco-ocr-trigger`, `ayco-parse-contract`, `ayco-llm-inference`
- DLI database `ayco_contracts` exists with `contracts` and `risk_results` tables
- DWS `ayco_db` has the `risk_results` table (created by `seed-dws.sql`)
- DWS pre-seeded with 3 contract records
- Terminal open with environment variables loaded: `DWS_ENDPOINT`, `DWS_ADMIN_PASSWORD`, `OBS_BUCKET`

## 2. Step-by-Step Commands / Screen Actions

### Step 1: Show PDFs in OBS (1 min)

Navigate to Huawei Cloud Console > OBS > Bucket `ayco-contracts-input`

Show the 3 uploaded files:
- `contrato-01-alto-riesgo.pdf`
- `contrato-02-bajo-riesgo.pdf`
- `contrato-03-critico.pdf`

### Step 2: Trigger OCR via FunctionGraph (2 min)

Upload a new PDF to trigger the pipeline:

```bash
# Option A: Upload via CLI to trigger FunctionGraph event
huaweicloud-sdk-cli obs upload \
  --bucket ayco-contracts-input \
  --key contrato-04-nuevo.pdf \
  --file ./data/sample-contracts/contrato-04-nuevo.pdf

# Option B: Manually invoke FunctionGraph test
huaweicloud-sdk-cli fg invoke \
  --function-urn ayco-ocr-trigger \
  --body '{"bucket":"ayco-contracts-input","key":"contrato-01-alto-riesgo.pdf"}'
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
```

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

# Demo 2: Data Governance with DataArts (15-22 min)

## 1. Pre-demo Setup

- DataArts Studio instance created (via Terraform `data-platform/dataarts.tf`)
- DataArts workspace: `ayco-dataarts-workspace`
- Data connections configured:
  - `ayco-dli-connection` (DLI)
  - `ayco-dws-connection` (DWS)
- Factory job `contract-risk-etl-pipeline` created with 3 nodes
- DataService APIs published:
  - `GET /api/v1/risk-results`
  - `GET /api/v1/contracts/{id}`
- DataService API key generated and saved
- Browser tab: Huawei Console > DataArts Studio (logged in)

## 2. Step-by-Step Commands / Screen Actions

### Step 1: Show DataArts Studio Instance (1 min)

Navigate to Huawei Console > DataArts Studio > Workspace `ayco-dataarts-workspace`

Show the workspace dashboard with connected data sources.

### Step 2: Show Data Connections (2 min)

In DataArts Studio > Data Connections:

Show connections:
```
Connection Name        | Type  | Status
---------------------- |-------|--------
ayco-dli-connection    | DLI   | Connected
ayco-dws-connection    | DWS   | Connected
```

### Step 3: Show ETL Pipeline DAG (3 min)

Navigate to DataArts Studio > Factory > Jobs > `contract-risk-etl-pipeline`

Show the DAG visualization:

```
┌─────────────┐     ┌─────────────┐     ┌───────────────┐
│   PARSE     │────>│    LOAD     │────>│ QUALITY CHECK │
│             │     │             │     │               │
│ Read from   │     │ Load to     │     │ Validate      │
│ OBS/JSON    │     │ DWS tables  │     │ completeness  │
└─────────────┘     └─────────────┘     └───────────────┘
```

Click "Run" to execute the pipeline.

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

### Step 4: Call DataService REST API Live (3 min)

```bash
# Set API key from Terraform outputs or environment
export DATAARTS_API_KEY="<api-key-from-dataarts-console>"
export DATAARTS_BASE_URL="<data-service-endpoint>"

# Call 1: Get all risk results
curl -s -H "X-DataArts-Token: $DATAARTS_API_KEY" \
  "$DATAARTS_BASE_URL/api/v1/risk-results" | python3 -m json.tool
```

Expected output:
```json
{
  "code": 0,
  "data": [
    {
      "contract_number": "CTR-2024-001",
      "vendor_name": "TechMex SA",
      "monto_total": 8500000.00,
      "plazo_dias": 365,
      "penalizacion_pct": 5.00,
      "garantia_pct": 10.00,
      "risk_score": 8.70,
      "risk_level": "ALTO",
      "alertas": "Cláusulas de terminación anticipada desfavorables. Penalización por retraso excesiva.",
      "recomendaciones": "Negociar cláusula de terminación. Reducir penalización a 2%.",
      "resumen": "Contrato de servicios tecnológicos con múltiples riesgos contractuales.",
      "llm_provider": "deepseek-v4-flash",
      "analyzed_at": "2026-05-08T10:15:00Z"
    },
    {
      "contract_number": "CTR-2024-002",
      "vendor_name": "LogiPro MX",
      "risk_score": 2.30,
      "risk_level": "BAJO",
      ...
    }
  ]
}
```

```bash
# Call 2: Get specific contract
curl -s -H "X-DataArts-Token: $DATAARTS_API_KEY" \
  "$DATAARTS_BASE_URL/api/v1/contracts/CTR-2024-003" | python3 -m json.tool
```

Expected output:
```json
{
  "code": 0,
  "data": {
    "contract_number": "CTR-2024-003",
    "vendor_name": "Constructora XYZ",
    "monto_total": 15000000.00,
    "risk_score": 9.20,
    "risk_level": "CRITICO",
    "alertas": "Penalización excesiva del 15%. Garantía insuficiente. Sin cláusula de confidencialidad.",
    "recomendaciones": "Renegociar penalización. Aumentar garantía al 15%. Agregar cláusula de confidencialidad."
  }
}
```

```bash
# Call 3: Filter by risk level
curl -s -H "X-DataArts-Token: $DATAARTS_API_KEY" \
  "$DATAARTS_BASE_URL/api/v1/risk-results?risk_level=CRITICO" | python3 -m json.tool
```

## 3. Talking Points

**Opening (Spanish):**
> "Acabamos de ver cómo se analizan los contratos. Pero en una empresa del tamaño de AYCO, no basta con analizar — necesitamos gobernar los datos. Necesitamos trazabilidad, calidad, y una forma segura de compartir estos datos con los sistemas que los necesitan."

**While showing Data Connections:**
> "DataArts Studio nos permite conectar todas nuestras fuentes de datos — DLI para procesamiento Spark, DWS para analytics — y ver todo desde un solo lugar. Estas conexiones son la base de todo el pipeline."

**While showing ETL Pipeline:**
> "Aquí tenemos el pipeline de ETL: primer nodo parsea los datos crudos desde OBS, segundo nodo carga los datos transformados a DWS, y tercer nodo ejecuta checks de calidad. Si algún check falla, el pipeline se detiene y nos alerta. Esto nos garantiza que nunca vamos a tomar decisiones con datos incorrectos."

**While calling REST API:**
> "Y lo mejor: DataArts expone estos datos como APIs REST listas para consumo. El equipo legal puede consultar los contratos de alto riesgo desde su sistema. El equipo financiero puede obtener los resultados directamente. Sin escribir una sola línea de SQL, sin dar acceso directo a la base de datos."

**Closing (Spanish):**
> "DataArts nos da control total: sabemos de dónde vienen los datos, cómo se transforman, si son de calidad, y quién los consume. Eso es gobernanza de datos de verdad."

## 4. Expected Output

- DataArts workspace dashboard showing 2 active connections
- ETL pipeline DAG visible with 3 nodes
- Pipeline execution completes with status: `SUCCESS`
- 3 REST API calls return JSON responses with correct data
- Total demo time: ~7 minutes

## 5. Backup Plan

| Failure Scenario | Backup Action |
|---|---|
| DataArts instance not responding | Show pre-recorded screenshots of DataArts console |
| ETL pipeline fails | Use `backports/demo2-etl-output.txt` with pre-captured output |
| DataService API returns 500 | Use pre-recorded curl output in `backports/demo2-api-outputs.json` |
| Data connections not configured | Show Terraform output proving connections are defined |

To switch to backup:
```bash
# Show pre-recorded API responses
cat backports/demo2-api-outputs.json | python3 -m json.tool
```

## 6. Transition to Demo 3

**Transition (Spanish):**
> "Ya tenemos el pipeline de datos funcionando, los contratos analizados, los resultados gobernados y expuestos como APIs. Ahora viene lo más interesante: ¿cómo le damos a los usuarios de negocio una forma natural de consultar toda esta información? Sin SQL, sin dashboards complicados. Con lenguaje natural. Vamos a ver nuestro chatbot de IA."

---

# Demo 3: Contract AI + Dify Chatbot (22-35 min)

## 1. Pre-demo Setup

- Dify deployed on ECS instance `s6.large.2` (confirmed via `make status`)
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
  --bucket ayco-contracts-input \
  --key contrato-demo-nuevo.pdf \
  --file ./data/sample-contracts/contrato-demo-nuevo.pdf
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
terraform output -raw dws_admin_password      # DWS password (via 1Password)
terraform output -raw obs_bucket_name         # OBS bucket
terraform output -raw dataarts_workspace_id   # DataArts workspace

# All outputs
terraform output
```

## Appendix B: Environment Variables

```bash
# Source before demo
export DWS_ENDPOINT=$(cd /home/eduardo/dev/ayco-huawei-cloud/terraform && terraform output -raw dws_endpoint)
export DWS_ADMIN_PASSWORD=$(op read "op://Huawei/DWS/admin_password")
export DIFY_PUBLIC_IP=$(cd /home/eduardo/dev/ayco-huawei-cloud/terraform && terraform output -raw dify_public_ip)
export DEEPSEEK_API_KEY=$(op read "op://DeepSeek/API/key")
export OBS_BUCKET="ayco-contracts-input"
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
| Contract parser | `terraform/modules/ai-ocr/functions/parse_contract.py` |
| LLM inference | `terraform/modules/ai-ocr/functions/llm_inference.py` |
| OCR trigger | `terraform/modules/ai-ocr/functions/ocr_trigger.py` |
| Health check | `scripts/health-check.sh` |
| Backup recordings | `scripts/backup-record-demos.sh` |
| Dify setup | `scripts/setup-dify.sh` |
| KB indexing | `scripts/index-knowledge-base.py` |
| Contract data gen | `scripts/generate-contract-data.py` |
| Upload to OBS | `scripts/upload-contracts-to-obs.sh` |
| DataArts test | `scripts/test-dataarts-api.sh` |
| Financial data gen | `scripts/generate-test-data.py` |
