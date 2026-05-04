# AYCO — Huawei Cloud Infrastructure

> **Workshop Mayo 8, 2026** — Mexico Century Plaza
> **Región:** la-north-2 (Mexico City 2)
> **Principio:** make demo → todo listo

## Quick Start

```bash
# 1. Configurar credenciales
cp .env.example .env
# Editar .env con AK/SK + DeepSeek API key

# 2. Desplegar todo
make demo

# 3. Verificar
make status
```

## Estructura

```
terraform/          # Infraestructura declarativa (4 módulos)
scripts/            # Automatización complementaria
data/               # Datos sintéticos para demo
dashboards/         # Configuraciones de dashboards DWS
```

## Requisitos

- Terraform >= 1.5
- huaweicloud provider >= 1.72.0
- Docker (para Dify en ECS)
- Python 3.10+ (para generate-test-data.py)
- 1Password CLI (op read para credenciales)
- make
