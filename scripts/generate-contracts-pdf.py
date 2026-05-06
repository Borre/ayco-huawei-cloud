#!/usr/bin/env python3
"""Generate 6 AYCO contract PDFs with different risk profiles for the demo."""

import os
from pathlib import Path
from fpdf import FPDF

DATA_DIR = Path(__file__).parent.parent / "data" / "contracts"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# DejaVu fonts for Unicode (ñ, á, $, etc.)
FONT_DIR = "/usr/share/fonts/truetype/dejavu/"

contracts = [
    {
        "filename": "contrato-bajo-riesgo-consultoria.pdf",
        "number": "AYCO-2026-0160",
        "title": "CONTRATO DE CONSULTORÍA EN PROCESOS ADMINISTRATIVOS",
        "contratante": {
            "name": "Grupo Educativo del Bajío S.A. de C.V.",
            "rfc": "GEB210415MN3",
            "rep": "Lic. María Elena Torres Mendoza",
        },
        "contratista": {
            "name": "Consultores Asociados de Querétaro S.C.",
            "rfc": "CAQ190830PQ8",
            "rep": "C.P. José Antonio Vázquez Durán",
        },
        "objeto": "servicios de consultoría en procesos administrativos, reingeniería de flujos de trabajo, e implementación de sistema de gestión de calidad bajo norma ISO 9001:2015",
        "vigencia_inicio": "1 de marzo de 2026",
        "vigencia_fin": "31 de agosto de 2026",
        "monto": 850000.00,
        "monto_texto": "Ochocientos cincuenta mil pesos 00/100 Moneda Nacional",
        "penalizacion_pct": 10,
        "penalizacion_diaria": 5000,
        "garantia_pct": 15,
        "garantia_clause": "El CONTRATISTA entrega póliza de fianza por el 15% del monto total del contrato. Adicionalmente, realiza depósito en garantía por $50,000.00 MXN en la cuenta de la CONTRATANTE.",
        "jurisdiccion_text": "tribunales competentes de la Ciudad de Querétaro, Querétaro",
        "confidencialidad": "por un periodo de cinco (5) años",
        "propiedad": "serán propiedad de la CONTRATANTE, con licencia de uso perpetua y gratuita para el CONTRATISTA",
    },
    {
        "filename": "contrato-medio-riesgo-mantenimiento.pdf",
        "number": "AYCO-2026-0161",
        "title": "CONTRATO DE MANTENIMIENTO INTEGRAL DE FLOTA VEHICULAR",
        "contratante": {
            "name": "Transportes y Logística del Centro S.A. de C.V.",
            "rfc": "TLC200512RN9",
            "rep": "Lic. Fernando Javier Díaz Castillo",
        },
        "contratista": {
            "name": "Autoservicio Mecánico del Norte S.A. de C.V.",
            "rfc": "AMN170215TS4",
            "rep": "Ing. Ricardo Alonso Martínez Peña",
        },
        "objeto": "mantenimiento preventivo y correctivo integral de flota vehicular compuesta por 85 unidades de transporte de carga, incluyendo refacciones originales, mano de obra, y servicio de grúa 24/7 en carreteras de la región centro-norte",
        "vigencia_inicio": "1 de mayo de 2026",
        "vigencia_fin": "30 de abril de 2027",
        "monto": 4200000.00,
        "monto_texto": "Cuatro millones doscientos mil pesos 00/100 Moneda Nacional",
        "penalizacion_pct": 25,
        "penalizacion_diaria": 15000,
        "garantia_pct": 5,
        "garantia_clause": "El CONTRATISTA presenta carta de crédito por el 5% del monto total del contrato. No se requiere depósito en garantía adicional.",
        "jurisdiccion_text": "tribunales competentes de San Luis Potosí, San Luis Potosí",
        "confidencialidad": "por un periodo de tres (3) años",
        "propiedad": "serán propiedad de la CONTRATANTE",
    },
    {
        "filename": "contrato-alto-riesgo-software.pdf",
        "number": "AYCO-2026-0162",
        "title": "CONTRATO DE DESARROLLO DE SOFTWARE EMPRESARIAL",
        "contratante": {
            "name": "Financiera Nacional de Desarrollo S.A. de C.V.",
            "rfc": "FND220901KL7",
            "rep": "Lic. María Fernanda Gutiérrez López",
        },
        "contratista": {
            "name": "TechSolutions de México S.A. de C.V.",
            "rfc": "TSM210315AB4",
            "rep": "Ing. Carlos Alberto Ramírez Hernández",
        },
        "objeto": "desarrollo de software empresarial para sistema de originación de crédito, incluyendo módulo de scoring crediticio, integración con burós de crédito, portal de clientes, y dashboard de análisis de riesgo en tiempo real",
        "vigencia_inicio": "1 de abril de 2026",
        "vigencia_fin": "31 de marzo de 2027",
        "monto": 7800000.00,
        "monto_texto": "Siete millones ochocientos mil pesos 00/100 Moneda Nacional",
        "penalizacion_pct": 40,
        "penalizacion_diaria": 80000,
        "garantia_pct": 0,
        "garantia_clause": "Sin garantía de cumplimiento. El CONTRATISTA no presenta fianza, depósito ni carta de crédito. La CONTRATANTE confía en la trayectoria del proveedor.",
        "jurisdiccion_text": "tribunales competentes de Monterrey, Nuevo León",
        "confidencialidad": "por un periodo de diez (10) años",
        "propiedad": "serán propiedad exclusiva de la CONTRATANTE, sin licencia para el CONTRATISTA",
    },
    {
        "filename": "contrato-critico-datacenter.pdf",
        "number": "AYCO-2026-0163",
        "title": "CONTRATO DE CONSTRUCCIÓN DE CENTRO DE DATOS",
        "contratante": {
            "name": "Fondo de Inversión del Pacífico S.A. de C.V.",
            "rfc": "FIP230801KL5",
            "rep": "Lic. María Fernanda Gutiérrez López",
        },
        "contratista": {
            "name": "Constructora del Pacífico Express S. de R.L. de C.V.",
            "rfc": "CPE240115MN6",
            "rep": "Arq. Juan Pablo Mendoza Ríos",
        },
        "objeto": "construcción, equipamiento y puesta en marcha de un centro de datos corporativo Tier III, incluyendo obra civil, sistemas de respaldo energético con generadores y UPS redundantes, climatización de precisión N+1, infraestructura de red con fibra óptica, y certificación ICREA",
        "vigencia_inicio": "1 de junio de 2026",
        "vigencia_fin": "31 de diciembre de 2027",
        "monto": 22500000.00,
        "monto_texto": "Veintidós millones quinientos mil pesos 00/100 Moneda Nacional",
        "penalizacion_pct": 50,
        "penalizacion_diaria": 350000,
        "garantia_pct": 0,
        "garantia_clause": "Sin garantía de cumplimiento. El CONTRATISTA es una empresa de reciente creación (RFC 2024) y no presenta fianza, depósito ni carta de crédito.",
        "jurisdiccion_text": "arbitraje internacional bajo reglamento UNCITRAL en inglés, sede en Cancún, Quintana Roo",
        "confidencialidad": "de manera indefinida, sin limitación temporal",
        "propiedad": "serán propiedad compartida entre las partes en proporción 50-50%",
    },
    {
        "filename": "contrato-alto-riesgo-outsourcing.pdf",
        "number": "AYCO-2026-0164",
        "title": "CONTRATO DE OUTSOURCING DE PERSONAL ESPECIALIZADO",
        "contratante": {
            "name": "Banco Regional de Desarrollo S.A. Institución de Banca Múltiple",
            "rfc": "BRD150820FG6",
            "rep": "Lic. Alejandro Gómez Sada",
        },
        "contratista": {
            "name": "Capital Humano y Servicios del Sureste S.A. de C.V.",
            "rfc": "CHS190530WX2",
            "rep": "Lic. Patricia Hernández López",
        },
        "objeto": "suministro de personal especializado en tecnologías de la información para el área de transformación digital y modernización del core bancario, incluyendo 45 ingenieros de software senior, 12 arquitectos de soluciones, y 8 gerentes de proyecto certificados PMP",
        "vigencia_inicio": "15 de abril de 2026",
        "vigencia_fin": "14 de abril de 2027",
        "monto": 9600000.00,
        "monto_texto": "Nueve millones seiscientos mil pesos 00/100 Moneda Nacional",
        "penalizacion_pct": 35,
        "penalizacion_diaria": 120000,
        "garantia_pct": 0,
        "garantia_clause": "Sin garantía de cumplimiento. Se exonera al CONTRATISTA de presentar cualquier tipo de garantía debido a la 'relación de confianza' entre las partes.",
        "jurisdiccion_text": "tribunales competentes de Tapachula, Chiapas",
        "confidencialidad": "por tiempo indefinido",
        "propiedad": "el CONTRATISTA conservará todos los derechos de propiedad intelectual del personal asignado",
    },
    {
        "filename": "contrato-medio-riesgo-suministros.pdf",
        "number": "AYCO-2026-0165",
        "title": "CONTRATO DE SUMINISTRO DE EQUIPO MÉDICO",
        "contratante": {
            "name": "Hospital Ángeles del Pedregal S.A. de C.V.",
            "rfc": "HAP910620KL2",
            "rep": "Dr. Roberto Sánchez Miranda",
        },
        "contratista": {
            "name": "Equipamiento Hospitalario del Bajío S.A. de C.V.",
            "rfc": "EHB180410MN7",
            "rep": "Ing. Luis Fernando Ortega Vega",
        },
        "objeto": "suministro, instalación y capacitación de equipo médico de imagenología, incluyendo un tomógrafo computarizado de 128 cortes, un resonador magnético de 1.5 Tesla, y un sistema de angiografía digital con arco en C, para el área de diagnóstico por imagen del hospital",
        "vigencia_inicio": "1 de julio de 2026",
        "vigencia_fin": "31 de diciembre de 2026",
        "monto": 5800000.00,
        "monto_texto": "Cinco millones ochocientos mil pesos 00/100 Moneda Nacional",
        "penalizacion_pct": 20,
        "penalizacion_diaria": 25000,
        "garantia_pct": 10,
        "garantia_clause": "El CONTRATISTA entrega póliza de fianza por el 10% del monto total del contrato, únicamente por el primer año. No se requiere garantía adicional para años subsecuentes.",
        "jurisdiccion_text": "tribunales competentes de la Ciudad de México",
        "confidencialidad": "por un periodo de siete (7) años",
        "propiedad": "el equipo será propiedad de la CONTRATANTE una vez recibido a entera satisfacción",
    },
]


def format_mxn(amount):
    return f"${amount:,.2f} MXN"


def add_page_header(pdf, c, page_num):
    """Add header to each page."""
    pdf.set_font("DejaVuSans", "", 7)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 4, f"CONTRATO {c['number']} — Página {page_num}", align="R")
    pdf.ln(6)


def build_contract(c):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_font("DejaVuSerif", "", os.path.join(FONT_DIR, "DejaVuSerif.ttf"))
    pdf.add_font("DejaVuSerif", "B", os.path.join(FONT_DIR, "DejaVuSerif-Bold.ttf"))
    pdf.add_font("DejaVuSans", "", os.path.join(FONT_DIR, "DejaVuSans.ttf"))

    def write_header():
        pdf.set_font("DejaVuSans", "", 7)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 4, f"CONTRATO {c['number']}  —  Página {pdf.page_no()}", align="R")
        pdf.ln(6)

    pdf.add_page()

    # Contract number
    pdf.set_font("DejaVuSerif", "B", 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, f"CONTRATO NÚMERO: {c['number']}", align="C")
    pdf.ln(12)

    # Title
    pdf.set_font("DejaVuSerif", "B", 11)
    pdf.cell(0, 7, c["title"], align="C")
    pdf.ln(10)

    # Parties
    pdf.set_font("DejaVuSerif", "B", 10)
    pdf.cell(0, 6, "CONTRATANTE:")
    pdf.ln(6)
    pdf.set_font("DejaVuSerif", "", 9)
    pdf.multi_cell(0, 5, c["contratante"]["name"])
    pdf.cell(0, 5, f"RFC: {c['contratante']['rfc']}")
    pdf.ln(5)
    pdf.cell(0, 5, f"Representante legal: {c['contratante']['rep']}")
    pdf.ln(8)

    pdf.set_font("DejaVuSerif", "B", 10)
    pdf.cell(0, 6, "CONTRATISTA:")
    pdf.ln(6)
    pdf.set_font("DejaVuSerif", "", 9)
    pdf.multi_cell(0, 5, c["contratista"]["name"])
    pdf.cell(0, 5, f"RFC: {c['contratista']['rfc']}")
    pdf.ln(5)
    pdf.cell(0, 5, f"Representante legal: {c['contratista']['rep']}")
    pdf.ln(8)

    pdf.set_font("DejaVuSerif", "", 9)
    pdf.multi_cell(
        0,
        5,
        'Ambas partes, en lo sucesivo denominadas conjuntamente como "Las Partes", reconocen tener capacidad legal suficiente para obligarse en los términos del presente contrato y, al efecto, manifiestan:',
    )
    pdf.ln(4)

    # Declarations
    pdf.multi_cell(0, 5, f"I. Que la CONTRATANTE requiere de {c['objeto']}.")
    pdf.ln(3)
    pdf.multi_cell(
        0,
        5,
        "II. Que el CONTRATISTA cuenta con la experiencia, capacidad técnica y recursos necesarios para prestar los servicios requeridos.",
    )
    pdf.ln(3)
    pdf.multi_cell(
        0,
        5,
        "III. Que Las Partes, en virtud de lo anterior, convienen en celebrar el presente contrato de conformidad con las siguientes cláusulas:",
    )
    pdf.ln(6)

    # CLAUSES
    # PRIMERA — Objeto
    pdf.set_font("DejaVuSerif", "B", 10)
    pdf.cell(0, 6, "PRIMERA. OBJETO DEL CONTRATO")
    pdf.ln(7)
    pdf.set_font("DejaVuSerif", "", 9)
    pdf.multi_cell(0, 5, f"El presente contrato tiene por objeto la {c['objeto']}. El CONTRATISTA se obliga a prestar los servicios conforme al alcance descrito en el Anexo Técnico I, el cual forma parte integral del presente contrato.")
    pdf.ln(5)

    # SEGUNDA — Vigencia
    pdf.set_font("DejaVuSerif", "B", 10)
    pdf.cell(0, 6, "SEGUNDA. VIGENCIA")
    pdf.ln(7)
    pdf.set_font("DejaVuSerif", "", 9)
    pdf.multi_cell(0, 5, f"El presente contrato tendrá una vigencia del {c['vigencia_inicio']} al {c['vigencia_fin']}, pudiendo prorrogarse por mutuo acuerdo de las partes mediante convenio adicional suscrito por ambas.")
    pdf.ln(5)

    # TERCERA — Monto
    pdf.set_font("DejaVuSerif", "B", 10)
    pdf.cell(0, 6, "TERCERA. MONTO TOTAL Y FORMA DE PAGO")
    pdf.ln(7)
    pdf.set_font("DejaVuSerif", "", 9)
    monto_str = format_mxn(c["monto"])
    pdf.multi_cell(0, 5, f"El monto total del presente contrato es de {monto_str} ({c['monto_texto']}), más IVA. El pago se realizará de la siguiente manera: a) 30% a la firma del presente contrato; b) 40% contra entregables parciales aprobados por la CONTRATANTE; c) 30% restante contra la recepción final del proyecto.")
    pdf.ln(5)

    # CUARTA — Penalizaciones
    pdf.set_font("DejaVuSerif", "B", 10)
    pdf.cell(0, 6, "CUARTA. PENALIZACIONES")
    pdf.ln(7)
    pdf.set_font("DejaVuSerif", "", 9)
    pen_diaria_str = format_mxn(c["penalizacion_diaria"])
    pdf.multi_cell(0, 5, f"En caso de terminación anticipada del presente contrato por causas imputables al CONTRATISTA, éste deberá pagar a la CONTRATANTE una penalización equivalente al {c['penalizacion_pct']}% del monto total del contrato. En caso de retraso en la entrega de los servicios contratados, el CONTRATISTA pagará una penalización de {pen_diaria_str} por día calendario de retraso, sin que dicha penalización pueda exceder del {min(c['penalizacion_pct'] + 10, 50)}% del monto total del contrato.")
    pdf.ln(5)

    # QUINTA — Garantía
    pdf.set_font("DejaVuSerif", "B", 10)
    pdf.cell(0, 6, "QUINTA. GARANTÍA DE CUMPLIMIENTO")
    pdf.ln(7)
    pdf.set_font("DejaVuSerif", "", 9)
    pdf.multi_cell(0, 5, c["garantia_clause"])
    pdf.ln(5)

    # SEXTA — Jurisdicción
    pdf.set_font("DejaVuSerif", "B", 10)
    pdf.cell(0, 6, "SEXTA. JURISDICCIÓN")
    pdf.ln(7)
    pdf.set_font("DejaVuSerif", "", 9)
    pdf.multi_cell(0, 5, f"Para la interpretación y cumplimiento del presente contrato, las partes se someten a los {c['jurisdiccion_text']}, renunciando expresamente a cualquier otro fuero que pudiera corresponderles por razón de domicilio presente o futuro.")
    pdf.ln(5)

    # SÉPTIMA — Confidencialidad
    pdf.set_font("DejaVuSerif", "B", 10)
    pdf.cell(0, 6, "SÉPTIMA. CONFIDENCIALIDAD")
    pdf.ln(7)
    pdf.set_font("DejaVuSerif", "", 9)
    pdf.multi_cell(0, 5, f"Las partes se comprometen a mantener estricta confidencialidad sobre toda la información técnica, comercial, financiera y operativa que reciban con motivo del presente contrato. Las obligaciones de confidencialidad subsistirán {c['confidencialidad']} contados a partir de la terminación del presente contrato.")
    pdf.ln(5)

    # OCTAVA — Propiedad Intelectual
    pdf.set_font("DejaVuSerif", "B", 10)
    pdf.cell(0, 6, "OCTAVA. PROPIEDAD INTELECTUAL")
    pdf.ln(7)
    pdf.set_font("DejaVuSerif", "", 9)
    pdf.multi_cell(0, 5, f"Todo el software, documentación y material desarrollado por el CONTRATISTA en virtud del presente contrato {c['propiedad']}.")
    pdf.ln(5)

    # NOVENA — Rescisión
    pdf.set_font("DejaVuSerif", "B", 10)
    pdf.cell(0, 6, "NOVENA. CAUSAS DE RESCISIÓN")
    pdf.ln(7)
    pdf.set_font("DejaVuSerif", "", 9)
    pdf.multi_cell(0, 5, "El presente contrato podrá rescindirse por cualquiera de las siguientes causas: a) Incumplimiento de las obligaciones pactadas; b) Quiebra o concurso mercantil de cualquiera de las partes; c) Mutuo acuerdo de las partes; d) Caso fortuito o fuerza mayor debidamente comprobado.")
    pdf.ln(8)

    # Signatures
    pdf.set_font("DejaVuSerif", "", 9)
    pdf.cell(0, 5, "Las partes firman el presente contrato en dos tantos, en la Ciudad de México, a los ___ días del mes de ______________ de 2026.", align="C")
    pdf.ln(15)

    # Signature lines
    pdf.set_font("DejaVuSerif", "", 9)
    left_x = pdf.get_x()
    mid_x = pdf.w / 2
    pdf.cell(mid_x - 20, 1, "", border="T")
    pdf.set_x(mid_x + 20)
    pdf.cell(mid_x - 20, 1, "", border="T")
    pdf.ln(4)
    pdf.set_x(left_x)
    pdf.set_font("DejaVuSerif", "B", 9)
    pdf.cell(mid_x - 20, 5, "CONTRATANTE", align="C")
    pdf.set_x(mid_x + 20)
    pdf.cell(mid_x - 20, 5, "CONTRATISTA", align="C")
    pdf.ln(10)

    pdf.set_font("DejaVuSans", "", 6)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 4, f"AYCO-2026 — Documento generado para fines de demostración", align="C")

    return pdf


# Generate all contracts
for c in contracts:
    path = DATA_DIR / c["filename"]
    pdf = build_contract(c)
    pdf.output(str(path))
    risk_label = c.get("riesgo", "?")
    print(f"  {risk_label:8s} {c['number']} — {path.name} (${c['monto']:,.0f})")

print(f"\n6 contratos generados en {DATA_DIR}/")
