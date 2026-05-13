# AYCO Demo Script — 3 Actos Narrativos

**Duración:** 15 minutos | **Audiencia:** Dirección General / Comités de Crédito y Cobranza
**Fecha:** Mayo 2026 | **URL Demo:** http://ayco-dashboard.hwcdemo.com (frontend) — Dify: http://101.44.185.139 (consola)

> "Lo que van a ver hoy corre 100% sobre Huawei Cloud — misma infraestructura física en México (la-north-2), sin depender de servicios de terceros."

---

## Prólogo (1 min)

**Qué decir:**
"Hoy en AYCO manejan crédito y cobranza — dos caras de la misma moneda. Les voy a mostrar cómo Huawei Cloud acelera las tres interacciones más frecuentes: el cliente que pregunta sobre su crédito, el ejecutivo que gestiona una cobranza, y el analista que procesa documentos. Tres apps, una plataforma."

**Dashboard abierto en monitor auxiliar:**
- Mostrar http://101.44.185.139:8501 con los KPIs de riesgo visibles
- Señalar: "Este dashboard lo corremos en el mismo servidor que las apps, 0 licencias, 0 infraestructura extra."

---

## Acto 1 — FAQ Chatbot (4 min)

**Escena:** Un cliente quiere saber sobre créditos personales

**App:** AYCO Chat — http://101.44.185.139 (primera app en el selector)

**Diálogo del demo:**

| Quién | Qué dice/hace |
|-------|--------------|
| **Demo** | "Empecemos con lo más simple: un cliente que pregunta. Sin呼叫 center, sin esperar." |
| **Escribe** | `Quiero saber qué requisitos necesito para un crédito personal` |
| **Respuesta esperada** | Documentación requerida, montos típicos, plazo, tasa — extraído del dataset FAQ |
| **Demo** | "Respuesta inmediata, con datos del catálogo real de AYCO. No es un chatbot genérico — está indexado con sus políticas." |
| **Escribe** | `¿Cuál es la diferencia entre crédito personal y automotriz?` |
| **Respuesta esperada** | Comparativa clara con tabla de diferencias |
| **Escribe** | `¿Puedo pagar por adelantado sin penalización?` |
| **Respuesta esperada** | Política de prepago del dataset, con condiciones |

**Qué señalar:**
- El chatbot responde en español mexicano, con contexto real de AYCO
- 17 documentos indexados en el knowledge base (FAQ, políticas, procedimientos)
- Corre sobre DeepSeek v4 via Huawei Cloud MaaS

**Transición → Acto 2:**
"Esto cubre al cliente que pregunta. Pero, ¿qué pasa cuando el cliente ya no responde? Ahí entra la cobranza inteligente."

---

## Acto 2 — Agent Cobranza (5 min)

**Escena:** Un ejecutivo de cobranza atiende un caso de mora

**App:** AYCO Cobranza Agent (segunda app en el selector)

**Diálogo del demo:**

| Quién | Qué dice/hace |
|-------|--------------|
| **Demo** | "Segundo escenario: un cliente con 45 días de atraso. El ejecutivo de cobranza necesita decidir rápido." |
| **Escribe** | `María García López tiene un crédito vencido de $15,000 con 45 días de atraso. ¿Qué plan le recomiendas?` |
| **Respuesta esperada** | El Agent consulta su knowledge base, analiza el perfil del cliente, y recomienda un plan específico (ej. Pagos Fijos a 6 meses con 0% interés). Muestra condiciones y riesgos. |
| **Demo** | "El agente consultó el catálogo de planes, evaluó el monto y los días de atraso, y recomendó el plan óptimo." |
| **Escribe** | `Aplica el plan de pagos fijos a 6 meses para ella, y genera la carta de cobranza administrativa` |
| **Respuesta esperada** | El Agent intenta usar las herramientas (aplicar_plan_pago, generar_carta_cobranza) y reporta los resultados con formato profesional |

**Qué señalar:**
- El Agent tiene 3 tools simuladas: aplicar plan, consultar buró, generar carta
- Piensa antes de responder — usa `function_call` strategy con DeepSeek
- Muestra el catálogo completo de planes de AYCO (Pagos Fijos, Reestructura, Liquidación con Quita, Emergencia)
- Dataset de cobranza con 5 documentos: proceso 4 etapas, políticas, negociación

**Transición → Acto 3:**
"Todo esto con datos estructurados. Pero AYCO recibe miles de documentos al mes — INEs, facturas, cartas. Hoy se leen a mano. Veamos cómo automatizarlo."

---

## Acto 3 — Document Analyzer (5 min)

**Escena:** Un analista procesa documentos escaneados

**App:** AYCO Document Analyzer (tercera app en el selector)

**Diálogo del demo:**

| Quién | Qué dice/hace |
|-------|--------------|
| **Demo** | "Este es el flujo más potente. Subo un documento — una imagen, un PDF — y en segundos tengo los datos extraídos y clasificados." |
| **Subir** | factura_credito.png (desde /tmp/ayco_docs/) |
| **Explicar** | "El documento pasa por OCR de Huawei Cloud — el mismo OCR que usa el gobierno chino para digitalizar documentos. Luego un modelo de lenguaje extrae los campos relevantes." |
| **Resultado** | JSON con tipo_documento: FACTURA, RFC, monto, concepto, fecha |
| **Demo** | "Pero el sistema no solo extrae — clasifica. Si subo un INE, el pipeline se adapta solo." |
| **Subir** | ine_frente.png |
| **Resultado** | JSON con tipo_documento: INE, nombre, CURP, domicilio, vigencia |
| **Demo** | "Y si es una carta de cobranza, también la reconoce." |
| **Subir** | carta_cobranza.png |
| **Resultado** | JSON con tipo_documento: CARTA_COBRANZA, deudor, monto, etapa |

**Arquitectura del pipeline (explicar mientras se procesa):**
1. Documento → OCR Huawei Cloud (General Text OCR)
2. Texto → Code node (clasifica tipo: FACTURA/INE/CARTA/ESTADO_CUENTA/CONTRATO)
3. Tipo + texto → LLM DeepSeek (extrae campos específicos según tipo)
4. Resultado → JSON estructurado listo para integrar al core bancario

**Qué señalar:**
- OCR de Huawei Cloud — zero third-party dependency
- Routing inteligente: el mismo pipeline maneja 5 tipos de documentos
- Procesamiento serverless — solo consume cuando se usa

---

## Cierre (30 seg)

"Aren vieron en 15 minutos lo que a un equipo de desarrollo toma semanas:
- Un chatbot que responde con las políticas reales de AYCO
- Un agente de cobranza que recomienda planes y ejecuta acciones  
- Un pipeline de documentos que clasifica y extrae datos automáticamente

Todo corriendo sobre Huawei Cloud México — sin depender de OpenAI, Google o AWS. La plataforma es suya, los datos son suyos, el modelo está en su región."

---

## Datos Técnicos de Referencia

| Recurso | Detalle |
|---------|---------|
| **URL Dify** | http://101.44.185.139 |
| **Dashboard** | http://101.44.185.139:8501 |
| **Login admin** | eduardo@ayco-demo.com / ver 1Password |
| **API Chat** | app-Y8MxfRygyUWOAfyTlo1MQSJx |
| **API Agent** | app-ZrM7Pal6G2b89drd1zLVssvM |
| **API Workflow** | app-mGyFcdX7vT3CZDDsvttCX6iF |
| **ECS** | s6.xlarge.2 (4vCPU/8GB), la-north-2 |
| **Modelo** | DeepSeek V4 Pro (via API directa, fallback) |
| **OCR** | Huawei Cloud General Text OCR, proxy :8300 |
| **Docs prueba** | /tmp/ayco_docs/ (factura_credito.png, ine_frente.png, carta_cobranza.png, estado_cuenta.png) |

## Plan B (si algo falla)

| Falla | Plan B |
|-------|--------|
| Dify no carga | Mostrar dashboard + screenshots pre-grabados |
| OCR timeout | Usar documento de texto directo (.txt) sin OCR |
| DeepSeek lento | Cambiar a DeepSeek V4 Flash (más rápido) |
| Internet cae | Demo local con documentos pre-procesados |
