from pathlib import Path
from reportlab.graphics.shapes import Drawing, Circle, Rect, Line, String, Path as GPath
from reportlab.graphics import renderSVG, renderPDF
from reportlab.lib import colors
from placa_layout import PARTS, TRACKS, WIRES, check, p

ROOT=Path(__file__).resolve().parents[1]


def crear_montaje():
    errors,_,_=check()
    if errors: raise ValueError('; '.join(errors))
    d=Drawing(835,700)
    pitch=22; left=30; top=625; count=20
    ink=colors.HexColor('#292720')
    brown=colors.HexColor('#c79155')
    netcolor={'3V3':'#b52e2b','GND':'#333333'}

    def xy(hole):
        c,r=p(hole)
        return left+(count-1-c)*pitch,top-(r-1)*pitch

    def line(a,b,color=ink,width=2):
        d.add(Line(*a,*b,strokeColor=color,strokeWidth=width))

    def text(x,y,s,size=11,color=ink,font='Helvetica'):
        d.add(String(x,y,s,fontName=font,fontSize=size,fillColor=color))

    def tag(x,y,s,size=10):
        from reportlab.pdfbase.pdfmetrics import stringWidth
        width=stringWidth(s,'Helvetica-Bold',size)
        d.add(Rect(x-3,y-3,width+6,size+5,rx=2,ry=2,
                   fillColor=colors.HexColor('#f9efd9'),strokeColor=None))
        text(x,y,s,size,ink,'Helvetica-Bold')

    def node(x,y,color):
        d.add(Circle(x,y,2.8,fillColor=color,strokeColor=ink,strokeWidth=.3))

    d.add(Rect(6,67,482,599,rx=8,ry=8,fillColor=brown,
               strokeColor=colors.HexColor('#a56f38'),strokeWidth=1.5))
    for row in range(1,26):
        text(11,top-(row-1)*pitch-3,f'{row:02d}',8,colors.HexColor('#533d22'))
        for col in range(count):
            x=left+col*pitch; y=top-(row-1)*pitch
            d.add(Circle(x,y,3.1,fillColor=colors.HexColor('#6e4b2b'),strokeColor=None))
            d.add(Circle(x,y,1.9,fillColor=colors.HexColor('#2d2721'),strokeColor=None))
    for col in range(count):
        text(left+col*pitch-3,646,chr(ord('T')-col),8,colors.white,'Helvetica-Bold')
    text(15,679,'Faro: vista del lado de componentes',16,ink,'Helvetica-Bold')


    for net,a,b in TRACKS:
        x1,y1=xy(a); x2,y2=xy(b)
        color=colors.HexColor(netcolor.get(net,'#a56235'))
        d.add(Line(x1,y1,x2,y2,strokeColor=color,strokeWidth=2,
                   strokeDashArray=[4,3] if net in ('3V3','GND') else None))
        node(x1,y1,color); node(x2,y2,color)

    bands={
        'R1':['#dc7b24','#dc7b24','#222222','#222222','#75502d'],
        'R2':['#bc3028','#bc3028','#222222','#75502d','#75502d'],
        'R3':['#75502d','#222222','#222222','#bc3028','#75502d'],
        'R4':['#75502d','#222222','#222222','#bc3028','#75502d'],
        'R5':['#75502d','#222222','#222222','#75502d','#75502d'],
        'R6':['#75502d','#222222','#222222','#75502d','#75502d'],
    }
    values={'R1':'330 ohm','R2':'2k2','R3':'10k','R4':'10k','R5':'1k','R6':'1k'}
    for ref,(kind,_,pins) in PARTS.items():
        if kind!='res': continue
        (x1,y1),(x2,y2)=[xy(h) for h,_ in pins.values()]
        cx,cy=(x1+x2)/2,(y1+y2)/2
        line((x1,y1),(x2,y2),colors.HexColor('#c8c9c3'),3)
        vertical=x1==x2
        w,h=(15,57) if vertical else (57,15)
        d.add(Rect(cx-w/2,cy-h/2,w,h,rx=4,ry=4,fillColor=colors.HexColor('#e6d9ad'),
                   strokeColor=colors.HexColor('#9b8b61'),strokeWidth=1))
        for k,color in enumerate(bands[ref]):
            pos=-20+k*9
            d.add(Rect(cx-w/2 if vertical else cx+pos,cy+pos if vertical else cy-h/2,
                       w if vertical else 4,4 if vertical else h,
                       fillColor=colors.HexColor(color),strokeColor=None))
        if vertical: tag(cx+13,cy-3,ref+' '+values[ref])
        else: tag(cx-29,cy-25 if ref=='R2' else cy+15,ref+' '+values[ref])


    for ref,clear in [('D1',True),('Q2',False)]:
        pins=PARTS[ref][2]
        coords=[xy(h) for h,_ in pins.values()]
        cx=sum(a[0] for a in coords)/2; yy=coords[0][1]
        for x,y in coords: line((x,y),(x,yy+14),colors.HexColor('#c6c7c0'),3)
        d.add(Rect(cx-20,yy+12,40,54,rx=18,ry=18,
                   fillColor=colors.HexColor('#deebee' if clear else '#202123'),
                   strokeColor=colors.HexColor('#9aabb0' if clear else '#08090a'),strokeWidth=1.2))
        d.add(Rect(cx-22,yy+10,44,6,fillColor=colors.HexColor('#becdd0' if clear else '#111214'),strokeColor=None))
        line((cx-11,yy+28),(cx-11,yy+48),colors.HexColor('#f8ffff' if clear else '#4b4d50'),3)
        tag(cx-24,yy+73,'D1 IR' if clear else 'Q2 PT333')
        for pin,(hole,_) in pins.items():
            x,y=xy(hole); text(x-3,y-15,pin,9,colors.white,'Helvetica-Bold')


    pins=PARTS['Q1'][2]
    coords={k:xy(v[0]) for k,v in pins.items()}
    cx,yy=coords['B']
    for pin,(x,y) in coords.items():
        line((x,y),(cx+(x-cx)*.65,yy+20),colors.HexColor('#c6c7c0'),2.6)
        text(x-3,y-13,pin,8,colors.white,'Helvetica-Bold')
    d.add(Rect(cx-24,yy+6,48,25,rx=11,ry=11,fillColor=colors.HexColor('#252628'),strokeColor=ink))
    line((cx-23,yy+7),(cx+23,yy+7),colors.HexColor('#65676a'),2)
    text(cx-9,yy+15,'Q1',11,colors.white,'Helvetica-Bold')

    x1,y1=xy(PARTS['C1'][2]['1'][0]); x2,y2=xy(PARTS['C1'][2]['2'][0])
    cy=(y1+y2)/2
    line((x1,y1),(x1,cy+12),colors.HexColor('#bfc1ba'),2)
    line((x2,y2),(x2,cy-12),colors.HexColor('#bfc1ba'),2)
    d.add(Circle(x1,cy,15,fillColor=colors.HexColor('#d9b741'),strokeColor=colors.HexColor('#8c7125')))
    text(x1-9,cy-3,'104',10)
    tag(x1-20,cy+24,'C1')

    for ref,fill in [('D2','#df5b4b'),('D3','#659cdd')]:
        pins=PARTS[ref][2]; xa,ya=xy(pins['A'][0]); xk,yk=xy(pins['K'][0])
        line((xa,ya),(xa+8,yk+6),colors.HexColor('#c4c5bc'),2.5)
        line((xk,yk),(xk-8,yk+6),colors.HexColor('#c4c5bc'),2.5)
        d.add(Circle(xa,yk+17,17,fillColor=colors.HexColor(fill),strokeColor=colors.HexColor('#59616a')))
        d.add(Circle(xa-6,yk+23,5,fillColor=colors.HexColor('#eef8ff'),strokeColor=None))
        tag(xa-21,yk+42,ref+' '+('TX' if ref=='D2' else 'RX'))

    a,b=xy('S17'),xy('N19'); xmin=min(a[0],b[0]); xmax=max(a[0],b[0]); ymin=min(a[1],b[1]); ymax=max(a[1],b[1])
    d.add(Rect(xmin-9,ymin-10,xmax-xmin+18,ymax-ymin+20,rx=5,ry=5,
               fillColor=colors.HexColor('#2c2b2b'),strokeColor=colors.HexColor('#151414')))
    cx,cy=(xmin+xmax)/2,(ymin+ymax)/2
    d.add(Circle(cx,cy,26,fillColor=colors.HexColor('#505050'),strokeColor=colors.HexColor('#161616'),strokeWidth=2))
    text(cx-13,cy-4,'SW1',12,colors.white,'Helvetica-Bold')


    wirecolors={'W1':'#e49428','W2':'#24619e','W3':'#32975e','W4':'#d3b322','W5':'#f1f0e7'}
    for i,(ref,net,a,b,_) in enumerate(WIRES):
        x1,y1=xy(a); x2,y2=xy(b)
        curve=GPath(strokeColor=colors.HexColor('#423c30'),strokeWidth=6,fillColor=None)
        curve.moveTo(x1,y1); curve.curveTo(x1-18,y1+20,x2+12,y2+12,x2,y2)
        d.add(curve)
        bright=GPath(strokeColor=colors.HexColor(wirecolors[ref]),strokeWidth=4,fillColor=None)
        bright.moveTo(x1,y1); bright.curveTo(x1-18,y1+20,x2+12,y2+12,x2,y2)
        d.add(bright)
        for x,y in [(x1,y1),(x2,y2)]: node(x,y,colors.HexColor('#d0d2ce'))

    x,y=xy('B22'); _,ytop=xy('B16')
    d.add(Rect(x-12,y-12,24,ytop-y+24,rx=3,ry=3,fillColor=colors.HexColor('#252629'),strokeColor=None))
    tag(x-10,ytop+25,'J1')
    for i in range(1,8):
        x,y=xy('B'+str(15+i))
        d.add(Rect(x-4,y-4,8,8,fillColor=colors.HexColor('#e1bf55'),strokeColor=None))
        text(x+28,y-3,str(i),9,ink,'Helvetica-Bold')


    lx=520
    text(lx,638,'Componentes',16,ink,'Helvetica-Bold')
    legends=[('D1','LED infrarrojo transparente'),('Q2','Fototransistor PT333 negro'),('Q1','Transistor 2N2222A'),
             ('R1','330 ohm'),('R2','2,2 kiloohmios'),('R3 / R4','10 kiloohmios'),
             ('R5 / R6','1 kiloohmio'),('C1','100 nF (104)'),('D2 / D3','Indicadores TX / RX'),('SW1','Boton de panico')]
    for k,(ref,label) in enumerate(legends):
        y=608-25*k; text(lx,y,ref,11,ink,'Helvetica-Bold'); text(lx+78,y,label,11)
    text(lx,325,'J1 hacia la Raspberry',15,ink,'Helvetica-Bold')
    text(lx,300,'Contacto      Funcion          Pin fisico',10,ink,'Helvetica-Bold')
    for i,(label,physical) in enumerate([('3V3','1'),('GND','6'),('TX - GPIO17','11'),('RX - GPIO27','13'),
                                           ('LED TX - GPIO22','15'),('LED RX - GPIO23','16'),('Boton - GPIO24','18')],1):
        y=300-i*22; text(lx+15,y,str(i),11); text(lx+75,y,label,11); text(lx+240,y,physical,11)
    text(lx,100,'Trazos finos: pistas en la cara inferior.',10)
    text(lx,82,'Trazos gruesos: cables aislados superiores.',10)
    text(14,40,'Zona ocupada de la HS-03. Vista superior; no es una foto de la placa terminada.',11)
    text(14,22,'Confirmar el patillaje real del transistor y del detector antes de soldar.',10)
    return d


def main():
    drawing=crear_montaje()
    renderSVG.drawToFile(drawing,str(ROOT/'docs/hardware/montaje-faro.svg'))
    renderPDF.drawToFile(drawing,str(ROOT/'docs/latex/figuras/montaje-faro.pdf'))
    print('Montaje SVG/PDF: redes verificadas contra placa_layout.py')


if __name__=='__main__': main()
