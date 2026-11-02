"""Adaptador de exportación de fichas a PDF con ReportLab."""
from __future__ import annotations

import io
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.application.ports.exportador_plan import ExportadorPlan

LOGO = Path(__file__).resolve().parents[2] / "assets" / "logo.png"
NAVY = colors.HexColor("#0B3C6F")
SKY = colors.HexColor("#1E9BE0")
INK = colors.HexColor("#14213D")
MUTED = colors.HexColor("#64748B")
PALE = colors.HexColor("#EFF7FC")
LINE = colors.HexColor("#D9E4EF")
TIPO = {"ALOJAMIENTO": "Alojamiento", "ACTIVIDAD": "Actividad", "TRANSPORTE": "Transporte"}
DIAS = ("lun", "mar", "mié", "jue", "vie", "sáb", "dom")


def _texto(value: object) -> str:
    return escape(str(value if value is not None else "—"))


def _fecha(value: str) -> str:
    parsed = date.fromisoformat(value)
    return f"{DIAS[parsed.weekday()]} {parsed.day}/{parsed.month}"


def _pagina(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.line(doc.leftMargin, 1.35 * cm, A4[0] - doc.rightMargin, 1.35 * cm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(doc.leftMargin, 0.95 * cm, "Althea · Plan turístico")
    canvas.drawRightString(A4[0] - doc.rightMargin, 0.95 * cm, f"Página {doc.page}")
    canvas.restoreState()


class PdfExportador(ExportadorPlan):
    def exportar(self, ficha: dict) -> bytes:
        buf = io.BytesIO()
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name="PlanTitle", parent=styles["Title"], alignment=TA_LEFT,
            textColor=NAVY, fontSize=22, leading=27, spaceAfter=2,
        ))
        styles.add(ParagraphStyle(
            name="SectionTitle", parent=styles["Heading2"], textColor=NAVY,
            fontSize=14, leading=18, spaceBefore=8, spaceAfter=8,
        ))
        styles.add(ParagraphStyle(
            name="SmallMuted", parent=styles["Normal"], textColor=MUTED,
            fontSize=8, leading=11,
        ))
        styles.add(ParagraphStyle(
            name="CardLabel", parent=styles["Normal"], textColor=MUTED,
            fontSize=8, leading=11, alignment=TA_CENTER,
        ))
        styles.add(ParagraphStyle(
            name="CardValue", parent=styles["Normal"], textColor=INK,
            fontSize=11, leading=14, alignment=TA_CENTER,
        ))
        styles.add(ParagraphStyle(
            name="Cell", parent=styles["Normal"], textColor=INK,
            fontSize=8, leading=11,
        ))
        styles.add(ParagraphStyle(
            name="CellCenter", parent=styles["Cell"], alignment=TA_CENTER,
        ))
        styles.add(ParagraphStyle(
            name="CellHeader", parent=styles["Cell"], textColor=colors.white,
            fontName="Helvetica-Bold",
        ))
        styles.add(ParagraphStyle(
            name="CellHeaderCenter", parent=styles["CellHeader"], alignment=TA_CENTER,
        ))

        doc = SimpleDocTemplate(
            buf, pagesize=A4, title=str(ficha["titulo"]),
            leftMargin=2 * cm, rightMargin=2 * cm,
            topMargin=1.6 * cm, bottomMargin=1.8 * cm,
        )
        elements = []
        if LOGO.exists():
            elements.extend([Image(str(LOGO), width=4.2 * cm, height=2.1 * cm), Spacer(1, 5)])

        elements.extend([
            Paragraph(_texto(ficha["titulo"]), styles["PlanTitle"]),
            Paragraph(
                f"{_texto(ficha.get('destino'))} &nbsp;·&nbsp; "
                f"{_texto(ficha['estado'])} &nbsp;·&nbsp; "
                f"{_texto(ficha['cantidad_viajeros'])} viajeros &nbsp;·&nbsp; "
                f"{_texto(ficha.get('duracion') or '—')} días",
                styles["Normal"],
            ),
            Spacer(1, 12),
        ])

        costo = f"${float(ficha['costo_estimado']):,.0f}".replace(",", ".")
        resumen = Table([[
            [
                Paragraph("INVERSIÓN ESTIMADA", styles["CardLabel"]),
                Paragraph(f"<b>{costo} COP</b>", styles["CardValue"]),
            ],
            [
                Paragraph("DURACIÓN", styles["CardLabel"]),
                Paragraph(f"<b>{_texto(ficha.get('duracion') or '—')} días</b>", styles["CardValue"]),
            ],
            [
                Paragraph("VIAJEROS", styles["CardLabel"]),
                Paragraph(f"<b>{_texto(ficha['cantidad_viajeros'])}</b>", styles["CardValue"]),
            ],
        ]], colWidths=[doc.width / 3] * 3)
        resumen.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PALE),
            ("BOX", (0, 0), (-1, -1), 0.7, LINE),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        elements.extend([resumen, Spacer(1, 15)])

        clima = ficha.get("clima")
        if clima:
            elements.append(Paragraph(f"Clima · {_texto(clima.get('lugar'))}", styles["SectionTitle"]))
            condiciones = Table([[
                [
                    Paragraph("AHORA", styles["CardLabel"]),
                    Paragraph(f"<b>{_texto(clima.get('temperatura'))} °C</b>", styles["CardValue"]),
                    Paragraph(_texto(clima.get("estado")), styles["CardLabel"]),
                ],
                [
                    Paragraph("SENSACIÓN", styles["CardLabel"]),
                    Paragraph(f"<b>{_texto(clima.get('sensacion_termica'))} °C</b>", styles["CardValue"]),
                ],
                [
                    Paragraph("HUMEDAD", styles["CardLabel"]),
                    Paragraph(f"<b>{_texto(clima.get('humedad'))}%</b>", styles["CardValue"]),
                ],
                [
                    Paragraph("PRECIPITACIÓN", styles["CardLabel"]),
                    Paragraph(f"<b>{_texto(clima.get('precipitacion'))} mm</b>", styles["CardValue"]),
                ],
                [
                    Paragraph("VIENTO", styles["CardLabel"]),
                    Paragraph(f"<b>{_texto(clima.get('viento'))} km/h</b>", styles["CardValue"]),
                ],
            ]], colWidths=[doc.width * 0.28, doc.width * 0.18, doc.width * 0.18,
                           doc.width * 0.18, doc.width * 0.18])
            condiciones.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.7, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]))
            elements.extend([condiciones, Spacer(1, 8)])

            pronostico = clima.get("pronostico") or []
            if pronostico:
                elements.append(Paragraph("Pronóstico · próximos 6 días", styles["Normal"]))
                forecast_rows = [[
                    Paragraph("Día", styles["CellHeader"]),
                    Paragraph("Condición", styles["CellHeader"]),
                    Paragraph("Máx.", styles["CellHeaderCenter"]),
                    Paragraph("Mín.", styles["CellHeaderCenter"]),
                    Paragraph("Lluvia", styles["CellHeaderCenter"]),
                ]]
                for dia in pronostico[:6]:
                    forecast_rows.append([
                        Paragraph(_texto(_fecha(dia["fecha"])), styles["Cell"]),
                        Paragraph(_texto(dia.get("estado")), styles["Cell"]),
                        Paragraph(f"{_texto(dia.get('temperatura_max'))} °C", styles["CellCenter"]),
                        Paragraph(f"{_texto(dia.get('temperatura_min'))} °C", styles["CellCenter"]),
                        Paragraph(f"{_texto(dia.get('probabilidad_precipitacion'))}%", styles["CellCenter"]),
                    ])
                forecast_table = Table(
                    forecast_rows,
                    colWidths=[doc.width * 0.18, doc.width * 0.34, doc.width * 0.16,
                               doc.width * 0.16, doc.width * 0.16],
                    repeatRows=1,
                )
                forecast_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
                    ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]))
                elements.extend([forecast_table, Spacer(1, 14)])
            else:
                elements.extend([
                    Paragraph("Pronóstico de los próximos días no disponible.", styles["SmallMuted"]),
                    Spacer(1, 10),
                ])
            elements.append(Paragraph(
                f"Datos meteorológicos actualizados: {_texto(clima.get('actualizado'))} · Open-Meteo",
                styles["SmallMuted"],
            ))
        elif ficha.get("id_destino"):
            elements.append(Paragraph("Clima no disponible para este destino.", styles["SmallMuted"]))
        else:
            elements.append(Paragraph("Este plan no tiene un destino vinculado para consultar el clima.", styles["SmallMuted"]))

        elements.extend([Spacer(1, 14), Paragraph("Itinerario", styles["SectionTitle"])])
        filas = [[
            Paragraph("Día", styles["CellHeader"]),
            Paragraph("Tipo", styles["CellHeader"]),
            Paragraph("Destino", styles["CellHeader"]),
            Paragraph("Servicio", styles["CellHeader"]),
        ]]
        items_por_dia: dict[int, list[dict]] = {}
        for item in ficha["items"]:
            items_por_dia.setdefault(int(item["numero_dia"]), []).append(item)
        duracion = max(
            int(ficha.get("duracion") or 0),
            max(items_por_dia, default=0),
        )
        for dia in range(1, duracion + 1):
            items = items_por_dia.get(dia, [])
            if not items:
                filas.append([
                    Paragraph(f"Día {dia}", styles["Cell"]),
                    Paragraph("—", styles["Cell"]),
                    Paragraph("—", styles["Cell"]),
                    Paragraph("Día libre · sin recursos programados", styles["Cell"]),
                ])
                continue
            for index, item in enumerate(items):
                filas.append([
                    Paragraph(f"Día {dia}" if index == 0 else "", styles["Cell"]),
                    Paragraph(_texto(TIPO.get(item["tipo_recurso"], item["tipo_recurso"])), styles["Cell"]),
                    Paragraph(_texto(item.get("destino")), styles["Cell"]),
                    Paragraph(_texto(item["nombre"]), styles["Cell"]),
                ])
        itinerario = Table(
            filas, colWidths=[1.8 * cm, 2.8 * cm, 3.5 * cm, doc.width - 8.1 * cm], repeatRows=1,
        )
        itinerario.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
            ("GRID", (0, 0), (-1, -1), 0.4, LINE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        elements.append(itinerario)
        doc.build(elements, onFirstPage=_pagina, onLaterPages=_pagina)
        return buf.getvalue()
