"""Adaptador de exportación de fichas a PDF con ReportLab."""
from __future__ import annotations

import io
from itertools import groupby
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.application.ports.exportador_plan import ExportadorPlan

LOGO = Path(__file__).resolve().parents[2] / "assets" / "logo.png"
NAVY = colors.HexColor("#0B3C6F")
TIPO = {"ALOJAMIENTO": "Alojamiento", "ACTIVIDAD": "Actividad", "TRANSPORTE": "Transporte"}


class PdfExportador(ExportadorPlan):
    def exportar(self, ficha: dict) -> bytes:
        buf, st, el = io.BytesIO(), getSampleStyleSheet(), []
        doc = SimpleDocTemplate(buf, pagesize=A4, title=ficha["titulo"], leftMargin=2 * cm, rightMargin=2 * cm)
        if LOGO.exists():
            el += [Image(str(LOGO), width=6 * cm, height=3 * cm), Spacer(1, 8)]
        el += [Paragraph(f"<b>{ficha['titulo']}</b>", st["Title"]),
               Paragraph(f"Destino: {ficha.get('destino') or '—'} · Estado: {ficha['estado']} · "
                         f"Viajeros: {ficha['cantidad_viajeros']} · Duración: {ficha.get('duracion') or '—'} días", st["Normal"]),
               Paragraph(f"Costo estimado: <b>${float(ficha['costo_estimado']):,.0f} COP</b>", st["Normal"]),
               Spacer(1, 14), Paragraph("Itinerario propuesto", st["Heading2"])]
        filas = [["Día", "Tipo", "Servicio"]]
        for dia, its in groupby(ficha["items"], key=lambda i: i["numero_dia"]):
            for k, i in enumerate(its):
                filas.append([f"Día {dia}" if k == 0 else "", TIPO.get(i["tipo_recurso"], i["tipo_recurso"]), i["nombre"]])
        t = Table(filas, colWidths=[2.5 * cm, 4 * cm, 10 * cm])
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                               ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D5DCE6")),
                               ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        el.append(t)
        doc.build(el)
        return buf.getvalue()
