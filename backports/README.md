# Backports — Plan B para AYCO Demo

Archivos pre-generados para usar como fallback si algo falla en vivo.

## Demo 1 — Risk Scoring
- `demo1-spark-output.txt` — Salida pre-capturada de DLI Spark
- `demo1-llm-response.json` — Respuesta pre-cacheada de DeepSeek

## Demo 2 — Data Governance
- `demo2-etl-output.txt` — Logs pre-capturados del pipeline DataArts
- `demo2-api-outputs.json` — Respuestas pre-capturadas de DataService API

## Demo 3 — Contract AI + Dify
- `demo3-chat-outputs.txt` — Respuestas pre-capturadas del chatbot

## Uso
```
# Mostrar en terminal durante el demo
cat backports/demo1-spark-output.txt
cat backports/demo2-api-outputs.json | python3 -m json.tool
cat backports/demo3-chat-outputs.txt
```
