# AYCO Contract Risk Analysis — Demo Script (v2: Branded Frontend)

**Workshop:** Huawei Cloud LATAM × Grupo Salinas (AYCO)
**Date:** May 8, 2026
**Duration:** 45 min total (0-5 PPT, 5-15 Demo 1, 15-25 Demo 2, 25-38 Demo 3, 38-41 ROI/FinOps, 41-45 Q&A)
**Region:** la-north-2 (Mexico City 2)
**Audience:** Huawei Cloud LATAM Leadership
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
| **Dify Admin** | `http://101.44.185.139/admin` | Solo si se necesita mostrar config interna |
| **Langfuse** | `https://cloud.langfuse.com` → ayco-demo | Observabilidad LLM |

---

## Pre-Workshop Checklist (complete by May 7, 6 PM)

- [ ] Run `make demo` and verify all services are healthy
- [ ] Run `bash scripts/health-check.sh` — all checks must pass
- [ ] **Frontend accessible:** `curl -s http://149.232.129.39/` returns 200
- [ ] **Chatbot functional:** Open `http://149.232.129.39/contract-ai/` → click quick action → response streams
- [ ] Confirm Dify is accessible at ECS public IP, port 80
- [ ] Confirm DWS endpoint responds (PG client test)
- [ ] Confirm DataArts Studio instance is running in Huawei Console
- [ ] Run `python3 scripts/generate-contract-data.py` to generate 20 seed contracts
- [ ] Upload 20 contract PDFs/TXTs to OBS bucket `ayco-contracts-raw`
- [ ] Have Huawei Console tabs open and pinned: OBS, FunctionGraph, DLI, DWS, DataArts, ECS/Dify
- [ ] Verify DeepSeek API key is valid: `curl -H "Authorization: Bearer $DEEPSEEK_API_KEY" https://api.deepseek.com/v1/models`
- [ ] Run `bash scripts/langfuse-setup.sh` and verify Langfuse dashboard displays traces
- [ ] Open Langfuse dashboard tab: https://cloud.langfuse.com → project ayco-demo (pinned)
- [ ] Confirm DataArts Catalog metadata collection task executed (lineage graph populated)
- [ ] **Browser tabs pinned (in order):**
  1. `http://149.232.129.39/` (Landing — punto de partida)
  2. `http://149.232.129.39/risk-scoring/` (Demo 1)
  3. `http://149.232.129.39/data-governance/` (Demo 2)
  4. `http://149.232.129.39/contract-ai/` (Demo 3 — principal)
  5. Huawei Console > DataArts Studio (para mostrar gobernanza interna)
  6. Langfuse Cloud > ayco-demo
  7. Huawei Console > FunctionGraph (logs OCR en vivo)

---

## Cómo Funciona el Frontend (Referencia Rápida)

El frontend branded es un sitio estático (Astro + Tailwind) servido por nginx en el ECS `ayco-web` (149.232.129.39). Reemplaza la UI raw de Dify con la identidad visual de Grupo Salinas.

**Arquitectura del frontend:**
```
Navegador del presentador
    │
    ▼
http://149.232.129.39/          ← nginx sirve HTML/CSS/JS estáticos
    │
    ├── /                       ← Landing: hero + 3 cards de demo + KPIs
    ├── /risk-scoring/          ← Demo 1: gauge + tabla + pipeline visual
    ├── /data-governance/       ← Demo 2: ETL steps + API explorer + calidad
    └── /contract-ai/           ← Demo 3: uploader + chatbot + contratos
            │
            │ (chat widget usa fetch() con SSE streaming)
            ▼
    http://149.232.129.39/api/dify/*   ← nginx reverse proxy
            │
            ▼
    http://101.44.185.139/v1/*         ← Dify API (ECS interno)
```

**Componentes clave del frontend:**
- **Header:** Logo Grupo Salinas + navegación entre demos. Sticky arriba.
- **ChatWidget:** Botón flotante (esquina inferior derecha) en TODAS las páginas. Habla con Dify API vía SSE streaming. Se abre/cierra con click.
- **RiskGauge:** SVG animado que muestra score 0-10 con colores (verde/amarillo/rojo/crítico). Se anima al hacer scroll.
- **ContractUploader:** Drag & drop de PDFs. Simula pipeline OCR → Parse → IA → Score con barra de progreso.
- **PipelineDiagram:** Flujo visual de cada pipeline (3 variantes: risk, governance, contract).
- **MetricCard:** KPIs animados con trend indicators.

---

# Demo 1: Risk Scoring with DLI + DWS (5-15 min)

## Runtime Flow — Cómo Interactuar con el Dashboard

### Paso 0: Punto de partida (30s)

El demo arranca en la **Landing** (`http://149.232.129.39/`).

**Qué hacer:**
1. Abre la Landing en el navegador.
2. Señala el hero con el tagline: "Inteligencia Artificial para la Gestión de Riesgo Financiero".
3. Menciona: "Esto es la interfaz de AYCO construida sobre Huawei Cloud. Todo lo que van a ver corre en la nube de Huawei — la-north-2, Ciudad de México."
4. Haz scroll lentamente para mostrar los 4 KPIs animados (proveedores analizados, reducción de tiempo, costo diario, minutos por análisis).
5. Señala las 3 cards de demo: Risk Scoring, Data Governance, Contract AI.

**🎤 Speaker:**
> "Esta es la plataforma completa de AYCO. No vamos a ver consolas de Huawei ni interfaces de desarrollo — vamos a ver lo que el usuario final ve. Identidad de Grupo Salinas, datos en tiempo real, inteligencia artificial integrada. Empecemos por Risk Scoring."

6. Click en la card **"Risk Scoring"** → navega a `/risk-scoring/`.

---

### Paso 1: Risk Scoring — Pipeline Visual (1 min)

**URL:** `http://149.232.129.39/risk-scoring/`

**Qué hacer:**
1. La página carga con el header navy y el breadcrumb: "Inicio / Demo 1".
2. Señala el **PipelineDiagram** en la parte superior: muestra el flujo visual:
   ```
   📊 Datos CNBV → ⚡ DLI Spark → 🗄️ DWS → 📈 Dashboard
   ```
3. Explica que este pipeline corre automáticamente cada vez que hay nuevos datos.

**🎤 Speaker:**
> "El pipeline de riesgo empieza con datos de transacciones y proveedores. DLI Spark agrega y correlaciona, DWS almacena, y este dashboard muestra los resultados. Todo orquestado en Huawei Cloud."

---

### Paso 2: KPIs Animados (1 min)

**Qué hacer:**
1. Haz scroll hacia abajo para revelar los 4 MetricCards.
2. Los números se animan al entrar en viewport (IntersectionObserver).
3. Señala cada uno:
   - **2,347 Proveedores Activos** (+5.2% este mes)
   - **5,128 Transacciones Analizadas** (+18% vs mes anterior)
   - **47 Alertas CNBV Activas** (12 críticas) — este tiene color rojo
   - **$2.1B MXN Exposición Total** (-3.4% reducción)

**🎤 Speaker:**
> "Estos son los KPIs en tiempo real conectados a nuestro data warehouse en DWS. 2,300 proveedores analizados, 5,000 transacciones procesadas, y 47 alertas activas de la CNBV. La exposición total es de 2,100 millones de pesos."

---

### Paso 3: Risk Gauge + Distribución (2 min)

**Qué hacer:**
1. Sigue haciendo scroll. Aparece la sección con 2 columnas:
   - **Izquierda:** Placeholder del dashboard Grafana (o Streamlit embebido si está configurado). Menciona que aquí va el dashboard interactivo.
   - **Derecha:** El **RiskGauge** grande con score 5.8 (Riesgo Global). Se anima al entrar en viewport — el arco se llena de naranja.
2. Debajo del gauge, muestra la distribución por nivel:
   - Bajo (0-3): 847 proveedores (verde)
   - Medio (3-5): 1,024 proveedores (amarillo)
   - Alto (5-7): 389 proveedores (rojo)
   - Crítico (7-10): 87 proveedores (marrón oscuro)

**🎤 Speaker:**
> "Este gauge muestra el riesgo promedio de toda la cartera de proveedores: 5.8 sobre 10. En rojo vemos 389 proveedores de alto riesgo y 87 críticos que requieren atención inmediata. Esto se actualiza en tiempo real conforme el pipeline procesa nuevos contratos."

---

### Paso 4: Tabla de Top Proveedores (1 min)

**Qué hacer:**
1. Sigue scroll. Aparece la tabla "Top 5 Proveedores de Mayor Riesgo".
2. Señala las columnas: Proveedor, Estado, Score, Exposición, Alertas.
3. Los scores tienen badges de color (crítico = badge rojo oscuro, alto = badge rojo claro).

**Datos de la tabla:**
| Proveedor | Estado | Score | Exposición | Alertas |
|-----------|--------|-------|------------|---------|
| Constructora Delta MX | Nuevo León | 8.7 (crítico) | $385M | 3 |
| Servicios Integrales SA | Jalisco | 8.2 (alto) | $290M | 2 |
| TechSupply Corp | CDMX | 7.9 (alto) | $210M | 4 |
| Logística Nacional | Estado de México | 7.5 (alto) | $175M | 1 |
| Materiales del Bajío | Guanajuato | 7.1 (alto) | $140M | 2 |

**🎤 Speaker:**
> "Aquí vemos los 5 proveedores más riesgosos. Constructora Delta en Nuevo León tiene un score de 8.7 con 3 alertas activas y una exposición de 385 millones de pesos. Si hacen click en cualquier fila, pueden ver el detalle del contrato."

---

### Paso 5: Transición a Huawei Console (opcional, 1 min)

**Qué hacer (si hay tiempo):**
1. Abre una nueva tab con Huawei Console > DWS.
2. Muestra la tabla `risk_results` con los datos reales.
3. Ejecuta una query rápida para mostrar que los datos del dashboard vienen de aquí.

**🎤 Speaker:**
> "Todo lo que vieron en el dashboard viene de DWS — nuestro data warehouse en Huawei Cloud. Los mismos datos, consultados con SQL estándar. En producción, el dashboard se conecta directamente aquí."

**Transición a Demo 2:**
> "Ya vimos cómo se analiza el riesgo. Ahora la pregunta es: ¿cómo gobernamos todo este pipeline? ¿Cómo garantizamos calidad y seguridad? Vamos a Data Governance."

---

# Demo 2: Data Governance & Intelligence (15-25 min)

## Runtime Flow — Cómo Interactuar con el Dashboard

### Paso 0: Navegar a Data Governance (15s)

**Desde el Risk Scoring:**
1. Click en "Data Governance" en el header de navegación.
2. O click "Inicio" → card "Data Governance".

**URL:** `http://149.232.129.39/data-governance/`

---

### Paso 1: Pipeline ETL Visual (1 min)

**Qué hacer:**
1. La página carga con header verde esmeralda (diferenciación visual del Demo 1).
2. Señala el **PipelineDiagram** variante "governance":
   ```
   📁 OBS Storage → 🔄 DataArts ETL → 🗄️ DWS Target → 🌐 DataService API
   ```
3. Explica el flujo: datos crudos en OBS, transformación en DataArts, carga a DWS, exposición como API.

**🎤 Speaker:**
> "El pipeline de gobernanza toma datos crudos de OBS, los transforma con DataArts Studio, los carga a DWS con validaciones de calidad, y los expone como APIs REST gobernadas. Vamos a ver cada etapa."

---

### Paso 2: ETL Steps Detallados (2 min)

**Qué hacer:**
1. Haz scroll. Aparecen 5 cards apiladas, cada una representando una etapa del ETL:
   - **Extract** (📥) — Lectura desde OBS (CSV, JSON, PDFs) ✓ Completado
   - **Transform** (🔄) — Limpieza, normalización CNBV, deduplicación ✓ Completado
   - **Validate** (✅) — Reglas de calidad: nulos, rangos, consistencia ✓ Completado
   - **Load** (📤) — Escritura a DWS con particionamiento ✓ Completado
   - **Publish** (🌐) — DataService API REST con cache y rate limiting ● Activo (parpadea)
2. Cada card tiene un indicador de estado: check verde (completado) o spinner azul (activo).
3. Señala que "Publish" está activo — la API está sirviendo requests en tiempo real.

**🎤 Speaker:**
> "5 etapas, cada una validada. Extract lee de OBS, Transform normaliza los datos con estándares CNBV, Validate ejecuta 5 reglas de calidad — si alguna falla, el pipeline se detiene. Load escribe a DWS con particionamiento por fecha. Y Publish expone todo como API REST. El punto azul parpadeante significa que la API está activa ahora mismo."

---

### Paso 3: DataService API Explorer (2 min)

**Qué hacer:**
1. Scroll. Aparece la sección "DataService API" con un indicador verde "API en vivo" y la URL base.
2. Debajo hay una tabla con 5 endpoints:

| Method | Path | Descripción | Status | Latencia |
|--------|------|-------------|--------|----------|
| GET | `/api/v1/vendors` | Lista de proveedores con scores | 200 OK | 45ms |
| GET | `/api/v1/vendors/{id}/risk` | Detalle de riesgo por proveedor | 200 OK | 32ms |
| GET | `/api/v1/transactions` | Transacciones con anomalías CNBV | 200 OK | 58ms |
| POST | `/api/v1/analyze` | Análisis on-demand de contrato | 201 Created | 4.2s |
| GET | `/api/v1/alerts` | Alertas activas de compliance | 200 OK | 28ms |

3. Señala que GET tiene badge verde y POST tiene badge azul.
4. Las latencias están en la columna derecha — todas bajo 100ms excepto el análisis on-demand (4.2s porque invoca el LLM).

**🎤 Speaker:**
> "Estos son los 5 endpoints de la DataService API. Cualquier aplicación interna de AYCO puede consumir estos datos sin saber SQL, sin acceso a DWS. Solo necesita un token. Fíjense en las latencias: 45 milisegundos para listar proveedores, 28 para alertas. El análisis on-demand tarda 4 segundos porque invoca DeepSeek en vivo."

---

### Paso 4: Métricas de Calidad de Datos (1 min)

**Qué hacer:**
1. Scroll. Aparecen 3 cards de métricas de calidad:
   - **Completitud:** 98.7% (campos no nulos vs total) — barra verde casi llena
   - **Consistencia:** 99.2% (reglas de negocio válidas) — barra verde casi llena
   - **Freshness:** <5min (latencia de datos actualizados) — barra azul
2. Cada card tiene una barra de progreso visual.

**🎤 Speaker:**
> "Gobernanza de datos sin métricas es marketing. Aquí vemos los números reales: 98.7% de completitud, 99.2% de consistencia, y los datos se actualizan cada 5 minutos. Si algún indicador cae, se dispara una alerta."

---

### Paso 5: Transición a Huawei Console (opcional, 2 min)

**Qué hacer (si hay tiempo):**
1. Abre Huawei Console > DataArts Studio > Catalog.
2. Muestra el grafo de linaje: OBS → FunctionGraph → DLI → DWS → API.
3. Click en un nodo para mostrar linaje a nivel de campo.

**🎤 Speaker:**
> "DataArts nos da trazabilidad completa. Si un regulador pregunta '¿de dónde salió este risk score?', tenemos la respuesta en un click. Esto ningún otro cloud lo da integrado."

**Transición a Demo 3:**
> "Ya tenemos los datos gobernados. Pero ¿qué pasa cuando un usuario de negocio — sin saber SQL — quiere hacer preguntas? Ahí entra la IA. Vamos a Contract AI."

---

# Demo 3: Contract AI + Dify Chatbot (25-38 min)

Este es el **demo principal** — el que más tiempo tiene y el que debe impresionar.

## Runtime Flow — Cómo Interactuar con el Dashboard

### Paso 0: Navegar a Contract AI (15s)

**Desde Data Governance:**
1. Click en "Contract AI" en el header.

**URL:** `http://149.232.129.39/contract-ai/`

---

### Paso 1: Pipeline de Análisis (30s)

**Qué hacer:**
1. La página carga con header ámbar/dorado (diferenciación visual).
2. Señala el **PipelineDiagram** variante "contract":
   ```
   📄 PDF Upload → 👁️ OCR → 🧠 DeepSeek MaaS → 📊 Score
   ```
3. Mención rápida: "PDF entra, score de riesgo sale. Todo automatizado."

---

### Paso 2: Contract Uploader — Demo en Vivo (3 min)

**Qué hacer:**
1. Scroll. Aparecen dos columnas:
   - **Izquierda:** Zona de drag & drop "Arrastra un contrato PDF aquí"
   - **Derecha:** Chatbot con preguntas rápidas pre-definidas
2. **Arrastra un PDF** de la carpeta `data/contracts/` a la zona de upload (o haz click para seleccionar).
3. Observa la animación de procesamiento:
   - Barra de progreso se llena en 4 pasos:
     - "Extrayendo texto con OCR..." (20%)
     - "Analizando cláusulas contractuales..." (45%)
     - "Evaluando riesgo con IA..." (70%)
     - "Generando reporte..." (90%)
4. El resultado aparece con:
   - Un **RiskGauge** animado con el score (ej: 7.4)
   - Nombre del archivo procesado
   - Badge de nivel de riesgo (Alto/Medio/Bajo/Crítico)
   - Texto: "Score: 7.4/10 · Procesado con OCR + DeepSeek v4 Flash"
5. Click en "Analizar otro contrato" para repetir con otro PDF.

**🎤 Speaker:**
> "Vamos a subir un contrato en vivo. Arrastro el PDF... y en 4 segundos el pipeline completo se ejecuta: OCR extrae el texto, DeepSeek analiza las cláusulas, y aquí tienen el resultado. Score 7.4, riesgo alto, con los factores identificados. Sin SQL, sin consola, sin programación. Esto es lo que el usuario de negocio ve."

---

### Paso 3: Chatbot RAG — Interacción (5 min)

**Este es el wow factor del demo completo.**

**Qué hacer:**
1. En la columna derecha de la página, hay 3 botones de preguntas rápidas:
   - "Analizar contrato AYCO-2026-0147 y dime los principales riesgos"
   - "Compara las cláusulas de penalización entre los 3 contratos"
   - "¿Qué proveedores tienen exposición superior a $500M MXN?"

2. **Haz click en la primera pregunta.** Esto:
   - Abre el **ChatWidget** (botón flotante esquina inferior derecha) automáticamente
   - Envía la pregunta a Dify API vía `/api/dify/chat-messages`
   - La respuesta se **stremea** en tiempo real (SSE) — el texto aparece carácter por carácter

3. **Mientras la respuesta se genera**, señala:
   - El header del chat: "AYCO — Asistente de Contratos" con indicador "En línea"
   - Las quick actions debajo del input (3 botones pre-definidos)
   - El cursor parpadeante mientras se genera la respuesta

4. **Lee la respuesta en voz alta** (debería mencionar el contrato AYCO-2026-0147 con score 8.7, penalización 30%, sin garantía, etc.)

5. **Haz click en la segunda pregunta** ("Compara las cláusulas de penalización..."). El chatbot debe comparar los 3 contratos de demo.

6. **Escribe una pregunta manual** en el input del chat:
   - "¿Qué recomiendas para mitigir el riesgo del contrato más crítico?"
   - Enter → la respuesta se stremea en vivo

7. **Click en el ícono de "Nueva conversación"** (esquina superior derecha del chat) para reiniciar.

**🎤 Speaker (mientras el chat genera la respuesta):**
> "Esto es RAG — Retrieval-Augmented Generation. El chatbot busca en la base de conocimiento de contratos indexados, encuentra los más relevantes, y genera una respuesta estructurada con datos reales. No está inventando — está citando los resultados del análisis de riesgo que vimos en el Demo 1. Todo esto corre con DeepSeek v4 Flash a través de Huawei MaaS."

**Mientras muestra el chat:**
> "Fíjense que la respuesta incluye el número de contrato, el score, las alertas específicas, y recomendaciones accionables. Un analista humano tardaría horas en hacer este análisis. El modelo lo hace en 4 segundos."

---

### Paso 4: Contratos Pre-analizados (1 min)

**Qué hacer:**
1. Scroll hacia abajo en la página de Contract AI.
2. Aparecen 3 cards con los contratos de demo ya analizados:
   - **AYCO-2026-0147** — Constructora Delta MX — Score 8.7 (Alto Riesgo) — $3.85M MXN
   - **AYCO-2026-0148** — Servicios Logísticos SA — Score 2.3 (Bajo Riesgo) — $450K MXN
   - **AYCO-2026-0149** — TechGlobal Corp — Score 9.2 (Crítico) — $12.5M MXN
3. Cada card tiene su propio RiskGauge pequeño y lista de factores de riesgo.
4. Señala los factores: penalización, garantía, arbitraje, jurisdicción.

**🎤 Speaker:**
> "Estos son los 3 contratos canónicos de demo. El crítico tiene score 9.2 — penalización del 40%, sin límite de responsabilidad, arbitraje UNCITRAL. El bajo riesgo tiene penalización del 5% con garantía del 20% y arbitraje ICC. El modelo los distingue perfectamente."

---

### Paso 5: Observabilidad LLM (1 min)

**Qué hacer:**
1. Scroll. Aparece la sección "Observabilidad LLM" con 4 métricas:
   - Traces Hoy: 127
   - Latencia Media: 3.8s
   - Tokens Totales: 45.2K
   - Tasa de Éxito: 99.1%
2. Debajo hay un placeholder para el dashboard de Langfuse embebido.
3. Si hay tiempo, abre la tab de Langfuse Cloud para mostrar las trazas reales.

**🎤 Speaker:**
> "Cada llamada al modelo está trazada en Langfuse. 127 traces hoy, latencia media de 3.8 segundos, 99.1% de tasa de éxito. Si el modelo empieza a alucinar, lo detectamos inmediatamente. Langfuse es open-source, sin vendor lock-in."

---

### Paso 6: Preguntas en Vivo del Audience (2 min)

**Qué hacer:**
1. Abre el chat widget (botón flotante).
2. Invita al audience a hacer preguntas.
3. Escribe la pregunta del audience en el input y muestra la respuesta en vivo.

**Preguntas sugeridas si el audience no pregunta:**
- "¿Cuál es el contrato con mayor penalización?"
- "¿Qué cláusulas debo revisar antes de firmar con un proveedor nuevo?"
- "Dame un resumen ejecutivo de todos los contratos críticos"

**🎤 Speaker:**
> "¿Alguna pregunta? Escriban lo que quieran saber sobre los contratos y el chatbot les responde en vivo."

---

# ROI + Cierre (38-41 min)

**Transición:**
> "En 35 minutos vimos una plataforma completa: scoring de riesgo con DLI y DWS, gobernanza de datos con DataArts, y análisis inteligente con DeepSeek. Todo corriendo en Huawei Cloud, con la interfaz de AYCO. Déjenme mostrarles el impacto."

**Vuelve a la Landing** (`http://149.232.129.39/`) y señala los KPIs del hero:

| Métrica | Antes | Después |
|---------|-------|---------|
| Tiempo de análisis | 3 días | 4 minutos |
| Costo diario infra | N/A | $35 USD/día |
| Proveedores analizados | Manual | 2,300+ automatizados |
| Precisión de scoring | Subjetivo | 99.1% tasa de éxito LLM |

**🎤 Speaker:**
> "De 3 días a 4 minutos. De análisis subjetivo a scoring con IA. De $0 a $35 dólares al día de infraestructura. Esto es lo que Huawei Cloud permite hacer con DLI, DWS, DataArts, FunctionGraph, y MaaS. Todo en la nube, todo en México, todo gobernado."

---

# Q&A (41-45 min)

Abre el chat widget y el audience puede hacer preguntas técnicas.

---

# Backup Plan (Global)

| Fallo | Acción de respaldo |
|-------|-------------------|
| Frontend no carga (149.232.129.39 down) | Mostrar Dify directo en `http://101.44.185.139` + Huawei Console |
| Chatbot no responde | Usar `backports/demo3-chat-outputs.txt` con respuestas pre-grabadas |
| Dify API timeout | Cambiar a DeepSeek directo (`api.deepseek.com`) o usar respuestas cached |
| Dashboard no carga | Mostrar queries SQL directas en psql contra DWS |
| FunctionGraph falla | Usar `backports/demo1-llm-response.json` con respuesta pre-grabada |
| DataArts no accesible | Mostrar Terraform code como proof de que los recursos existen |
| Langfuse no carga | Mostrar código de integración Langfuse como proof |
| Internet del venue falla | Tener grabaciones de pantalla con `scripts/backup-record-demos.sh` |

**Para activar backup:**
```bash
# Grabar dry-run completo antes del evento
bash scripts/backup-record-demos.sh

# Reproducir en caso de fallo
bash scripts/backup-record-demos.sh --play demo1
bash scripts/backup-record-demos.sh --play demo2
bash scripts/backup-record-demos.sh --play demo3
```

---

## Appendix: Quick Reference — Comandos SSH

```bash
# Conectar al Dify ECS
ssh -i ~/.ssh/ayco-demo root@101.44.185.139

# Conectar al Web ECS (frontend)
ssh -i ~/.ssh/ayco-demo root@149.232.129.39

# Verificar Dify
ssh -i ~/.ssh/ayco-demo root@101.44.185.139 "cd /opt/dify/docker && docker compose ps"

# Verificar frontend
curl -s -o /dev/null -w "%{http_code}" http://149.232.129.39/

# Verificar chatbot proxy
curl -s -X POST http://149.232.129.39/api/dify/chat-messages \
  -H "Authorization: Bearer app-Y8MxfRygyUWOAfyTlo1MQSJx" \
  -H "Content-Type: application/json" \
  -d '{"query":"test","user":"healthcheck","response_mode":"blocking","inputs":{}}'

# Rebuild y redeploy frontend
cd /home/eduardo/dev/ayco-huawei-cloud/frontend
npm run build && bash deploy.sh

# Dify API keys (en PostgreSQL de Dify)
ssh -i ~/.ssh/ayco-demo root@101.44.185.139 \
  "docker exec docker-db_postgres-1 psql -U postgres -d dify \
   -c \"SELECT a.name, t.token FROM api_tokens t JOIN apps a ON t.app_id = a.id WHERE t.type='app';\""
```

---

**File:** `docs/demo-script.md`
**Version:** v2.0 — Branded Frontend
**Last updated:** May 5, 2026
