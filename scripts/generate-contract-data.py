#!/usr/bin/env python3
"""scripts/generate-contract-data.py — Datos sintéticos de contratos para AYCO demo.

Genera:
1. risk_results.csv — 20 resultados de riesgo: 3 canónicos alineados a los PDFs + 17 sintéticos
2. contract_texts/ — 20 archivos .txt de contratos sintéticos (para OBS + Dify KB)
3. risk_summary.json — Resumen agregado (para dashboards)
"""

import csv
import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
CONTRACTS_DIR = DATA_DIR / "contracts"
TEXTS_DIR = DATA_DIR / "contract_texts"
RESULTS_DIR = DATA_DIR / "risk_results"

for d in [TEXTS_DIR, RESULTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

random.seed(42)  # Reproducible

# ─── Catálogos realistas ──────────────────────────────────────────
PROVEEDORES = [
    ("Constructora del Valle de México S.A. de C.V.", "CDMX", "Construcción"),
    ("Tecnologías Avanzadas del Norte S.A. de C.V.", "Monterrey", "Tecnología"),
    ("Servicios Integrales de Ingeniería S.A. de C.V.", "Guadalajara", "Construcción"),
    ("Grupo Industrial Minero S.A. de C.V.", "Chihuahua", "Minería"),
    ("Soluciones Digitales del Pacífico S.A. de C.V.", "Tijuana", "Tecnología"),
    ("Constructora y Pavimentadora de Occidente S.A. de C.V.", "León", "Construcción"),
    ("Energía Solar del Golfo S.A. de C.V.", "Veracruz", "Energía"),
    ("Logística y Transporte Nacional S.A. de C.V.", "Puebla", "Logística"),
    ("Consultoría Fiscal y Legal S.A. de C.V.", "CDMX", "Servicios Profesionales"),
    ("Manufactura de Precisión S.A. de C.V.", "Querétaro", "Manufactura"),
    ("Proyectos Hidráulicos del Sureste S.A. de C.V.", "Mérida", "Construcción"),
    ("Telecomunicaciones de Baja California S.A. de C.V.", "Mexicali", "Tecnología"),
    ("Agroindustrial del Bajío S.A. de C.V.", "Aguascalientes", "Agroindustria"),
    ("Seguridad y Vigilancia Nacional S.A. de C.V.", "CDMX", "Seguridad"),
    ("Desarrollo Inmobiliario del Sur S.A. de C.V.", "Oaxaca", "Inmobiliario"),
    ("Proveedor de Servicios Generales S.A. de C.V.", "CDMX", "Servicios"),
    ("Tecnología Médica Avanzada S.A. de C.V.", "Monterrey", "Salud"),
    ("Consortium de Ingeniería Civil S.A. de C.V.", "Guadalajara", "Construcción"),
    ("Comercializadora de Materiales S.A. de C.V.", "Puebla", "Comercio"),
    ("Sistemas de Información Geográfica S.A. de C.V.", "CDMX", "Tecnología"),
]

CONTRATANTES = [
    "Grupo Salinas S.A. de C.V.",
    "Banco Azteca S.A.",
    "Totalplay Telecomunicaciones S.A. de C.V.",
    "Elektra S.A. de C.V.",
    "Grupo Televisa S.A.B. de C.V.",
    "Petrobal S.A. de C.V.",
    "Cementos Mexicanos S.A.B. de C.V.",
]

OBJETOS_CONTRATO = [
    "Prestación de servicios de consultoría tecnológica para modernización de infraestructura",
    "Suministro e instalación de equipo de cómputo y redes corporativas",
    "Desarrollo de plataforma digital de comercio electrónico B2B",
    "Construcción de Centro de Datos Tier III con capacidad de 500 racks",
    "Mantenimiento preventivo y correctivo de infraestructura de telecomunicaciones",
    "Implementación de sistema de gestión de riesgos basado en inteligencia artificial",
    "Servicios de limpieza, mantenimiento y seguridad para 15 sucursales",
    "Desarrollo e implementación de chatbot de atención al cliente con IA",
    "Auditoría de ciberseguridad y pruebas de penetración",
    "Suministro de materiales de construcción para proyecto habitacional",
    "Servicios de nube (IaaS/PaaS) para migración de sistemas legacy",
    "Consultoría en transformación digital y cambio organizacional",
    "Implementación de ERP SAP S/4HANA para gestión financiera",
    "Servicios de procesamiento de datos y analytics avanzado",
    "Construcción de carretera de 45 km con especificaciones SCT",
]

JURISDICCIONES = [
    "Ciudad de México, ante los tribunales competentes",
    "Monterrey, Nuevo León, ante los tribunales ordinarios",
    "Querétaro, Querétaro, mediante arbitraje CNA",
    "Guadalajara, Jalisco, ante la justicia ordinaria",
    "Arbitraje comercial bajo las reglas de la CCI (Cámara de Comercio Internacional)",
    "Arbitraje UNCITRAL con sede en Ciudad de México",
]

# ─── Perfiles de riesgo ──────────────────────────────────────────
RISK_PROFILES = {
    "BAJO": {
        "score_range": (10, 35),
        "penalizacion": (2, 8),
        "garantia": (15, 30),
        "anticipo": (0, 10),
        "plazo": (30, 180),
        "monto": (100_000, 2_000_000),
        "alertas_posibles": [
            "Sin alertas significativas",
            "Plazo de entrega ajustado pero factible",
            "Garantía cumple con el mínimo recomendado",
        ],
        "recomendaciones": [
            "Aprobar con monitoreo estándar",
            "Revisar cumplimiento de obligaciones fiscales",
            "Verificar experiencia previa del proveedor",
        ],
        "confidencialidad": "Estándar",
    },
    "MEDIO": {
        "score_range": (36, 55),
        "penalizacion": (8, 15),
        "garantia": (8, 15),
        "anticipo": (10, 25),
        "plazo": (90, 365),
        "monto": (1_000_000, 8_000_000),
        "alertas_posibles": [
            "Penalización por debajo del 10% recomendado",
            "Garantía insuficiente para el monto del contrato",
            "Plazo de entrega extenso sin hitos intermedios",
            "Proveedor con historial limitado en el sector",
        ],
        "recomendaciones": [
            "Solicitar garantía adicional del 5%",
            "Incluir cláusula de auditoría parcial",
            "Establecer pagos vinculados a entregables",
            "Revisar referencias del proveedor",
        ],
        "confidencialidad": "Reforzada",
    },
    "ALTO": {
        "score_range": (56, 75),
        "penalizacion": (15, 30),
        "garantia": (3, 10),
        "anticipo": (20, 40),
        "plazo": (180, 730),
        "monto": (5_000_000, 25_000_000),
        "alertas_posibles": [
            "Penalización excesiva que podría generar incumplimiento",
            "Garantía menor al 10% del monto total",
            "Anticipo superior al 25% sin garantía de devolución",
            "Jurisdicción en estado con alto índice de litigios",
            "Cláusula de rescisión unilateral sin causa justificada",
            "Proveedor con deuda fiscal reportada",
        ],
        "recomendaciones": [
            "RECHAZAR sin garantía de devolución de anticipo",
            "Exigir fianza de cumplimiento del 20%",
            "Incluir cláusula de resolución de disputas por arbitraje",
            "Solicitar estados financieros auditados",
            "Limitar anticipo al 15% con carta de crédito",
            "Incluir derecho de inspección sin previo aviso",
        ],
        "confidencialidad": "Estricta con NDA independiente",
    },
    "CRITICO": {
        "score_range": (76, 98),
        "penalizacion": (30, 50),
        "garantia": (0, 5),
        "anticipo": (30, 50),
        "plazo": (365, 1095),
        "monto": (10_000_000, 50_000_000),
        "alertas_posibles": [
            "ALERTA ROJA: Penalización superior al 30%",
            "ALERTA ROJA: Sin garantía o garantía simbólica",
            "ALERTA ROJA: Anticipo sin mecanismo de devolución",
            "ALERTA ROJA: Jurisdicción UNCITRAL (costoso, lento)",
            "ALERTA ROJA: Cláusula de confidencialidad perpetua",
            "ALERTA ROJA: Sin cláusula de terminación por conveniencia",
            "ALERTA ROJA: Obligaciones de resultado sin limitación",
            "ALERTA ROJA: Proveedor vinculado a persona políticamente expuesta",
        ],
        "recomendaciones": [
            "RECHAZAR el contrato en términos actuales",
            "Reestructurar completamente el esquema de garantías",
            "Eliminar anticipo o reducirlo al 10%",
            "Cambiar jurisdicción a arbitraje institucional en CDMX",
            "Incluir límite de responsabilidad (cap) del 100% del contrato",
            "Solicitar opinión legal externa antes de firmar",
            "Evaluar alternativas de proveedores",
        ],
        "confidencialidad": "Máxima con cláusula de destrucción de información",
    },
}

# ─── Generar risk_results canónicos alineados a data/contracts/*.pdf ─────
print("Generando 6 resultados canónicos de análisis de riesgo...")

risk_canonical = [
    {   # contrato-bajo-riesgo-consultoria.pdf
        "contract_number": "AYCO-2026-0160",
        "source_file": "contrato-bajo-riesgo-consultoria.pdf",
        "vendor_name": "Consultores Asociados de Queretaro S.C.",
        "monto_total": 850000.00,
        "plazo_dias": 184,
        "penalizacion_pct": 10.0,
        "garantia_pct": 15.0,
        "risk_score": 2.5,
        "risk_level": "BAJO",
        "alertas": "Sin alertas criticas | Garantia suficiente (fianza 15% + deposito $50K) | Jurisdiccion Queretaro",
        "recomendaciones": "Aprobar con monitoreo estandar | Verificar entrega de fianza",
        "resumen": "Contrato de bajo riesgo por monto moderado ($850K), garantia del 15% y penalizacion baja del 10%.",
        "llm_provider": "maas-deepseek-v4-flash",
        "analyzed_at": "2026-05-08T10:15:00",
    },
    {   # contrato-medio-riesgo-mantenimiento.pdf
        "contract_number": "AYCO-2026-0161",
        "source_file": "contrato-medio-riesgo-mantenimiento.pdf",
        "vendor_name": "Autoservicio Mecanico del Norte S.A. de C.V.",
        "monto_total": 4200000.00,
        "plazo_dias": 365,
        "penalizacion_pct": 25.0,
        "garantia_pct": 5.0,
        "risk_score": 5.0,
        "risk_level": "MEDIO",
        "alertas": "Penalizacion del 25% | Garantia minima del 5% | Jurisdiccion San Luis Potosi",
        "recomendaciones": "Evaluar incrementar garantia | Verificar cobertura de carta de credito",
        "resumen": "Contrato de riesgo medio por monto elevado ($4.2M), penalizacion del 25% y garantia limitada.",
        "llm_provider": "maas-deepseek-v4-flash",
        "analyzed_at": "2026-05-08T10:16:00",
    },
    {   # contrato-alto-riesgo-software.pdf
        "contract_number": "AYCO-2026-0162",
        "source_file": "contrato-alto-riesgo-software.pdf",
        "vendor_name": "TechSolutions de Mexico S.A. de C.V.",
        "monto_total": 7800000.00,
        "plazo_dias": 365,
        "penalizacion_pct": 40.0,
        "garantia_pct": 0.0,
        "risk_score": 8.5,
        "risk_level": "ALTO",
        "alertas": "Penalizacion por terminacion anticipada del 40% | Sin garantia de cumplimiento | Jurisdiccion fuera de CDMX",
        "recomendaciones": "Exigir fianza de cumplimiento | Reducir penalizacion | Revisar jurisdiccion y confidencialidad",
        "resumen": "Contrato de riesgo alto por penalizacion elevada (40%), ausencia de garantia y jurisdiccion en Monterrey.",
        "llm_provider": "maas-deepseek-v4-flash",
        "analyzed_at": "2026-05-08T10:17:00",
    },
    {   # contrato-critico-datacenter.pdf
        "contract_number": "AYCO-2026-0163",
        "source_file": "contrato-critico-datacenter.pdf",
        "vendor_name": "Constructora del Pacifico Express S. de R.L. de C.V.",
        "monto_total": 22500000.00,
        "plazo_dias": 549,
        "penalizacion_pct": 50.0,
        "garantia_pct": 0.0,
        "risk_score": 9.5,
        "risk_level": "CRITICO",
        "alertas": "Penalizacion por terminacion del 50% | Sin garantia de cumplimiento | Arbitraje UNCITRAL en ingles | Empresa de reciente creacion (RFC 2024) | Confidencialidad indefinida",
        "recomendaciones": "Reestructurar garantias | Renegociar penalizacion | Revisar arbitraje y confidencialidad con asesoria legal | Auditoria financiera al contratista",
        "resumen": "Contrato critico por penalizacion extrema (50%), ausencia de garantia, arbitraje internacional y contratista de reciente creacion.",
        "llm_provider": "maas-deepseek-v4-flash",
        "analyzed_at": "2026-05-08T10:18:00",
    },
    {   # contrato-alto-riesgo-outsourcing.pdf
        "contract_number": "AYCO-2026-0164",
        "source_file": "contrato-alto-riesgo-outsourcing.pdf",
        "vendor_name": "Capital Humano y Servicios del Sureste S.A. de C.V.",
        "monto_total": 9600000.00,
        "plazo_dias": 365,
        "penalizacion_pct": 35.0,
        "garantia_pct": 0.0,
        "risk_score": 8.0,
        "risk_level": "ALTO",
        "alertas": "Penalizacion del 35% | Sin garantia de cumplimiento (exonerado por relacion de confianza) | Jurisdiccion Tapachula, Chiapas | Propiedad intelectual para el contratista",
        "recomendaciones": "Exigir garantia de cumplimiento | Revisar clausula de propiedad intelectual | Evaluar jurisdiccion remota",
        "resumen": "Contrato de alto riesgo por outsourcing de personal especializado sin garantia, penalizacion del 35% y jurisdiccion en Chiapas.",
        "llm_provider": "maas-deepseek-v4-flash",
        "analyzed_at": "2026-05-08T10:19:00",
    },
    {   # contrato-medio-riesgo-suministros.pdf
        "contract_number": "AYCO-2026-0165",
        "source_file": "contrato-medio-riesgo-suministros.pdf",
        "vendor_name": "Equipamiento Hospitalario del Bajio S.A. de C.V.",
        "monto_total": 5800000.00,
        "plazo_dias": 184,
        "penalizacion_pct": 20.0,
        "garantia_pct": 10.0,
        "risk_score": 4.5,
        "risk_level": "MEDIO",
        "alertas": "Penalizacion del 20% | Garantia del 10% solo primer anio | Suministro de equipo medico critico",
        "recomendaciones": "Extender garantia a toda la vigencia | Verificar certificaciones del equipo medico",
        "resumen": "Contrato de riesgo medio por equipo medico especializado, garantia limitada al primer anio y monto de $5.8M.",
        "llm_provider": "maas-deepseek-v4-flash",
        "analyzed_at": "2026-05-08T10:20:00",
    },
]

# Add 17 synthetic contracts to reach 20 total (better demo visual)
print("Generando 17 contratos sintéticos adicionales (total 20)...")
risk_synthetic = []
for i in range(1, 18):
    profile_name = random.choices(
        ["BAJO", "MEDIO", "ALTO", "CRITICO"],
        weights=[30, 30, 25, 15]
    )[0]
    profile = RISK_PROFILES[profile_name]
    proveedor = random.choice(PROVEEDORES)
    contratante = random.choice(CONTRATANTES)
    monto = round(random.uniform(*profile["monto"]), 2)
    penalizacion = round(random.uniform(*profile["penalizacion"]), 1)
    garantia = round(random.uniform(*profile["garantia"]), 1)
    plazo = random.randint(*profile["plazo"])
    score = round(random.uniform(*profile["score_range"]) / 10, 1)
    alertas = random.sample(profile["alertas_posibles"], min(2, len(profile["alertas_posibles"])))
    recs = random.sample(profile["recomendaciones"], min(2, len(profile["recomendaciones"])))

    risk_synthetic.append({
        "contract_number": f"AYCO-2026-{170 + i:04d}",
        "vendor_name": proveedor[0],
        "monto_total": monto,
        "plazo_dias": plazo,
        "penalizacion_pct": penalizacion,
        "garantia_pct": garantia,
        "risk_score": score,
        "risk_level": profile_name,
        "alertas": " | ".join(alertas),
        "recomendaciones": " | ".join(recs),
        "resumen": f"Contrato {profile_name.lower()} — ${monto:,.0f} MXN, {plazo} días, penalización {penalizacion}%, garantía {garantia}%",
        "llm_provider": "maas-deepseek-v4-flash",
        "analyzed_at": f"2026-05-08T10:{18 + i:02d}:00",
    })

risk_results = risk_canonical + risk_synthetic

# Write CSV
fieldnames = list(risk_results[0].keys())
with open(RESULTS_DIR / "risk_results.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(risk_results)

print(f"  → {RESULTS_DIR / 'risk_results.csv'} ({len(risk_results)} rows)")

# ─── Generar contract_texts (20 contratos como .txt) ──────────────
print("Generando 20 textos de contrato para OBS...")

for i in range(1, 21):
    profile_name = random.choices(
        ["BAJO", "MEDIO", "ALTO", "CRITICO"],
        weights=[30, 30, 25, 15]
    )[0]
    profile = RISK_PROFILES[profile_name]

    proveedor = random.choice(PROVEEDORES)
    contratante = random.choice(CONTRATANTES)
    objeto = random.choice(OBJETOS_CONTRATO)
    jurisdiccion = random.choice(JURISDICCIONES)

    monto = round(random.uniform(*profile["monto"]), 2)
    penalizacion = round(random.uniform(*profile["penalizacion"]), 1)
    garantia = round(random.uniform(*profile["garantia"]), 1)
    anticipo = round(random.uniform(*profile["anticipo"]), 1)
    plazo = random.randint(*profile["plazo"])

    inicio = datetime(2026, 5, random.randint(1, 28))
    fin = inicio + timedelta(days=plazo)

    confidencialidad = profile["confidencialidad"]

    # Generate contract text
    text = f"""CONTRATO DE PRESTACIÓN DE SERVICIOS
No. AYCO-2026-{i:04d}

──────────────────────────────────────────────────────────────

CONTRATANTE: {contratante}
RFC: {random.choice(['GSA850101ABC', 'BAA920215XYZ', 'TTP880312DEF', 'ELK750620GHI'])}
Domicilio: Av. Insurgentes Sur {random.randint(1000, 5000)}, Col. {random.choice(['Del Valle', 'Roma Norte', 'Condesa', 'Polanco', 'Narvarte'])}, CDMX

CONTRATISTA: {proveedor[0]}
RFC: {random.choice(['CVM850101ABC', 'TAN920215XYZ', 'SII880312DEF', 'GIM750620GHI'])}
Domicilio: {proveedor[1]}, {proveedor[2]}

──────────────────────────────────────────────────────────────

OBJETO DEL CONTRATO:
{objeto}

──────────────────────────────────────────────────────────────

CLÁUSULAS:

PRIMERA. MONTO TOTAL
El monto total del presente contrato asciende a la cantidad de ${monto:,.2f} MXN ({"{:.2f}".format(monto)} pesos 00/100 M.N.), más IVA aplicable.

SEGUNDA. PLAZO DE EJECUCIÓN
El plazo de ejecución será de {plazo} días naturales, contados a partir de la firma del presente contrato.
Fecha de inicio: {inicio.strftime('%d de %B de %Y').replace('May', 'mayo').replace('June', 'junio').replace('July', 'julio')}
Fecha de término: {fin.strftime('%d de %B de %Y').replace('May', 'mayo').replace('June', 'junio').replace('July', 'julio')}

TERCERA. PENALIZACIÓN POR RETRASO
En caso de incumplimiento en los plazos pactados, el CONTRATISTA pagará como penalización por retraso la cantidad equivalente al {penalizacion}% del monto total del contrato, es decir, ${monto * penalizacion / 100:,.2f} MXN por cada día de retraso, sin que el total acumulado pueda exceder el 30% del monto total.

CUARTA. GARANTÍA DE CUMPLIMIENTO
El CONTRATISTA constituirá garantía de cumplimiento equivalente al {garantia}% del monto total del contrato, mediante fianza expedida por institución autorizada. {"No se requiere garantía adicional." if garantia < 3 else f"La garantía será de ${monto * garantia / 100:,.2f} MXN."}

QUINTA. ANTICIPO
El CONTRATANTE entregará al CONTRATISTA un anticipo del {anticipo}% del monto total, equivalente a ${monto * anticipo / 100:,.2f} MXN. {"El anticipo no será reembolsable." if anticipo > 30 else "El anticipo será amortizable en los primeros 3 pagos parciales."}

SEXTA. JURISDICCIÓN
Para la interpretación y cumplimiento del presente contrato, las partes se someten a la jurisdicción de {jurisdiccion}.

SÉPTIMA. CONFIDENCIALIDAD
Las partes se obligan a mantener confidencialidad respecto de toda la información intercambiada con motivo del presente contrato. Nivel de confidencialidad: {confidencialidad}.

OCTAVA. PROPIEDAD INTELECTUAL
Todo lo desarrollado en virtud del presente contrato será propiedad del CONTRATANTE, incluyendo pero no limitado a: software, documentación, diseños, metodologías y procesos.

NOVENA. CAUSALES DE RESCISIÓN
El presente contrato podrá rescindirse por las siguientes causales:
a) Incumplimiento de las obligaciones pactadas
b) Insolvencia o quiebra de cualquiera de las partes
c) Caso fortuito o fuerza mayor que impida la ejecución
{"d) Rescisión unilateral del CONTRATANTE sin causa justificada" if profile_name in ["ALTO", "CRITICO"] else ""}

DÉCIMA. OBLIGACIONES FISCALES
El CONTRATISTA se obliga a cumplir con todas las obligaciones fiscales derivadas del presente contrato, incluyendo la emisión de CFDI por los pagos recibidos.

──────────────────────────────────────────────────────────────

Lugar y fecha de firma: Ciudad de México, {random.randint(1, 28)} de abril de 2026

POR EL CONTRATANTE:
_________________________________
{random.choice(['Lic. Roberto Martínez Sánchez', 'C.P. María Elena González', 'Ing. Carlos Alberto Ramírez'])}
Representante Legal

POR EL CONTRATISTA:
_________________________________
{random.choice(['Ing. José Luis Hernández', 'Mtro. Ana Patricia López', 'C.P. Fernando García Martínez'])}
Director General
"""

    filepath = TEXTS_DIR / f"contrato-2026-{i:04d}.txt"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)

print(f"  → {TEXTS_DIR}/ ({i} archivos .txt)")

# ─── Generar risk_summary.json ────────────────────────────────────
print("Generando resumen agregado...")

summary = {
    "generated_at": datetime.now().isoformat(),
    "total_contracts": len(risk_results),
    "by_level": {},
    "top_risk_contracts": [],
    "vendor_exposure": {},
    "avg_score_by_level": {},
}

# By level
for level in ["BAJO", "MEDIO", "ALTO", "CRITICO"]:
    contracts = [r for r in risk_results if r["risk_level"] == level]
    summary["by_level"][level] = {
        "count": len(contracts),
        "total_mxn": sum(r["monto_total"] for r in contracts),
        "avg_score": round(sum(r["risk_score"] for r in contracts) / max(len(contracts), 1), 1),
    }

# Top 5 risk contracts
sorted_by_score = sorted(risk_results, key=lambda r: r["risk_score"], reverse=True)
summary["top_risk_contracts"] = [
    {
        "contract": r["contract_number"],
        "vendor": r["vendor_name"],
        "score": r["risk_score"],
        "level": r["risk_level"],
        "monto": r["monto_total"],
    }
    for r in sorted_by_score[:5]
]

# Vendor exposure
for r in risk_results:
    v = r["vendor_name"]
    if v not in summary["vendor_exposure"]:
        summary["vendor_exposure"][v] = {"contracts": 0, "total_mxn": 0, "max_score": 0}
    summary["vendor_exposure"][v]["contracts"] += 1
    summary["vendor_exposure"][v]["total_mxn"] += r["monto_total"]
    summary["vendor_exposure"][v]["max_score"] = max(summary["vendor_exposure"][v]["max_score"], r["risk_score"])

# Sort by total exposure
summary["vendor_exposure"] = dict(
    sorted(summary["vendor_exposure"].items(), key=lambda x: x[1]["total_mxn"], reverse=True)[:10]
)

with open(RESULTS_DIR / "risk_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

print(f"  → {RESULTS_DIR / 'risk_summary.json'}")

# ─── Generar DWS seed data (SQL INSERT statements) ───────────────
print("Generando SQL INSERTs para DWS...")

sql_lines = [
    "-- Auto-generated by generate-contract-data.py",
    f"-- Generated: {datetime.now().isoformat()}",
    f"-- {len(risk_results)} risk results",
    "",
    "-- Limpiar datos existentes",
    "TRUNCATE TABLE risk_results;",
    "",
    "-- Insertar resultados de análisis de riesgo",
]

for r in risk_results:
    alertas = r["alertas"].replace("'", "''")
    recomendaciones = r["recomendaciones"].replace("'", "''")
    resumen = r["resumen"].replace("'", "''")
    vendor = r["vendor_name"].replace("'", "''")

    sql_lines.append(
        f"INSERT INTO risk_results "
        f"(contract_number, vendor_name, monto_total, plazo_dias, penalizacion_pct, garantia_pct, "
        f"risk_score, risk_level, alertas, recomendaciones, resumen, llm_provider, analyzed_at) "
        f"VALUES ("
        f"'{r['contract_number']}', '{vendor}', {r['monto_total']}, {r['plazo_dias']}, "
        f"{r['penalizacion_pct']}, {r['garantia_pct']}, {r['risk_score']}, '{r['risk_level']}', "
        f"'{alertas}', '{recomendaciones}', '{resumen}', '{r['llm_provider']}', "
        f"'{r['analyzed_at']}'"
        f");"
    )

sql_lines.extend([
    "",
    "-- Verify views (regular VIEWs, no MATERIALIZED refresh needed)",
    "SELECT 'contract_vendor_risk_summary' AS view_name, COUNT(*)::text AS rows FROM dm.contract_vendor_risk_summary;",
])

with open(DATA_DIR / "seed_risk_results.sql", "w", encoding="utf-8") as f:
    f.write("\n".join(sql_lines))

print(f"  → {DATA_DIR / 'seed_risk_results.sql'} ({len(risk_results)} INSERTs)")

# ─── Summary ──────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"  DATOS GENERADOS:")
print(f"  • {len(risk_results)} risk results (CSV + SQL)")
print(f"  • 20 contract text files (.txt)")
print(f"  • 1 risk summary (JSON)")
print(f"")
print(f"  DISTRIBUCIÓN DE RIESGO:")
for level in ["BAJO", "MEDIO", "ALTO", "CRITICO"]:
    count = sum(1 for r in risk_results if r["risk_level"] == level)
    total = sum(r["monto_total"] for r in risk_results if r["risk_level"] == level)
    print(f"    {level:8s}: {count:2d} contratos, ${total:>15,.2f} MXN")
print(f"")
total_monto = sum(r["monto_total"] for r in risk_results)
print(f"  EXPOSICIÓN TOTAL: ${total_monto:,.2f} MXN")
print(f"{'='*60}")
