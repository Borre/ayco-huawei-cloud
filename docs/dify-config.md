# AYCO Dify Configuration — Reproducible Reference
**Last updated:** May 5, 2026

## Access
- **Dify UI:** http://101.44.185.139
- **Console API:** http://101.44.185.139/console/api
- **Service API:** http://101.44.185.139/v1
- **Login:** eduardo@ayco-demo.com / ver 1Password
- **SSH:** ssh -i ~/.ssh/ayco-demo root@101.44.185.139
- **Docker:** cd /opt/ayco/dify/docker && docker compose ps

## Apps
| App | DB ID | API Key | Mode | Model | Dataset |
|-----|-------|---------|------|-------|---------|
| AYCO Chat | 253ad7c8-1cd7-44ea-a27d-9d67f031e5a1 | app-Y8MxfRygyUWOAfyTlo1MQSJx | chat | deepseek-v4-pro | FAQ |
| AYCO Cobranza | 7e0472b6-249f-47bb-a2c1-cf298b7287f7 | app-ZrM7Pal6G2b89drd1zLVssvM | agent | deepseek-v4-pro | Cobranza+Planes |
| AYCO Analyzer | b7e99855-1fc9-4374-82c8-9a47693205d7 | app-mGyFcdX7vT3CZDDsvttCX6iF | workflow | OCR+DeepSeek | — |

## Datasets
| Dataset | DB ID | Docs | Contents |
|---------|-------|------|----------|
| FAQ | 369a7215... | 9 | Creditos, tarjetas, pago, solicitud |
| Cobranza | f78411c9... | 5 | Proceso, politica, negociacion, buro |
| Planes de Pago | 3cdc091b... | 5 | Pagos fijos, reestructura, quita |

## MaaS HK Fix
**Problem:** Plugin usa /v1 (legacy) + model names lowercase -> error 81009 "Invalid model".
**Fix (re-apply if plugin_daemon restarts):**
```bash
ssh root@101.44.185.139
docker exec docker-plugin_daemon-1 sed -i 's|/v1/chat/completions|/v2/chat/completions|g' /app/dify-plugin-maas-hk-0.0.16*/models/*.yaml
docker exec docker-plugin_daemon-1 sed -i 's|model: deepseek|model: DeepSeek|g' /app/dify-plugin-maas-hk-0.0.16*/models/*.yaml
docker compose -f /opt/ayco/dify/docker/docker-compose.yaml restart plugin_daemon
```
**Status:** MaaS HK no funciona (NXDOMAIN maas-api.la-north-2). DeepSeek directo es el fallback.

## Agent Tools Mock
- **Port:** 8400 (systemd: ayco-tools)
- **Endpoints:** /aplicar_plan_pago, /consultar_buro, /generar_carta, /health
- **DB registration:** tool_api_providers.id=78e524a4... + 3 label_bindings
- **Agent config:** app_model_configs.agent_mode includes tools array

## Workflow Routing
Document types detected: FACTURA, INE, CARTA_COBRANZA, ESTADO_CUENTA, CONTRATO
Code node parses OCR JSON + keyword classification -> LLM extracts type-specific fields.

## Key DB Queries
```sql
-- All tables
\dt
-- Apps with keys
SELECT id, name, mode FROM apps;
-- Datasets with doc counts
SELECT d.id, d.name, COUNT(de.id) FROM datasets d LEFT JOIN documents de ON d.id=de.dataset_id GROUP BY d.id, d.name;
-- Provider status
SELECT provider_name, is_valid FROM provider_credentials;
```

## Recovery: Full Restart
```bash
ssh root@101.44.185.139
cd /opt/ayco/dify/docker && docker compose restart api worker web
# Wait 15s
curl -s http://localhost/console/api/version?current_version=1.0.0
```
