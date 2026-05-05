# DLI + DataArts — Demo Documentation

## DLI Status (FIXED 2026-05-05)

### Infrastructure
| Component | Status | Details |
|-----------|--------|---------|
| Database | `ayco_contracts` | Created via Terraform |
| Queue | `default` (serverless) | Dedicated queue sold out in la-north-2 |
| Table: risk_results | ✓ Active | 20 records, JSON from `obs://ayco-contracts-results/json/` |
| Table: contracts_raw | ✓ Active | 23 records, JSON from `obs://ayco-contracts-text/json/` |

### Key Fix: OBS Data Layout
DLI external tables read ALL files in the specified path. If non-JSON files (CSV, Python)
exist at the same path, DLI silently returns NULL for all fields.

**Solution:** Data organized into `json/` subdirectories in each OBS bucket:
```
obs://ayco-contracts-results/
├── json/                    ← DLI reads this (JSON only)
│   ├── AYCO-2026-0147.json
│   ├── AYCO-2026-0148.json
│   └── ... (20 files)
├── risk_results.csv         ← ignored by DLI
└── spark/                   ← ignored by DLI
    └── risk_aggregation.py

obs://ayco-contracts-text/
├── json/                    ← DLI reads this (JSON only)
│   ├── contrato-01-alto-riesgo.json
│   ├── contrato-2026-0001.json
│   └── ... (23 files)
├── contrato-01-alto-riesgo.txt  ← raw text (OBS direct access)
└── contrato-2026-0001.txt       ← raw text (OBS direct access)
```

### Key Fix: Text Files → JSON
DLI only supports PARQUET/ORC/JSON/CSV/HUDI/DELTA. Plain TEXT is not supported.

**Solution:** Text files wrapped as single-record JSON:
```json
{
  "file_name": "contrato-01-alto-riesgo.txt",
  "contract_id": "CONTRATO NÚMERO: AYCO-2026-0147",
  "content": "Full contract text...",
  "char_count": 5025
}
```

### Demo Queries (Spark SQL)

**Risk Distribution:**
```sql
SELECT risk_level, COUNT(*) as cnt, ROUND(AVG(risk_score),1) as avg_score
FROM risk_results
WHERE risk_level IS NOT NULL
GROUP BY risk_level
ORDER BY avg_score DESC;
```
Expected: CRITICO(1,9.0), ALTO(10,6.4), MEDIO(3,4.0), BAJO(6,1.5)

**Top 5 Riskiest Contracts:**
```sql
SELECT contract_number, vendor_name, risk_score, risk_level,
       ROUND(monto_total/1000000.0, 1) as monto_m
FROM risk_results
WHERE risk_level IS NOT NULL
ORDER BY risk_score DESC LIMIT 5;
```

**Contract Text Search:**
```sql
SELECT file_name, contract_id, char_count
FROM contracts_raw
ORDER BY char_count DESC LIMIT 5;
```

---

## DataArts Status (NOT PROVISIONED)

DataArts workspace was not provisioned due to monthly billing commitment.
For the demo, use Huawei Cloud Console screenshots to show the data governance pipeline.

### Screenshots Needed
1. DataArts workspace overview
2. Data catalog with AYCO tables
3. Quality rules dashboard
4. Data lineage diagram (OBS → DLI → DWS)

### Demo Flow for Data Governance (Demo 2)
1. Show the branded frontend "Data Governance" page at http://149.232.129.39/data-governance/
2. PipelineDiagram component shows 5 ETL steps visually
3. DataService API Explorer shows live API calls
4. Quality metrics from DWS query results
5. **Transition:** "En producción, DataArts agrega governance automatizado."
