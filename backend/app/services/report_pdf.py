"""Geração do relatório em PDF (reportlab) com a identidade visual da TrainUp."""
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape


from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


from app.core.tz import fmt_local, now_utc


NAVY = colors.HexColor("#13294B")
BLUE = colors.HexColor("#0B8FDB")
LIME = colors.HexColor("#9BD64A")
TEAL = colors.HexColor("#5FC28A")
MUTED = colors.HexColor("#5B6B80")
LINE = colors.HexColor("#DDE4EE")
SOFT = colors.HexColor("#F3F6FA")
LOGO = Path(__file__).resolve().parent.parent / "assets" / "logo.png"


H1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=20, textColor=NAVY, leading=24)
H2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=12.5, textColor=NAVY, leading=16, spaceBefore=12, spaceAfter=5)
BODY = ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, textColor=NAVY, leading=13.5)
SMALL = ParagraphStyle("small", fontName="Helvetica", fontSize=8, textColor=MUTED, leading=11)
CELL = ParagraphStyle("cell", fontName="Helvetica", fontSize=8.5, textColor=NAVY, leading=11)




def _pt(x, d: int = 1) -> str:
    return f"{x:.{d}f}".replace(".", ",")




def _d(iso: str) -> str:
    return f"{iso[8:10]}/{iso[5:7]}"




def _page(canvas, doc):
    w, h = A4
    canvas.saveState()
    if LOGO.exists():
        canvas.drawImage(str(LOGO), 18 * mm, h - 25 * mm, width=42 * mm, height=13.8 * mm, mask="auto")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(w - 18 * mm, h - 18 * mm, "Relatório de evolução")
    steps = 60
    bar_w = (w - 36 * mm) / steps
    for i in range(steps):
        t = i / (steps - 1)
        c = colors.Color(BLUE.red + (LIME.red - BLUE.red) * t, BLUE.green + (LIME.green - BLUE.green) * t,
                         BLUE.blue + (LIME.blue - BLUE.blue) * t)
        canvas.setFillColor(c)
        canvas.rect(18 * mm + i * bar_w, h - 28.5 * mm, bar_w + 0.3, 1.4 * mm, stroke=0, fill=1)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(18 * mm, 10 * mm, f"TrainUp · gerado em {fmt_local(now_utc(), '%d/%m/%Y %H:%M')} (horário de Brasília)")
    canvas.drawRightString(w - 18 * mm, 10 * mm, f"Página {doc.page}")
    canvas.restoreState()




def _line_chart(title: str, points: list[dict]) -> Drawing:
    d = Drawing(480, 125)
    d.add(String(0, 112, title, fontName="Helvetica-Bold", fontSize=9, fillColor=NAVY))
    lc = HorizontalLineChart()
    lc.x, lc.y, lc.width, lc.height = 34, 22, 430, 78
    vals = [p["max_load"] for p in points]
    lc.data = [vals]
    step = max(1, len(points) // 12)
    lc.categoryAxis.categoryNames = [_d(p["date"]) if i % step == 0 else "" for i, p in enumerate(points)]
    lc.categoryAxis.labels.fontSize = 7
    lc.valueAxis.labels.fontSize = 7
    lc.categoryAxis.labels.fontName = "Helvetica"
    lc.valueAxis.labels.fontName = "Helvetica"
    lo, hi = min(vals), max(vals)
    pad = max(2.0, (hi - lo) * 0.25)
    lc.valueAxis.valueMin, lc.valueAxis.valueMax = max(0, lo - pad), hi + pad
    lc.lines[0].strokeColor = BLUE
    lc.lines[0].strokeWidth = 2
    lc.valueAxis.gridStrokeColor = LINE
    lc.valueAxis.visibleGrid = True
    d.add(lc)
    return d




def _bar_chart(weekly: list[dict]) -> Drawing:
    d = Drawing(480, 135)
    bc = VerticalBarChart()
    bc.x, bc.y, bc.width, bc.height = 40, 24, 420, 95
    bc.data = [[w["volume"] for w in weekly]]
    step = max(1, len(weekly) // 14)
    bc.categoryAxis.categoryNames = [_d(w["week"]) if i % step == 0 else "" for i, w in enumerate(weekly)]
    bc.categoryAxis.labels.fontSize = 7
    bc.valueAxis.labels.fontSize = 7
    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = max(100.0, max((w["volume"] for w in weekly), default=0) * 1.1)
    bc.categoryAxis.labels.fontName = "Helvetica"
    bc.valueAxis.labels.fontName = "Helvetica"
    bc.bars[0].fillColor = TEAL
    bc.bars[0].strokeColor = None
    bc.valueAxis.gridStrokeColor = LINE
    bc.valueAxis.visibleGrid = True
    d.add(bc)
    return d




def render_report_pdf(r: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=34 * mm, bottomMargin=18 * mm, title="Relatório TrainUp",
                            author="TrainUp")
    s, e = r["period"]["start"], r["period"]["end"]
    fmt = lambda iso: f"{iso[8:10]}/{iso[5:7]}/{iso[:4]}"
    story = [
        Paragraph(escape(r["aluno"]["name"]), H1),
        Paragraph(
            f"Período: {fmt(s)} a {fmt(e)}"
            + (f" · Personal: {escape(r['personal'])}" if r.get("personal") else ""),
            SMALL,
        ),
        Spacer(1, 4),
        Paragraph("Resumo", H2),
        Paragraph(escape(r["summary_text"]), BODY),
    ]


    a = r["attendance"]
    kp = [
        ["Sessões de treino", "Aulas realizadas", "Canceladas", "Faltas", "Presença"],
        [str(a["sessoes"]), f"{a['realizadas']} de {a['agendadas']}", str(a["canceladas"]), str(a["faltas"]),
         f"{a['presenca_pct']}%" if a["presenca_pct"] is not None else "-"],
    ]
    t = Table(kp, colWidths=[34 * mm] * 5)
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica"), ("FONTSIZE", (0, 0), (-1, 0), 7.5),
        ("TEXTCOLOR", (0, 0), (-1, 0), MUTED),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"), ("FONTSIZE", (0, 1), (-1, 1), 13),
        ("TEXTCOLOR", (0, 1), (-1, 1), NAVY), ("BACKGROUND", (0, 0), (-1, -1), SOFT),
        ("BOX", (0, 0), (-1, -1), 0.5, LINE), ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.white),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [Paragraph("Frequência", H2), t]


    exs = r["exercises"]
    story.append(Paragraph("Evolução por exercício", H2))
    if exs:
        head = ["Exercício", "Sess.", "Inicial", "Final", "Máx.", "Progressão", "Volume (kg)", "Status"]
        data = [head]
        for x in exs:
            status = "Recorde" if x["record"] else ("Estagnado" if x["stagnant"] else "")
            data.append([Paragraph(escape(x["exercise"]), CELL), x["sessions"], f"{_pt(x['first_load'])} kg",
                         f"{_pt(x['last_load'])} kg", f"{_pt(x['max_load'])} kg",
                         f"{'+' if x['progression_pct'] > 0 else ''}{_pt(x['progression_pct'])}%",
                         _pt(x["total_volume"], 0), status])
        tb = Table(data, colWidths=[44 * mm, 11 * mm, 18 * mm, 18 * mm, 18 * mm, 20 * mm, 22 * mm, 20 * mm], repeatRows=1)
        style = [
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 1), (-1, -1), NAVY), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SOFT]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("LINEBELOW", (0, 0), (-1, -1), 0.25, LINE),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        for i, x in enumerate(exs, start=1):
            if x["record"]:
                style.append(("TEXTCOLOR", (7, i), (7, i), colors.HexColor("#1F7A45")))
            elif x["stagnant"]:
                style.append(("TEXTCOLOR", (7, i), (7, i), colors.HexColor("#B7791F")))
        tb.setStyle(TableStyle(style))
        story.append(tb)
        story.append(Paragraph("Cargas em kg (maior carga de cada sessão). Progressão compara a primeira e a última sessão do período.", SMALL))
        story.append(Paragraph("Gráficos de carga", H2))
        for x in exs[:4]:
            if len(x["points"]) >= 2:
                story.append(KeepTogether([_line_chart(x["exercise"], x["points"])]))
    else:
        story.append(Paragraph("Sem treinos registrados no período.", BODY))


    story.append(KeepTogether([Paragraph("Volume semanal (carga x repetições)", H2), _bar_chart(r["weekly_volume"])]))


    story.append(Paragraph("Observações do personal", H2))
    note = r.get("note")
    story.append(Paragraph(escape(note["text"]).replace("\n", "<br/>") if note else "Nenhuma observação registrada.", BODY))
    doc.build(story, onFirstPage=_page, onLaterPages=_page)
    return buf.getvalue()
