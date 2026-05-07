#!/usr/bin/env python3
"""Generate 6 clean AYCO contracts with searchable text (Helvetica core font)."""
import os, unicodedata
from pathlib import Path
from fpdf import FPDF

DATA_DIR = Path(__file__).parent.parent / "data" / "contracts"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def asciify(s):
    """Replace Spanish special chars and Unicode punctuation with ASCII equivalents."""
    replacements = {'á':'a','é':'e','í':'i','ó':'o','ú':'u','ü':'u','ñ':'ny',
                    'Á':'A','É':'E','Í':'I','Ó':'O','Ú':'U','Ü':'U','Ñ':'NY',
                    '--':'--','–':'-','\u201c':'"','\u201d':'"','\u2018':"'",'\u2019':"'",
                    '…':'...','\u00a0':' '}
    for sp, asc in replacements.items():
        s = s.replace(sp, asc)
    return s

contracts = [
    {
        "filename": "contrato-bajo-riesgo-consultoria.pdf",
        "number": "AYCO-2026-0160",
        "title": "CONTRATO DE CONSULTORIA EN PROCESOS ADMINISTRATIVOS",
        "contratante": {"name": "Grupo Educativo del Bajio S.A. de C.V.", "rfc": "GEB210415MN3", "rep": "Lic. Maria Elena Torres Mendoza"},
        "contratista": {"name": "Consultores Asociados de Queretaro S.C.", "rfc": "CAQ190830PQ8", "rep": "C.P. Jose Antonio Vazquez Duran"},
        "objeto": "servicios de consultoria en procesos administrativos, reingenieria de flujos de trabajo, e implementacion de sistema de gestion de calidad bajo norma ISO 9001:2015",
        "vigencia_inicio": "1 de marzo de 2026", "vigencia_fin": "31 de agosto de 2026",
        "monto": 850000.00, "monto_texto": "Ochocientos cincuenta mil pesos 00/100 Moneda Nacional",
        "penalizacion_pct": 10, "penalizacion_diaria": 5000,
        "garantia_clause": "El CONTRATISTA entrega poliza de fianza por el 15% del monto total del contrato. Adicionalmente, realiza deposito en garantia por $50,000.00 MXN en la cuenta de la CONTRATANTE.",
        "jurisdiccion_text": "tribunales competentes de la Ciudad de Queretaro, Queretaro",
        "confidencialidad": "por un periodo de cinco (5) anios",
        "propiedad": "seran propiedad de la CONTRATANTE, con licencia de uso perpetua y gratuita para el CONTRATISTA",
    },
    {
        "filename": "contrato-medio-riesgo-mantenimiento.pdf",
        "number": "AYCO-2026-0161",
        "title": "CONTRATO DE MANTENIMIENTO INTEGRAL DE FLOTA VEHICULAR",
        "contratante": {"name": "Transportes y Logistica del Centro S.A. de C.V.", "rfc": "TLC200512RN9", "rep": "Lic. Fernando Javier Diaz Castillo"},
        "contratista": {"name": "Autoservicio Mecanico del Norte S.A. de C.V.", "rfc": "AMN170215TS4", "rep": "Ing. Ricardo Alonso Martinez Pena"},
        "objeto": "mantenimiento preventivo y correctivo integral de flota vehicular compuesta por 85 unidades de transporte de carga, incluyendo refacciones originales, mano de obra, y servicio de grua 24/7 en carreteras de la region centro-norte",
        "vigencia_inicio": "1 de mayo de 2026", "vigencia_fin": "30 de abril de 2027",
        "monto": 4200000.00, "monto_texto": "Cuatro millones doscientos mil pesos 00/100 Moneda Nacional",
        "penalizacion_pct": 25, "penalizacion_diaria": 15000,
        "garantia_clause": "El CONTRATISTA presenta carta de credito por el 5% del monto total del contrato. No se requiere deposito en garantia adicional.",
        "jurisdiccion_text": "tribunales competentes de San Luis Potosi, San Luis Potosi",
        "confidencialidad": "por un periodo de tres (3) anios",
        "propiedad": "seran propiedad de la CONTRATANTE",
    },
    {
        "filename": "contrato-alto-riesgo-software.pdf",
        "number": "AYCO-2026-0162",
        "title": "CONTRATO DE DESARROLLO DE SOFTWARE EMPRESARIAL",
        "contratante": {"name": "Financiera Nacional de Desarrollo S.A. de C.V.", "rfc": "FND220901KL7", "rep": "Lic. Maria Fernanda Gutierrez Lopez"},
        "contratista": {"name": "TechSolutions de Mexico S.A. de C.V.", "rfc": "TSM210315AB4", "rep": "Ing. Carlos Alberto Ramirez Hernandez"},
        "objeto": "desarrollo de software empresarial para sistema de originacion de credito, incluyendo modulo de scoring crediticio, integracion con buros de credito, portal de clientes, y dashboard de analisis de riesgo en tiempo real",
        "vigencia_inicio": "1 de abril de 2026", "vigencia_fin": "31 de marzo de 2027",
        "monto": 7800000.00, "monto_texto": "Siete millones ochocientos mil pesos 00/100 Moneda Nacional",
        "penalizacion_pct": 40, "penalizacion_diaria": 80000,
        "garantia_clause": "Sin garantia de cumplimiento. El CONTRATISTA no presenta fianza, deposito ni carta de credito. La CONTRATANTE confia en la trayectoria del proveedor.",
        "jurisdiccion_text": "tribunales competentes de Monterrey, Nuevo Leon",
        "confidencialidad": "por un periodo de diez (10) anios",
        "propiedad": "seran propiedad exclusiva de la CONTRATANTE, sin licencia para el CONTRATISTA",
    },
    {
        "filename": "contrato-critico-datacenter.pdf",
        "number": "AYCO-2026-0163",
        "title": "CONTRATO DE CONSTRUCCION DE CENTRO DE DATOS",
        "contratante": {"name": "Fondo de Inversion del Pacifico S.A. de C.V.", "rfc": "FIP230801KL5", "rep": "Lic. Maria Fernanda Gutierrez Lopez"},
        "contratista": {"name": "Constructora del Pacifico Express S. de R.L. de C.V.", "rfc": "CPE240115MN6", "rep": "Arq. Juan Pablo Mendoza Rios"},
        "objeto": "construccion, equipamiento y puesta en marcha de un centro de datos corporativo Tier III, incluyendo obra civil, sistemas de respaldo energetico con generadores y UPS redundantes, climatizacion de precision N+1, infraestructura de red con fibra optica, y certificacion ICREA",
        "vigencia_inicio": "1 de junio de 2026", "vigencia_fin": "31 de diciembre de 2027",
        "monto": 22500000.00, "monto_texto": "Veintidos millones quinientos mil pesos 00/100 Moneda Nacional",
        "penalizacion_pct": 50, "penalizacion_diaria": 350000,
        "garantia_clause": "Sin garantia de cumplimiento. El CONTRATISTA es una empresa de reciente creacion (RFC 2024) y no presenta fianza, deposito ni carta de credito.",
        "jurisdiccion_text": "arbitraje internacional bajo reglamento UNCITRAL en ingles, sede en Cancun, Quintana Roo",
        "confidencialidad": "de manera indefinida, sin limitacion temporal",
        "propiedad": "seran propiedad compartida entre las partes en proporcion 50-50%",
    },
    {
        "filename": "contrato-alto-riesgo-outsourcing.pdf",
        "number": "AYCO-2026-0164",
        "title": "CONTRATO DE OUTSOURCING DE PERSONAL ESPECIALIZADO",
        "contratante": {"name": "Banco Regional de Desarrollo S.A. Institucion de Banca Multiple", "rfc": "BRD150820FG6", "rep": "Lic. Alejandro Gomez Sada"},
        "contratista": {"name": "Capital Humano y Servicios del Sureste S.A. de C.V.", "rfc": "CHS190530WX2", "rep": "Lic. Patricia Hernandez Lopez"},
        "objeto": "suministro de personal especializado en tecnologias de la informacion para el area de transformacion digital y modernizacion del core bancario, incluyendo 45 ingenieros de software senior, 12 arquitectos de soluciones, y 8 gerentes de proyecto certificados PMP",
        "vigencia_inicio": "15 de abril de 2026", "vigencia_fin": "14 de abril de 2027",
        "monto": 9600000.00, "monto_texto": "Nueve millones seiscientos mil pesos 00/100 Moneda Nacional",
        "penalizacion_pct": 35, "penalizacion_diaria": 120000,
        "garantia_clause": "Sin garantia de cumplimiento. Se exonera al CONTRATISTA de presentar cualquier tipo de garantia debido a la 'relacion de confianza' entre las partes.",
        "jurisdiccion_text": "tribunales competentes de Tapachula, Chiapas",
        "confidencialidad": "por tiempo indefinido",
        "propiedad": "el CONTRATISTA conservara todos los derechos de propiedad intelectual del personal asignado",
    },
    {
        "filename": "contrato-medio-riesgo-suministros.pdf",
        "number": "AYCO-2026-0165",
        "title": "CONTRATO DE SUMINISTRO DE EQUIPO MEDICO",
        "contratante": {"name": "Hospital Angeles del Pedregal S.A. de C.V.", "rfc": "HAP910620KL2", "rep": "Dr. Roberto Sanchez Miranda"},
        "contratista": {"name": "Equipamiento Hospitalario del Bajio S.A. de C.V.", "rfc": "EHB180410MN7", "rep": "Ing. Luis Fernando Ortega Vega"},
        "objeto": "suministro, instalacion y capacitacion de equipo medico de imagenologia, incluyendo un tomografo computarizado de 128 cortes, un resonador magnetico de 1.5 Tesla, y un sistema de angiografia digital con arco en C, para el area de diagnostico por imagen del hospital",
        "vigencia_inicio": "1 de julio de 2026", "vigencia_fin": "31 de diciembre de 2026",
        "monto": 5800000.00, "monto_texto": "Cinco millones ochocientos mil pesos 00/100 Moneda Nacional",
        "penalizacion_pct": 20, "penalizacion_diaria": 25000,
        "garantia_clause": "El CONTRATISTA entrega poliza de fianza por el 10% del monto total del contrato, unicamente por el primer anio. No se requiere garantia adicional para anios subsecuentes.",
        "jurisdiccion_text": "tribunales competentes de la Ciudad de Mexico",
        "confidencialidad": "por un periodo de siete (7) anios",
        "propiedad": "el equipo sera propiedad de la CONTRATANTE una vez recibido a entera satisfaccion",
    },
]

def format_mxn(amount):
    return f"${amount:,.2f} MXN"

def build_contract(c):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    pdf.add_page()

    # Contract number
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, f"CONTRATO NUMERO: {c['number']}", align="C")
    pdf.ln(12)

    # Title
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, asciify(c["title"]), align="C")
    pdf.ln(10)

    # Parties
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "CONTRATANTE:")
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, asciify(c["contratante"]["name"]))
    pdf.cell(0, 5, f"RFC: {c['contratante']['rfc']}")
    pdf.ln(5)
    pdf.cell(0, 5, f"Representante legal: {asciify(c['contratante']['rep'])}")
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "CONTRATISTA:")
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, asciify(c["contratista"]["name"]))
    pdf.cell(0, 5, f"RFC: {c['contratista']['rfc']}")
    pdf.ln(5)
    pdf.cell(0, 5, f"Representante legal: {asciify(c['contratista']['rep'])}")
    pdf.ln(8)

    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, 'Ambas partes, en lo sucesivo denominadas conjuntamente como "Las Partes", reconocen tener capacidad legal suficiente para obligarse en los terminos del presente contrato y, al efecto, manifiestan:')
    pdf.ln(4)

    # Declarations
    pdf.multi_cell(0, 5, asciify(f"I. Que la CONTRATANTE requiere de {c['objeto']}."))
    pdf.ln(3)
    pdf.multi_cell(0, 5, "II. Que el CONTRATISTA cuenta con la experiencia, capacidad tecnica y recursos necesarios para prestar los servicios requeridos.")
    pdf.ln(3)
    pdf.multi_cell(0, 5, "III. Que Las Partes, en virtud de lo anterior, convienen en celebrar el presente contrato de conformidad con las siguientes clausulas:")
    pdf.ln(6)

    # CLAUSES
    clauses = [
        ("PRIMERA. OBJETO DEL CONTRATO", f"El presente contrato tiene por objeto la {c['objeto']}. El CONTRATISTA se obliga a prestar los servicios conforme al alcance descrito en el Anexo Tecnico I, el cual forma parte integral del presente contrato."),
        ("SEGUNDA. VIGENCIA", f"El presente contrato tendra una vigencia del {c['vigencia_inicio']} al {c['vigencia_fin']}, pudiendo prorrogarse por mutuo acuerdo de las partes mediante convenio adicional suscrito por ambas."),
        ("TERCERA. MONTO TOTAL Y FORMA DE PAGO", f"El monto total del presente contrato es de {format_mxn(c['monto'])} ({c['monto_texto']}), mas IVA. El pago se realizara de la siguiente manera: a) 30% a la firma del presente contrato; b) 40% contra entregables parciales aprobados por la CONTRATANTE; c) 30% restante contra la recepcion final del proyecto."),
        ("CUARTA. PENALIZACIONES", f"En caso de terminacion anticipada del presente contrato por causas imputables al CONTRATISTA, este debera pagar a la CONTRATANTE una penalizacion equivalente al {c['penalizacion_pct']}% del monto total del contrato. En caso de retraso en la entrega de los servicios contratados, el CONTRATISTA pagara una penalizacion de {format_mxn(c['penalizacion_diaria'])} por dia calendario de retraso, sin que dicha penalizacion pueda exceder del {min(c['penalizacion_pct']+10,50)}% del monto total del contrato."),
        ("QUINTA. GARANTIA DE CUMPLIMIENTO", asciify(c["garantia_clause"])),
        ("SEXTA. JURISDICCION", asciify(f"Para la interpretacion y cumplimiento del presente contrato, las partes se someten a los {c['jurisdiccion_text']}, renunciando expresamente a cualquier otro fuero que pudiera corresponderles por razon de domicilio presente o futuro.")),
        ("SEPTIMA. CONFIDENCIALIDAD", asciify(f"Las partes se comprometen a mantener estricta confidencialidad sobre toda la informacion tecnica, comercial, financiera y operativa que reciban con motivo del presente contrato. Las obligaciones de confidencialidad subsistiran {c['confidencialidad']} contados a partir de la terminacion del presente contrato.")),
        ("OCTAVA. PROPIEDAD INTELECTUAL", asciify(f"Todo el software, documentacion y material desarrollado por el CONTRATISTA en virtud del presente contrato {c['propiedad']}.")),
        ("NOVENA. CAUSAS DE RESCISION", "El presente contrato podra rescindirse por cualquiera de las siguientes causas: a) Incumplimiento de las obligaciones pactadas; b) Quiebra o concurso mercantil de cualquiera de las partes; c) Mutuo acuerdo de las partes; d) Caso fortuito o fuerza mayor debidamente comprobado."),
    ]

    for title, body in clauses:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, asciify(title))
        pdf.ln(7)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, asciify(body))
        pdf.ln(5)

    # Signatures
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "Las partes firman el presente contrato en dos tantos, en la Ciudad de Mexico, a los ___ dias del mes de ______________ de 2026.", align="C")
    pdf.ln(12)

    left_x = pdf.get_x()
    mid_x = pdf.w / 2
    pdf.cell(mid_x - 20, 1, "", border="T")
    pdf.set_x(mid_x + 20)
    pdf.cell(mid_x - 20, 1, "", border="T")
    pdf.ln(4)
    pdf.set_x(left_x)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(mid_x - 20, 5, "CONTRATANTE", align="C")
    pdf.set_x(mid_x + 20)
    pdf.cell(mid_x - 20, 5, "CONTRATISTA", align="C")
    pdf.ln(10)

    pdf.set_font("Helvetica", "", 6)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 4, f"AYCO-2026 -- Documento generado para fines de demostracion", align="C")

    return pdf

# Generate all contracts
for c in contracts:
    path = DATA_DIR / c["filename"]
    pdf = build_contract(c)
    pdf.output(str(path))
    print(f"  {c['number']} -- {path.name} (${c['monto']:,.0f})")

print(f"\n6 contratos generados en {DATA_DIR}/")
