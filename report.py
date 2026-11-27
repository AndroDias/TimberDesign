from io import BytesIO
from xml.sax.saxutils import escape
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.graphics.shapes import Drawing, Line, String, PolyLine, Rect


def gerar_pdf(meta, secoes, diagramas):
    buf=BytesIO(); styles=getSampleStyleSheet(); story=[]
    def p(s,style='BodyText'): return Paragraph(escape(str(s)),styles[style])
    story.extend([p('TimberDesign | V1.1 Beta','Title'),p('Memória de pré-dimensionamento','Heading2'),p('EN 1995-1-1:2025 — protótipo não validado para projeto'),Spacer(1,10)])
    def tabela(rows):
        data=[[p(v) for v in row] for row in rows]
        t=Table(data,colWidths=[245,245],repeatRows=1,hAlign='LEFT'); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dceaf7')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f1f5f9')]),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),6)])); return t
    story.append(tabela([('Identificação','Valor')]+list(meta.items())+[('Data',datetime.now().strftime('%d/%m/%Y %H:%M'))]))
    for title,rows in secoes:
        story.extend([p(title,'Heading2'),tabela([('Parâmetro / verificação','Valor')]+list(rows)),Spacer(1,8)])
    for title,x,y in diagramas:
        d=Drawing(490,150); lo=min(0,min(y)); hi=max(0,max(y)); span=hi-lo or 1; yy=lambda v:20+105*(v-lo)/span; xx=lambda v:35+420*v/x[-1]
        d.add(Line(35,yy(0),455,yy(0),strokeColor=colors.grey)); d.add(PolyLine([(xx(a),yy(b)) for a,b in zip(x,y)],strokeColor=colors.HexColor('#24578d'),strokeWidth=1.5)); d.add(String(35,5,'0 m',fontSize=9)); d.add(String(420,5,f'{x[-1]:.2f} m',fontSize=9)); d.add(String(35,135,f'Mín. {min(y):.3f} | Máx. {max(y):.3f}',fontSize=9)); story.append(KeepTogether([p(title,'Heading2'),d]))
    def footer(c,doc):
        c.setFont('Helvetica',8); c.drawString(48,30,'TimberDesign V1.1 Beta | Pré-dimensionamento experimental'); c.drawRightString(547,30,str(doc.page))
    SimpleDocTemplate(buf,pagesize=A4,rightMargin=52,leftMargin=52,topMargin=42,bottomMargin=48).build(story,onFirstPage=footer,onLaterPages=footer)
    return buf.getvalue()
