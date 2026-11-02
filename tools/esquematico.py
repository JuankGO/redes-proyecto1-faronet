"""Esquematico vectorial del montaje 3V3 GPIO17/27; no modifica hardware."""
from pathlib import Path
from reportlab.graphics.shapes import Drawing, Line, Rect, Circle, Polygon, String
from reportlab.graphics import renderSVG
from reportlab.lib import colors


def crear_esquema():
    d = Drawing(900, 650)
    ink = colors.HexColor('#152e40')
    accent = colors.HexColor('#126d80')

    def line(x1, y1, x2, y2):
        d.add(Line(x1, y1, x2, y2, strokeColor=ink, strokeWidth=1.8))

    def text(x, y, s, size=13, color=ink):
        d.add(String(x, y, s, fontName='Helvetica', fontSize=size, fillColor=color))

    def node(x, y):
        d.add(Circle(x, y, 3, fillColor=ink, strokeColor=ink))

    def ground(x, y):
        line(x, y, x, y-7)
        for width, offset in [(12,7),(8,12),(4,17)]:
            line(x-width, y-offset, x+width, y-offset)

    def arrow(x1,y1,x2,y2):
        import math
        line(x1,y1,x2,y2)
        a=math.atan2(y2-y1,x2-x1)
        pts=[x2,y2,x2-8*math.cos(a-.45),y2-8*math.sin(a-.45),
             x2-8*math.cos(a+.45),y2-8*math.sin(a+.45)]
        d.add(Polygon(pts,fillColor=ink,strokeColor=ink))

    def resistor_v(x,top,bottom,label):
        mid=(top+bottom)/2
        line(x,top,x,mid+14)
        d.add(Rect(x-7,mid-14,14,28,fillColor=colors.white,strokeColor=ink,strokeWidth=1.8))
        line(x,mid-14,x,bottom)
        text(x+19,mid-4,label)

    def resistor_h(left,right,y,label):
        mid=(left+right)/2
        line(left,y,mid-21,y)
        d.add(Rect(mid-21,y-7,42,14,fillColor=colors.white,strokeColor=ink,strokeWidth=1.8))
        line(mid+21,y,right,y)
        text(mid-29,y+20,label)

    def led_v(x,y,label):
        line(x,y+20,x,y+9)
        d.add(Polygon([x-9,y+9,x+9,y+9,x,y-7],fillColor=colors.white,strokeColor=ink,strokeWidth=1.8))
        line(x-10,y-9,x+10,y-9)
        line(x,y-9,x,y-21)
        arrow(x+13,y+6,x+31,y+22)
        arrow(x+18,y-4,x+36,y+12)
        text(x+44,y-3,label)

    def led_h(x,y,label):
        line(x-20,y,x-9,y)
        d.add(Polygon([x-9,y-9,x-9,y+9,x+7,y],fillColor=colors.white,strokeColor=ink,strokeWidth=1.8))
        line(x+9,y-10,x+9,y+10)
        line(x+9,y,x+20,y)
        arrow(x-4,y+15,x+10,y+29)
        arrow(x+5,y+17,x+19,y+31)
        text(x-15,y-29,label)

    def npn(x,y,label,photo=False):
        d.add(Circle(x,y,27,fillColor=None,strokeColor=ink,strokeWidth=1.8))
        line(x-13,y-15,x-13,y+15)
        line(x-13,y+8,x+15,y+25)
        line(x-13,y-8,x+15,y-25)
        arrow(x-2,y-15,x+11,y-23)
        if photo:
            arrow(x-57,y+30,x-27,y+12)
            arrow(x-62,y+17,x-32,y-1)
        else:
            line(x-43,y,x-13,y)
        text(x+43,y-3,label)
        text(x+24,y+26,'C',11)
        text(x+24,y-32,'E',11)
        return (x-43,y),(x+15,y+25),(x+15,y-25)

    text(30,615,'FaroNet | Faro 3V3 | GPIO17 / GPIO27',22,accent)
    text(30,590,'Raspberry Pi 2 + LED IR + PT333. Redes por funcion, no por orientacion de patillas.',12)
    line(30,575,870,575)
    text(40,551,'EMISOR',16,accent)
    text(600,551,'RECEPTOR INVERTIDO',16,accent)

    text(331,531,'3V3',14)
    resistor_v(360,520,460,'R1 330 ohm')
    line(360,460,360,440)
    led_v(360,420,'D1 LED IR')
    line(360,399,360,380)
    npn(345,355,'Q1 2N2222A')
    text(36,350,'GPIO17',14)
    line(100,355,125,355)
    resistor_h(125,225,355,'R2 2k2')
    line(225,355,302,355)
    node(270,355)
    resistor_v(270,355,287,'R3 10k')
    line(360,330,360,287)
    line(270,287,360,287)
    ground(360,287)
    text(307,364,'B',11)

    text(59,531,'3V3',14)
    line(80,520,80,491)
    line(66,491,94,491)
    line(66,480,94,480)
    line(80,480,80,450)
    ground(80,450)
    text(108,480,'C1 100 nF',13)

    text(685,531,'3V3',14)
    resistor_v(715,520,460,'R4 10k')
    line(715,460,715,440)
    node(715,440)
    line(715,440,845,440)
    text(756,454,'GPIO27 RX',14)
    line(715,440,715,380)
    npn(700,355,'Q2 PT333',photo=True)
    line(715,330,715,287)
    ground(715,287)
    text(600,262,'Sin luz: RX=1. Con luz: RX=0.',13)
    text(600,244,'La lectura UART se invierte en pigpio.',12)

    line(30,226,870,226)
    text(40,200,'INDICADORES',15,accent)
    text(35,162,'GPIO22',13)
    line(100,166,125,166)
    resistor_h(125,225,166,'R5 1k')
    line(225,166,280,166)
    led_h(300,166,'D2 TX')
    line(320,166,415,166)
    ground(415,166)
    text(35,102,'GPIO23',13)
    line(100,106,125,106)
    resistor_h(125,225,106,'R6 1k')
    line(225,106,280,106)
    led_h(300,106,'D3 RX')
    line(320,106,415,106)
    ground(415,106)

    text(600,200,'BOTON DE PANICO',15,accent)
    text(600,174,'GPIO24 (pull-up interno)',13)
    line(600,150,700,150)
    d.add(Circle(700,150,3,fillColor=colors.white,strokeColor=ink))
    line(700,150,742,165)
    d.add(Circle(750,150,3,fillColor=colors.white,strokeColor=ink))
    line(750,150,835,150)
    ground(835,150)
    text(650,115,'SW1 normalmente abierto',13)

    line(30,65,870,65)
    text(30,44,'J1: 1=3V3   2=GND   3=TX17   4=RX27   5=LED22   6=LED23   7=BOTON24',12)
    text(30,24,'Pines fisicos RPi: 1, 6, 11, 13, 15, 16, 18. Confirmar B/C/E de cada encapsulado.',12)
    return d


if __name__=='__main__':
    path=Path(__file__).resolve().parents[1]/'docs/hardware/esquematico-faro.svg'
    renderSVG.drawToFile(crear_esquema(),str(path))
    print(path.name)
