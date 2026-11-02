"""Genera los dos PDFs desde Markdown y RFC ASCII, sin publicar ni usar GPIO.

Uso desde la raiz: python tools/generar_documentacion.py
Dependencias: requirements-docs.txt. Las tablas y fotos pendientes permanecen
identificadas como tales; esta herramienta no inventa resultados.
"""
from html import escape
from pathlib import Path
import re
import textwrap

from markdown_it import MarkdownIt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    CondPageBreak, Image, LongTable, PageBreak, Paragraph, Preformatted, SimpleDocTemplate,
    Spacer, TableStyle,
)

from esquematico import crear_esquema

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'output/pdf'
MD = MarkdownIt('commonmark').enable('table')
INK = colors.HexColor('#18313f')
TEAL = colors.HexColor('#106375')
MUTED = colors.HexColor('#536875')
SOURCES = [
    'docs/INFORME.md', 'docs/EJECUCION.md', 'docs/API.md',
    'docs/hardware/esquematico-faro.md', 'docs/hardware/BOM.md',
    'docs/hardware/bitacora-pruebas-multimetro.md',
    'docs/bitacora/horas.md', 'docs/bitacora/pruebas.md',
    'docs/AUTOEVALUACION.md', 'docs/bitacora/commits.md',
    'docs/hardware/fotos/README.md', 'docs/ENTREGA.md', 'docs/KICKOFF.md',
]


def fonts():
    """Usar fuentes con espanol; rutas de Windows o DejaVu en GNU/Linux."""
    win = Path('C:/Windows/Fonts')
    linux = Path('/usr/share/fonts/truetype/dejavu')
    if (win/'arial.ttf').exists():
        files = [('Doc','arial.ttf'),('DocBold','arialbd.ttf'),
                 ('DocItalic','ariali.ttf'),('DocMono','consola.ttf')]
        base=win
    elif (linux/'DejaVuSans.ttf').exists():
        files = [('Doc','DejaVuSans.ttf'),('DocBold','DejaVuSans-Bold.ttf'),
                 ('DocItalic','DejaVuSans-Oblique.ttf'),('DocMono','DejaVuSansMono.ttf')]
        base=linux
    else:
        raise RuntimeError('Instalar Arial o DejaVu Sans para generar los PDFs.')
    for name, filename in files:
        pdfmetrics.registerFont(TTFont(name,str(base/filename)))
    pdfmetrics.registerFontFamily('Doc',normal='Doc',bold='DocBold',italic='DocItalic',boldItalic='DocBold')
    pdfmetrics.registerFontFamily('DocMono',normal='DocMono',bold='DocMono',italic='DocMono',boldItalic='DocMono')


def styles():
    b=ParagraphStyle('Body',fontName='Doc',fontSize=9.2,leading=13,
                     textColor=INK,spaceAfter=6,splitLongWords=1,
                     allowWidows=0,allowOrphans=0)
    return {
        'body':b,
        'h1':ParagraphStyle('H1',parent=b,fontName='DocBold',fontSize=19,
                            leading=23,textColor=TEAL,spaceBefore=8,spaceAfter=12,keepWithNext=1),
        'h2':ParagraphStyle('H2',parent=b,fontName='DocBold',fontSize=13,
                            leading=17,textColor=TEAL,spaceBefore=13,spaceAfter=7,keepWithNext=1),
        'h3':ParagraphStyle('H3',parent=b,fontName='DocBold',fontSize=10.7,
                            leading=14,spaceBefore=9,spaceAfter=5,keepWithNext=1),
        'table':ParagraphStyle('Cell',parent=b,fontSize=7.8,leading=10.5,spaceAfter=0),
        'th':ParagraphStyle('CellHead',parent=b,fontName='DocBold',fontSize=7.8,
                            leading=10.5,spaceAfter=0,textColor=colors.white),
        'code':ParagraphStyle('Code',fontName='DocMono',fontSize=7.1,leading=10,
                              backColor=colors.HexColor('#f1f5f6'),borderPadding=7,
                              spaceBefore=4,spaceAfter=10,textColor=INK),
        'caption':ParagraphStyle('Caption',parent=b,fontSize=8,leading=11,
                                 textColor=MUTED,alignment=TA_CENTER,spaceAfter=12),
        'bullet':ParagraphStyle('Bullet',parent=b,leftIndent=12,firstLineIndent=-9),
    }


def inline(tokens):
    result=[]
    for t in tokens or []:
        kind=t.type
        if kind=='text': result.append(escape(t.content))
        elif kind=='code_inline': result.append('<font name="DocMono">'+escape(t.content)+'</font>')
        elif kind=='strong_open': result.append('<b>')
        elif kind=='strong_close': result.append('</b>')
        elif kind=='em_open': result.append('<i>')
        elif kind=='em_close': result.append('</i>')
        elif kind=='link_open':
            href=t.attrGet('href') or ''
            if href.startswith(('https://','http://')):
                result.append('<link href="'+escape(href,quote=True)+'" color="#106375">')
            else: result.append('<u>')
        elif kind=='link_close':
            # MarkdownIt no guarda el href en el token de cierre.
            open_tag=''.join(result).rfind('<link ')
            closed=''.join(result).rfind('</link>')
            result.append('</link>' if open_tag>closed else '</u>')
        elif kind=='softbreak': result.append(' ')
        elif kind=='hardbreak': result.append('<br/>')
        elif kind=='image': result.append(escape(t.content))
    return ''.join(result)


class Book(SimpleDocTemplate):
    def afterFlowable(self,flowable):
        if isinstance(flowable,Paragraph) and flowable.style.name in ('H1','H2'):
            if flowable.style.name=='H1': self._had_h1=True
            if not getattr(self,'_had_h1',False): return
            self._heading=getattr(self,'_heading',0)+1
            key=f'section-{self._heading}'
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(flowable.getPlainText(),key,
                                     level=0 if flowable.style.name=='H1' else 1,closed=False)


def running(c,doc):
    c.saveState()
    w,h=letter
    c.setStrokeColor(colors.HexColor('#ccdadf')); c.setLineWidth(.6)
    c.line(48,h-38,w-48,h-38)
    c.setFillColor(MUTED); c.setFont('Doc',8)
    c.drawString(48,h-28,'FaroNet | Redes de Computadoras | TEC')
    c.drawRightString(w-48,h-28,'Documentacion de entrega')
    c.line(48,38,w-48,38)
    c.drawString(48,25,'Jimmy Castillo Guzman / Juan Carlos Gomez | 01-11-2026')
    c.drawRightString(w-48,25,str(doc.page))
    c.restoreState()


def render_md(path,sty,width):
    tokens=MD.parse(path.read_text(encoding='utf-8'))
    story=[]; i=0; list_depth=0
    while i<len(tokens):
        t=tokens[i]
        if t.type=='heading_open':
            level=int(t.tag[1:]); content=tokens[i+1]
            story.append(Paragraph(inline(content.children),sty['h'+str(min(level,3))]))
            i+=3; continue
        if t.type=='paragraph_open':
            content=tokens[i+1]
            children=content.children or []
            if len(children)==1 and children[0].type=='image':
                img=children[0]; target=path.parent/(img.attrGet('src') or '')
                if target.suffix=='.svg':
                    drawing=crear_esquema(); scale=width/drawing.width
                    drawing.scale(scale,scale); drawing.width*=scale; drawing.height*=scale
                    story.append(drawing)
                else:
                    image=Image(str(target))
                    scale=min(width/image.imageWidth,310/image.imageHeight)
                    image.drawWidth=image.imageWidth*scale; image.drawHeight=image.imageHeight*scale
                    image.hAlign='CENTER'; story.append(image)
                story.append(Paragraph(escape(img.content),sty['caption']))
            else:
                value=inline(children)
                if list_depth: value='- '+value
                story.append(Paragraph(value,sty['bullet'] if list_depth else sty['body']))
            i+=3; continue
        if t.type in ('bullet_list_open','ordered_list_open'): list_depth+=1
        elif t.type in ('bullet_list_close','ordered_list_close'): list_depth-=1
        elif t.type in ('fence','code_block'):
            lines=[]
            for line in t.content.rstrip('\n').splitlines():
                lines.extend(textwrap.wrap(line,width=111,break_long_words=True,
                                          break_on_hyphens=False,replace_whitespace=False,
                                          drop_whitespace=False,subsequent_indent='  ') or [''])
            story.append(Preformatted('\n'.join(lines),sty['code']))
        elif t.type=='table_open':
            rows=[]; row=[]; j=i+1
            while tokens[j].type!='table_close':
                if tokens[j].type=='tr_open': row=[]
                elif tokens[j].type=='inline': row.append(tokens[j])
                elif tokens[j].type=='tr_close': rows.append(row)
                j+=1
            n=len(rows[0]); weights=[]
            for k in range(n):
                lengths=[len(row[k].content) for row in rows]
                weights.append(max(9,min(44,sum(lengths)/len(lengths))))
            col_widths=[width*v/sum(weights) for v in weights]
            cells=[[Paragraph(inline(cell.children),sty['th'] if r==0 else sty['table'])
                    for cell in row] for r,row in enumerate(rows)]
            table=LongTable(cells,colWidths=col_widths,repeatRows=1,hAlign='LEFT',
                            splitByRow=1 if len(rows)>8 else 0)
            if len(rows)>8 and story and isinstance(story[-1],Paragraph):
                story[-1].keepWithNext=0
            table.setStyle(TableStyle([
                ('BACKGROUND',(0,0),(-1,0),TEAL),
                ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f3f6f7')]),
                ('VALIGN',(0,0),(-1,-1),'TOP'),
                ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
                ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
                ('LINEBELOW',(0,0),(-1,0),.5,TEAL),
                ('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#dae3e7')),
            ]))
            story.extend([table,Spacer(1,11)])
            i=j+1; continue
        elif t.type=='hr': story.append(Spacer(1,10))
        i+=1
    return story


def documentation(sty):
    path=OUT/'FaroNet-documentacion.pdf'
    doc=Book(str(path),pagesize=letter,rightMargin=48,leftMargin=48,
             topMargin=53,bottomMargin=52,title='FaroNet - Documentacion del proyecto',
             author='Jimmy Castillo Guzman y Juan Carlos Gomez')
    story=[Spacer(1,45),Paragraph('FaroNet',ParagraphStyle('Cover',fontName='DocBold',
             fontSize=40,leading=46,textColor=TEAL)),
           Paragraph('Proyecto 1 - Redes de Computadoras',sty['h2']),
           Paragraph('Ingenieria en Computacion | TEC | II semestre 2026',sty['body']),
           Spacer(1,22),Paragraph('Jimmy Castillo Guzman<br/>Juan Carlos Gomez',sty['body']),
           Paragraph('Profesor: Kevin Moraga<br/>Corte: 1 de noviembre de 2026',sty['body']),
           Spacer(1,24),Paragraph('Informe y anexos',sty['h2'])]
    for item in ['Diseno, funciones y comandos reproducibles',
                 'Esquema, materiales y presupuesto en colones',
                 'Bitacoras, resultados y autoevaluacion',
                 'Trazabilidad de requisitos y evidencias disponibles']:
        story.append(Paragraph('- '+item,sty['bullet']))
    story += [Spacer(1,22),Paragraph('Worker implementado; no utilizado en la demostracion integrada.',sty['body']),
              Paragraph('Las mediciones pendientes se identifican sin sustituirlas por valores esperados.',sty['body']),
              Paragraph('Repositorio: https://github.com/JuankGO/redes-proyecto1-faronet',sty['body']),
              PageBreak()]
    for index,relative in enumerate(SOURCES):
        if index:
            story.append(PageBreak() if index in (1,2,3,12) else CondPageBreak(220))
            story.append(Spacer(1,10))
        story.extend(render_md(ROOT/relative,sty,doc.width))
    doc.build(story,onFirstPage=running,onLaterPages=running)
    return path


def rfc_pdf():
    source=(ROOT/'docs/rfc/rfc-faronet.txt').read_text(encoding='ascii')
    path=OUT/'FaroNet-RFC.pdf'
    c=canvas.Canvas(str(path),pagesize=letter)
    c.setTitle('FaroNet - RFC 9999 academico, version 1')
    c.setAuthor('Jimmy Castillo Guzman y Juan Carlos Gomez')
    for page in source.split('\f'):
        lines=page.strip('\n').splitlines()
        if len(lines)>66: raise ValueError('Pagina RFC demasiado larga')
        c.setFont('Courier',9.2)
        for i,line in enumerate(lines):
            if pdfmetrics.stringWidth(line,'Courier',9.2)>letter[0]-84:
                raise ValueError('Linea RFC excede ancho: '+line)
            c.drawString(42,letter[1]-43-i*10.5,line)
        c.showPage()
    c.save()
    return path


def main():
    fonts(); OUT.mkdir(parents=True,exist_ok=True)
    from reportlab.graphics import renderSVG
    renderSVG.drawToFile(crear_esquema(),str(ROOT/'docs/hardware/esquematico-faro.svg'))
    for path in [documentation(styles()),rfc_pdf()]:
        print(path.relative_to(ROOT))


if __name__=='__main__': main()
