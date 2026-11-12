"""Rendu reproductible A4 des trois sources Markdown avec contrôle des pages."""
from pathlib import Path
import re
import sys
from xml.sax.saxutils import escape

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle,Preformatted
from pypdf import PdfReader


def render(source,destination):
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleLocal",fontName="Helvetica-Bold",fontSize=19,leading=24,textColor=colors.HexColor("#123e35"),spaceAfter=12))
    styles.add(ParagraphStyle(name="HeadingLocal",fontName="Helvetica-Bold",fontSize=12,leading=16,spaceBefore=10,spaceAfter=6,textColor=colors.HexColor("#123e35")))
    styles.add(ParagraphStyle(name="BodyLocal",fontSize=10,leading=14,spaceAfter=6))
    styles.add(ParagraphStyle(name="CellLocal",fontSize=8.5,leading=11))
    styles.add(ParagraphStyle(name="CodeLocal",fontName="Courier",fontSize=8.5,leading=12,spaceAfter=8))
    def inline(text):
        text=re.sub(r"\[([^]]+)\]\(([^)]+)\)",r"\1 (\2)",text)
        text=escape(text)
        text=re.sub(r"\*\*(.+?)\*\*",r"<b>\1</b>",text)
        return text.replace("`","")
    lines=source.read_text(encoding="utf-8").splitlines()
    story=[]
    paragraph=[]
    def flush():
        if paragraph:
            story.append(Paragraph(inline(" ".join(paragraph)),styles["BodyLocal"]))
            paragraph.clear()
    i=0
    while i<len(lines):
        line=lines[i]
        if line.strip()=="<!-- pagebreak -->":
            flush(); story.append(PageBreak())
        elif line.startswith("```"):
            flush(); i+=1; code=[]
            while i<len(lines) and not lines[i].startswith("```"):
                code.append(lines[i]); i+=1
            story.append(Preformatted("\n".join(code),styles["CodeLocal"],maxLineLength=90))
        elif line.startswith("|"):
            flush(); rows=[]
            while i<len(lines) and lines[i].startswith("|"):
                cells=[c.strip() for c in lines[i].strip("|").split("|")]
                if not all(re.fullmatch(r"[:\- ]+",c) for c in cells):
                    rows.append([Paragraph(inline(c),styles["CellLocal"]) for c in cells])
                i+=1
            i-=1
            if rows:
                count=len(rows[0]); table=Table(rows,colWidths=[174*mm/count]*count,repeatRows=1,hAlign="LEFT")
                table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#e5eee5")),("VALIGN",(0,0),(-1,-1),"TOP"),
                    ("LINEBELOW",(0,0),(-1,0),.6,colors.HexColor("#123e35")),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
                story.extend([table,Spacer(1,6)])
        elif line.startswith("# "):
            flush();story.append(Paragraph(inline(line[2:]),styles["TitleLocal"]))
        elif line.startswith("## ") or line.startswith("### "):
            flush();story.append(Paragraph(inline(line.lstrip("# ")),styles["HeadingLocal"]))
        elif line.startswith("- ") or re.match(r"^\d+\. ",line):
            flush();paragraph.append(line)
        elif not line.strip():
            flush()
        elif line.startswith("<!--"):
            flush()
        else:
            paragraph.append(line.strip())
        i+=1
    flush()
    def footer(canvas,doc):
        canvas.setFont("Helvetica",8)
        canvas.setFillColor(colors.HexColor("#4a5e57"))
        canvas.drawString(18*mm,10*mm,"Habitat & énergie - Rendu local - 30/10/2026")
        canvas.drawRightString(192*mm,10*mm,str(doc.page))
    doc=SimpleDocTemplate(str(destination),pagesize=(210*mm,297*mm),topMargin=16*mm,bottomMargin=17*mm,leftMargin=18*mm,rightMargin=18*mm)
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    return len(PdfReader(destination).pages)


if __name__=="__main__":
    output=ROOT/"output/submission"
    output.mkdir(parents=True,exist_ok=True)
    for name,minimum,maximum in [("guide_utilisateur",1,2),("documentation_a_voir",1,2),("rapport_ml_final",4,6)]:
        pages=render(ROOT/"doc"/(name+".md"),output/(name+".pdf"))
        print(f"{name}: {pages} pages")
        if not minimum<=pages<=maximum:
            raise SystemExit(f"Nombre de pages non conforme : {name}")
